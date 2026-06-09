# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development: Stanislav WEB
"""

import json
import os
import sqlite3

from .provider import PluginProvider
from src.core import CoreConfig
from src.core import filesystem, FileSystemError
from src.lib import tpl


class SqliteReportPlugin(PluginProvider):
    """SqliteReportPlugin class."""

    PLUGIN_NAME = 'SqliteReport'
    EXTENSION_SET = '.sqlite'

    def __init__(self, target, data, directory=None):
        """
        PluginProvider constructor.

        :param str target: target host
        :param dict data: result set
        :param str directory: custom directory
        """

        PluginProvider.__init__(self, target, data)

        try:
            if directory is None:
                directory = CoreConfig.get('data').get('reports')
            self.__target_dir = filesystem.makedir(os.path.join(directory, self._target))
        except FileSystemError as error:
            raise Exception(error)


    @staticmethod
    def _json_or_none(value):
        """Return stable JSON text for structured metadata or None.

        :param dict | list | mixed value: value to serialize
        :return: JSON text or None
        :rtype: str | None
        """

        if value is None:
            return None
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        return str(value)

    @staticmethod
    def _dict_or_empty(value):
        """Return a dict value or an empty dict.

        :param dict | mixed value: source value
        :return: source dict or empty dict
        :rtype: dict
        """

        if isinstance(value, dict):
            return value
        return {}

    @staticmethod
    def _str_or_none(value):
        """Return string value or None.

        :param mixed value: source value
        :return: string value or None
        :rtype: str | None
        """

        if value is None:
            return None
        return str(value)

    @staticmethod
    def _int_or_none(value):
        """Return integer value or None.

        :param mixed value: source value
        :return: integer value or None
        :rtype: int | None
        """

        if value is None:
            return None
        return int(value)

    @staticmethod
    def _float_or_none(value):
        """Return float value or None.

        :param mixed value: source value
        :return: float value or None
        :rtype: float | None
        """

        if value is None:
            return None
        return float(value)

    @staticmethod
    def _bool_int_or_none(value):
        """Return bool coerced to SQLite integer or None.

        :param mixed value: source value
        :return: 1/0 integer value or None
        :rtype: int | None
        """

        if value is None:
            return None
        return int(bool(value))

    @staticmethod
    def _joined_or_none(value):
        """Return semicolon-joined iterable values or None.

        This preserves the existing SQLite report coercion behavior for
        iterable metadata values.

        :param iterable | None value: source value
        :return: semicolon-joined string or None
        :rtype: str | None
        """

        if value is None:
            return None
        return ';'.join([str(item) for item in value])

    def process(self):
        """
        Persist report data into a SQLite database.

        :return: None
        """

        database_path = os.path.join(self.__target_dir, self._target + self.EXTENSION_SET)
        connection = None

        try:
            filesystem.clear(self.__target_dir, extension=self.EXTENSION_SET)
            filesystem.makefile(database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            cursor.execute('CREATE TABLE summary (status TEXT PRIMARY KEY, total INTEGER NOT NULL)')
            cursor.execute(
                'CREATE TABLE items ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'status TEXT NOT NULL, '
                'url TEXT NOT NULL, '
                'code TEXT NOT NULL, '
                'size TEXT NOT NULL, '
                'bypass TEXT, '
                'bypass_profile TEXT, '
                'bypass_header TEXT, '
                'bypass_value TEXT, '
                'bypass_variant TEXT, '
                'bypass_url TEXT, '
                'bypass_from_status TEXT, '
                'bypass_to_status TEXT, '
                'bypass_from_code TEXT, '
                'bypass_to_code TEXT, '
                'bypass_score INTEGER, '
                'bypass_reasons TEXT, '
                'stacktrace_detection TEXT, '
                'stacktrace_runtime TEXT, '
                'stacktrace_signal TEXT, '
                'stacktrace_confidence INTEGER, '
                'secret_detection TEXT, '
                'secret_redacted TEXT, '
                'secret_confidence INTEGER, '
                'secret_count INTEGER, '
                'secret_types TEXT, '
                'malware_detection TEXT, '
                'malware_subtype TEXT, '
                'malware_family TEXT, '
                'malware_signal TEXT, '
                'malware_confidence INTEGER, '
                'malware_count INTEGER, '
                'malware_signals TEXT, '
                'shadow_detection TEXT, '
                'shadow_confidence INTEGER, '
                'shadow_reason TEXT, '
                'shadow_base_url TEXT, '
                'shadow_variant TEXT, '
                'shadow_similarity REAL, '
                'shadow_base_size INTEGER, '
                'shadow_size INTEGER, '
                'openredirect_detection TEXT, '
                'openredirect_confidence INTEGER, '
                'openredirect_parameter TEXT, '
                'openredirect_variant TEXT, '
                'openredirect_payload TEXT, '
                'openredirect_payload_family TEXT, '
                'openredirect_location TEXT, '
                'openredirect_source_url TEXT, '
                'redirect_type TEXT, '
                'redirect_reason TEXT, '
                'redirect_location TEXT, '
                'redirect_target_scheme TEXT, '
                'redirect_target_host TEXT, '
                'redirect_target_path TEXT, '
                'redirect_same_origin INTEGER, '
                'redirect_cross_origin INTEGER, '
                'redirect_confidence TEXT, '
                'finding_type TEXT, '
                'finding_severity TEXT, '
                'finding_reason TEXT, '
                'finding_confidence TEXT, '
                'finding_source TEXT, '
                'finding_evidence TEXT'
                ')'
            )
            cursor.execute(
                'CREATE TABLE fingerprint ('
                'id INTEGER PRIMARY KEY CHECK (id = 1), '
                'category TEXT NOT NULL, '
                'name TEXT NOT NULL, '
                'confidence INTEGER NOT NULL, '
                'runtime_name TEXT, '
                'runtime_confidence INTEGER, '
                'infrastructure_provider TEXT, '
                'infrastructure_confidence INTEGER, '
                'hsts_present INTEGER, '
                'hsts_grade TEXT, '
                'hsts_max_age INTEGER, '
                'hsts_include_subdomains INTEGER, '
                'hsts_preload INTEGER, '
                'hsts_preload_ready INTEGER, '
                'hsts_http_to_https_redirect INTEGER, '
                'hsts_warnings TEXT, '
                'supercookie_risk TEXT, '
                'supercookie_score INTEGER, '
                'supercookie_hsts_tracking_surface INTEGER, '
                'supercookie_etag_tracking_surface INTEGER, '
                'supercookie_cache_tracking_surface INTEGER, '
                'supercookie_persistent_surface INTEGER, '
                'privacy_supercookie_warnings TEXT, '
                'supercookie_signals TEXT'
                ')'
            )
            cursor.execute(
                'CREATE TABLE runtime_signals ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'type TEXT NOT NULL, '
                'value TEXT NOT NULL'
                ')'
            )
            cursor.execute(
                'CREATE TABLE fingerprint_signals ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'type TEXT NOT NULL, '
                'value TEXT NOT NULL'
                ')'
            )

            cursor.executemany(
                'INSERT INTO metadata(key, value) VALUES(?, ?)',
                [
                    ('target', self._target),
                    ('plugin', self.PLUGIN_NAME),
                ]
            )

            cursor.executemany(
                'INSERT INTO summary(status, total) VALUES(?, ?)',
                [
                    (str(status), int(total))
                    for status, total in self._data.get('total', {}).items()
                ]
            )

            rows = []
            str_or_none = self._str_or_none
            int_or_none = self._int_or_none
            float_or_none = self._float_or_none
            bool_int_or_none = self._bool_int_or_none
            joined_or_none = self._joined_or_none
            json_or_none = self._json_or_none
            dict_or_empty = self._dict_or_empty

            for status in self._data.get('items', {}).keys():
                for item in self.get_report_items(status):
                    stacktrace_detection = dict_or_empty(item.get('stacktrace_detection'))
                    secret_detection = dict_or_empty(item.get('secret_detection'))
                    malware_detection = dict_or_empty(item.get('malware_detection'))
                    shadow_detection = dict_or_empty(item.get('shadow_detection'))
                    openredirect_detection = dict_or_empty(item.get('openredirect_detection'))
                    redirect_classification = dict_or_empty(item.get('redirect_classification'))
                    passive_finding = dict_or_empty(item.get('passive_finding'))

                    rows.append(
                        (
                            str(status),
                            str(item.get('url', '')),
                            str(item.get('code', '-')),
                            str(item.get('size', '0B')),
                            str_or_none(item.get('bypass')),
                            str_or_none(item.get('bypass_profile')),
                            str_or_none(item.get('bypass_header')),
                            str_or_none(item.get('bypass_value')),
                            str_or_none(item.get('bypass_variant')),
                            str_or_none(item.get('bypass_url')),
                            str_or_none(item.get('bypass_from_status')),
                            str_or_none(item.get('bypass_to_status')),
                            str_or_none(item.get('bypass_from_code')),
                            str_or_none(item.get('bypass_to_code')),
                            int_or_none(item.get('bypass_score')),
                            joined_or_none(item.get('bypass_reasons')),
                            str_or_none(stacktrace_detection.get('type')),
                            str_or_none(stacktrace_detection.get('runtime')),
                            str_or_none(stacktrace_detection.get('signal')),
                            int_or_none(stacktrace_detection.get('confidence')),
                            str_or_none(secret_detection.get('type')),
                            str_or_none(secret_detection.get('redacted')),
                            int_or_none(secret_detection.get('confidence')),
                            int_or_none(secret_detection.get('count')),
                            joined_or_none(secret_detection.get('types')),
                            str_or_none(malware_detection.get('type')),
                            str_or_none(malware_detection.get('subtype')),
                            str_or_none(malware_detection.get('family')),
                            str_or_none(malware_detection.get('signal')),
                            int_or_none(malware_detection.get('confidence')),
                            int_or_none(malware_detection.get('count')),
                            joined_or_none(malware_detection.get('signals')),
                            str_or_none(shadow_detection.get('type')),
                            int_or_none(shadow_detection.get('confidence')),
                            str_or_none(shadow_detection.get('reason')),
                            str_or_none(shadow_detection.get('base_url')),
                            str_or_none(shadow_detection.get('variant')),
                            float_or_none(shadow_detection.get('similarity')),
                            int_or_none(shadow_detection.get('base_size')),
                            int_or_none(shadow_detection.get('shadow_size')),
                            str_or_none(openredirect_detection.get('type')),
                            int_or_none(openredirect_detection.get('confidence')),
                            str_or_none(openredirect_detection.get('parameter')),
                            str_or_none(openredirect_detection.get('variant')),
                            str_or_none(openredirect_detection.get('payload')),
                            str_or_none(openredirect_detection.get('payload_family')),
                            str_or_none(openredirect_detection.get('location')),
                            str_or_none(openredirect_detection.get('source_url')),
                            str_or_none(redirect_classification.get('type')),
                            str_or_none(redirect_classification.get('reason')),
                            str_or_none(redirect_classification.get('location')),
                            str_or_none(redirect_classification.get('target_scheme')),
                            str_or_none(redirect_classification.get('target_host')),
                            str_or_none(redirect_classification.get('target_path')),
                            bool_int_or_none(redirect_classification.get('same_origin')),
                            bool_int_or_none(redirect_classification.get('cross_origin')),
                            str_or_none(redirect_classification.get('confidence')),
                            str_or_none(passive_finding.get('type')),
                            str_or_none(passive_finding.get('severity')),
                            str_or_none(passive_finding.get('reason')),
                            str_or_none(passive_finding.get('confidence')),
                            json_or_none(passive_finding.get('source')),
                            json_or_none(passive_finding.get('evidence')),
                        )
                    )

            if len(rows) > 0:
                cursor.executemany(
                    'INSERT INTO items('
                    'status, url, code, size, '
                    'bypass, bypass_profile, bypass_header, bypass_value, bypass_variant, bypass_url, '
                    'bypass_from_status, bypass_to_status, bypass_from_code, bypass_to_code, '
                    'bypass_score, bypass_reasons, stacktrace_detection, stacktrace_runtime, stacktrace_signal, '
                    'stacktrace_confidence, secret_detection, secret_redacted, secret_confidence, secret_count, secret_types, '
                    'malware_detection, malware_subtype, malware_family, malware_signal, malware_confidence, '
                    'malware_count, malware_signals, shadow_detection, shadow_confidence, shadow_reason, shadow_base_url, shadow_variant, '
                    'shadow_similarity, shadow_base_size, shadow_size, openredirect_detection, '
                    'openredirect_confidence, openredirect_parameter, openredirect_variant, openredirect_payload, '
                    'openredirect_payload_family, openredirect_location, openredirect_source_url, redirect_type, redirect_reason, '
                    'redirect_location, redirect_target_scheme, redirect_target_host, redirect_target_path, '
                    'redirect_same_origin, redirect_cross_origin, redirect_confidence, finding_type, finding_severity, '
                    'finding_reason, finding_confidence, finding_source, finding_evidence'
                    ') VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    rows
                )

            fingerprint = self._data.get('fingerprint')
            if isinstance(fingerprint, dict) and len(fingerprint) > 0:
                runtime = fingerprint.get('runtime')
                runtime_name = runtime.get('name') if isinstance(runtime, dict) else None
                runtime_confidence = runtime.get('confidence') if isinstance(runtime, dict) else None

                infrastructure = fingerprint.get('infrastructure')
                infrastructure_provider = None
                infrastructure_confidence = None

                if isinstance(infrastructure, dict) and len(infrastructure) > 0:
                    infrastructure_provider = infrastructure.get('provider')
                    infrastructure_confidence = infrastructure.get('confidence')

                security_headers = dict_or_empty(fingerprint.get('security_headers'))
                hsts = dict_or_empty(security_headers.get('hsts'))

                privacy_risks = dict_or_empty(fingerprint.get('privacy_risks'))
                supercookie = dict_or_empty(privacy_risks.get('supercookie'))

                cursor.execute(
                    'INSERT INTO fingerprint('
                    'id, category, name, confidence, runtime_name, runtime_confidence, '
                    'infrastructure_provider, infrastructure_confidence, hsts_present, hsts_grade, '
                    'hsts_max_age, hsts_include_subdomains, hsts_preload, hsts_preload_ready, '
                    'hsts_http_to_https_redirect, hsts_warnings, supercookie_risk, '
                    'supercookie_score, supercookie_hsts_tracking_surface, '
                    'supercookie_etag_tracking_surface, supercookie_cache_tracking_surface, '
                    'supercookie_persistent_surface, privacy_supercookie_warnings, '
                    'supercookie_signals'
                    ') VALUES(1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (
                        str(fingerprint.get('category', 'custom')),
                        str(fingerprint.get('name', 'Unknown custom stack')),
                        int(fingerprint.get('confidence', 0)),
                        str_or_none(runtime_name),
                        int_or_none(runtime_confidence),
                        str_or_none(infrastructure_provider),
                        int_or_none(infrastructure_confidence),
                        bool_int_or_none(hsts.get('present')),
                        str_or_none(hsts.get('grade')),
                        int_or_none(hsts.get('max_age')),
                        bool_int_or_none(hsts.get('include_subdomains')),
                        bool_int_or_none(hsts.get('preload')),
                        bool_int_or_none(hsts.get('preload_ready')),
                        bool_int_or_none(hsts.get('http_to_https_redirect')),
                        joined_or_none(hsts.get('warnings')) if isinstance(hsts.get('warnings'), list) else None,
                        str_or_none(supercookie.get('risk')),
                        int_or_none(supercookie.get('score')),
                        bool_int_or_none(supercookie.get('hsts_tracking_surface')),
                        bool_int_or_none(supercookie.get('etag_tracking_surface')),
                        bool_int_or_none(supercookie.get('cache_tracking_surface')),
                        bool_int_or_none(supercookie.get('persistent_cookie_surface')),
                        joined_or_none(supercookie.get('warnings')) if isinstance(supercookie.get('warnings'), list) else None,
                        joined_or_none(supercookie.get('signals')) if isinstance(supercookie.get('signals'), list) else None,
                    )
                )

                signals = fingerprint.get('signals', [])
                if isinstance(signals, list) and len(signals) > 0:
                    cursor.executemany(
                        'INSERT INTO fingerprint_signals(type, value) VALUES(?, ?)',
                        [
                            (
                                str(signal.get('type', 'unknown')),
                                str(signal.get('value', '')),
                            )
                            for signal in signals
                            if isinstance(signal, dict)
                        ]
                    )

                runtime_signals = runtime.get('signals', []) if isinstance(runtime, dict) else []
                if isinstance(runtime_signals, list) and len(runtime_signals) > 0:
                    cursor.executemany(
                        'INSERT INTO runtime_signals(type, value) VALUES(?, ?)',
                        [
                            (str(signal.get('type', 'unknown')), str(signal.get('value', '')))
                            for signal in runtime_signals
                            if isinstance(signal, dict)
                        ]
                    )

            connection.commit()
            tpl.info(key='report', plugin=self.PLUGIN_NAME, dest=filesystem.getabsname(database_path))
        except (sqlite3.Error, FileSystemError, ValueError, TypeError) as error:
            raise Exception(error)
        finally:
            if connection is not None:
                connection.close()
