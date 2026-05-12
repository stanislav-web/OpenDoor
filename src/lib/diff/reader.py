# -*- coding: utf-8 -*-

"""Read and validate OpenDoor reports for differential scan."""

import json
import os
import sqlite3
from pathlib import Path

from .exceptions import DiffValidationError
from .records import DiffReport, DiffReportFinding


SQLITE_EXTENSIONS = ('.sqlite', '.db')
JSON_EXTENSIONS = ('.json',)
SUPPORTED_EXTENSIONS = SQLITE_EXTENSIONS + JSON_EXTENSIONS


class DiffReportReader(object):
    """Load exactly two same-format OpenDoor reports for diff mode."""

    def parse_pair(self, value):
        """
        Parse --diff value.

        :param str value: old:new report path pair
        :raise DiffValidationError: when the input is malformed
        :return: tuple[str, str]
        """

        if not isinstance(value, str) or not value.strip():
            raise DiffValidationError(
                'Invalid --diff value. Expected: old.sqlite:new.sqlite or old.json:new.json'
            )

        parts = value.split(':')
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            raise DiffValidationError(
                'Invalid --diff value. Expected exactly two reports: previous and current'
            )

        return parts[0].strip(), parts[1].strip()

    def read_pair(self, value):
        """
        Read and validate a previous/current report pair.

        :param str value: old:new report path pair
        :raise DiffValidationError: when reports are missing, unsupported or incompatible
        :return: tuple[DiffReport, DiffReport]
        """

        previous_path, current_path = self.parse_pair(value)
        previous_format = self.detect_format(previous_path)
        current_format = self.detect_format(current_path)

        if previous_format != current_format:
            raise DiffValidationError('Diff reports must use the same supported format')

        return self.read(previous_path), self.read(current_path)

    def read(self, path):
        """
        Read one supported OpenDoor report.

        :param str path: report path
        :raise DiffValidationError: when report is invalid
        :return: DiffReport
        """

        report_format = self.detect_format(path)

        if report_format == 'sqlite':
            return SqliteDiffReportReader().read(path)

        if report_format == 'json':
            return JsonDiffReportReader().read(path)

        raise DiffValidationError('Unsupported diff report format: {0}'.format(path))

    @staticmethod
    def detect_format(path):
        """
        Detect report format from the file extension after common path checks.

        :param str path: report path
        :raise DiffValidationError: when report path is invalid or unsupported
        :return: str
        """

        if not isinstance(path, str) or not path.strip():
            raise DiffValidationError('Diff report path is empty')

        report_path = Path(path)
        if not report_path.exists():
            raise DiffValidationError('Diff report does not exist: {0}'.format(path))

        if not report_path.is_file():
            raise DiffValidationError('Diff report is not a file: {0}'.format(path))

        extension = report_path.suffix.lower()
        if extension in SQLITE_EXTENSIONS:
            return 'sqlite'

        if extension in JSON_EXTENSIONS:
            return 'json'

        raise DiffValidationError(
            'Unsupported diff report format: {0}. Supported formats: sqlite, json'.format(path)
        )


class SqliteDiffReportReader(object):
    """Read OpenDoor SQLite reports."""

    REQUIRED_TABLES = {'metadata', 'items'}
    REQUIRED_ITEM_COLUMNS = {'status', 'url', 'code', 'size'}

    def read(self, path):
        """
        Read a SQLite report into a normalized DiffReport.

        :param str path: SQLite report path
        :raise DiffValidationError: when the SQLite file is invalid or unsupported
        :return: DiffReport
        """

        connection = None
        try:
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
            self._validate_schema(connection)

            target = self._read_target(connection, path)
            findings = tuple(self._read_findings(connection))

            return DiffReport(
                path=os.path.abspath(path),
                format='sqlite',
                target=target,
                findings=findings,
            )
        except DiffValidationError:
            raise
        except sqlite3.Error as error:
            raise DiffValidationError('Invalid SQLite report: {0}'.format(error))
        finally:
            if connection is not None:
                connection.close()

    def _validate_schema(self, connection):
        cursor = connection.cursor()
        tables = {
            row['name']
            for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

        missing_tables = sorted(self.REQUIRED_TABLES - tables)
        if missing_tables:
            raise DiffValidationError(
                'Invalid SQLite report: missing OpenDoor table(s): {0}'.format(', '.join(missing_tables))
            )

        columns = {
            row['name']
            for row in cursor.execute('PRAGMA table_info(items)')
        }
        missing_columns = sorted(self.REQUIRED_ITEM_COLUMNS - columns)
        if missing_columns:
            raise DiffValidationError(
                'Invalid SQLite report: missing item column(s): {0}'.format(', '.join(missing_columns))
            )

    @staticmethod
    def _read_target(connection, path):
        row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'target' LIMIT 1"
        ).fetchone()

        if row is not None and row['value']:
            return str(row['value'])

        return Path(path).stem

    @staticmethod
    def _read_findings(connection):
        rows = connection.execute(
            'SELECT status, url, code, size FROM items ORDER BY id'
        ).fetchall()

        for row in rows:
            yield normalize_finding(
                bucket=row['status'],
                url=row['url'],
                status=row['code'],
                size=row['size'],
            )


class JsonDiffReportReader(object):
    """Read OpenDoor JSON reports."""

    def read(self, path):
        """
        Read a JSON report into a normalized DiffReport.

        :param str path: JSON report path
        :raise DiffValidationError: when JSON syntax or structure is invalid
        :return: DiffReport
        """

        try:
            with open(path, encoding='utf-8') as handler:
                payload = json.load(handler)
        except json.JSONDecodeError as error:
            raise DiffValidationError('Invalid JSON report: {0}'.format(error))
        except OSError as error:
            raise DiffValidationError('Cannot read JSON report: {0}'.format(error))

        if not isinstance(payload, dict):
            raise DiffValidationError('Invalid JSON report: expected an object at top level')

        target = self._read_target(payload, path)
        findings = tuple(self._read_findings(payload))

        return DiffReport(
            path=os.path.abspath(path),
            format='json',
            target=target,
            findings=findings,
        )

    @staticmethod
    def _read_target(payload, path):
        target = payload.get('target') or payload.get('host')
        if isinstance(target, str) and target.strip():
            return target.strip()

        return Path(path).stem

    def _read_findings(self, payload):
        report_items = payload.get('report_items')
        if isinstance(report_items, dict):
            return self._read_report_items(report_items)

        items = payload.get('items')
        if isinstance(items, dict):
            return self._read_plain_items(items)

        raise DiffValidationError('Invalid JSON report: missing OpenDoor report items')

    @staticmethod
    def _read_report_items(report_items):
        findings = []
        for bucket in sorted(report_items.keys()):
            values = report_items.get(bucket)
            if not isinstance(values, list):
                raise DiffValidationError('Invalid JSON report: bucket {0} must contain a list'.format(bucket))

            for item in values:
                if not isinstance(item, dict):
                    raise DiffValidationError('Invalid JSON report: report item must be an object')

                findings.append(normalize_finding(
                    bucket=bucket,
                    url=item.get('url'),
                    status=item.get('code'),
                    size=item.get('size'),
                    method=item.get('method'),
                    location=item.get('location') or item.get('redirect_location'),
                ))

        return findings

    @staticmethod
    def _read_plain_items(items):
        findings = []
        for bucket in sorted(items.keys()):
            values = items.get(bucket)
            if not isinstance(values, list):
                raise DiffValidationError('Invalid JSON report: bucket {0} must contain a list'.format(bucket))

            for url in values:
                findings.append(normalize_finding(
                    bucket=bucket,
                    url=url,
                    status='-',
                    size='0B',
                ))

        return findings


def normalize_finding(bucket, url, status='-', size='0B', method='', location=''):
    """
    Normalize one raw report item into a DiffReportFinding.

    :param str bucket: OpenDoor bucket/status
    :param str url: discovered URL
    :param str status: HTTP status code or placeholder
    :param str size: response size text
    :param str method: HTTP method if available
    :param str location: redirect location if available
    :raise DiffValidationError: when a finding has no URL
    :return: DiffReportFinding
    """

    normalized_url = '' if url is None else str(url).strip()
    if not normalized_url:
        raise DiffValidationError('Invalid report item: url is required')

    return DiffReportFinding(
        bucket='' if bucket is None else str(bucket).strip(),
        url=normalized_url,
        status='-' if status is None else str(status).strip(),
        size='0B' if size is None else str(size).strip(),
        method='' if method is None else str(method).strip().upper(),
        location='' if location is None else str(location).strip(),
    )
