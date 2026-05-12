# -*- coding: utf-8 -*-

import json
import os
import sqlite3
import tempfile
import unittest

from src.lib.diff import DiffReportReader, DiffValidationError


class TestDiffReportReader(unittest.TestCase):
    """Diff report reader and validation coverage."""

    def setUp(self):
        """Create a temporary workspace."""

        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Remove temporary files."""

        self.tmpdir.cleanup()

    def path(self, name):
        """Return path inside temporary workspace."""

        return os.path.join(self.tmpdir.name, name)

    def write_sqlite_report(self, name='report.sqlite', rows=None, target='example.com'):
        """Create a minimal OpenDoor SQLite report."""

        if rows is None:
            rows = [('success', 'https://example.com/admin', '200', '12B')]

        path = self.path(name)
        connection = sqlite3.connect(path)
        try:
            cursor = connection.cursor()
            cursor.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            cursor.execute('CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT, url TEXT, code TEXT, size TEXT)')
            cursor.execute('INSERT INTO metadata(key, value) VALUES(?, ?)', ('target', target))
            cursor.executemany('INSERT INTO items(status, url, code, size) VALUES(?, ?, ?, ?)', rows)
            connection.commit()
        finally:
            connection.close()

        return path

    def write_json_report(self, name='report.json', payload=None):
        """Create an OpenDoor JSON report."""

        if payload is None:
            payload = {
                'target': 'example.com',
                'report_items': {
                    'success': [
                        {'url': 'https://example.com/admin', 'code': '200', 'size': '12B'},
                    ],
                },
            }

        path = self.path(name)
        with open(path, 'w', encoding='utf-8') as handler:
            json.dump(payload, handler, sort_keys=True)

        return path

    def test_parse_pair_accepts_exactly_two_reports(self):
        """parse_pair should accept previous/current syntax."""

        self.assertEqual(
            DiffReportReader().parse_pair('old.sqlite:new.sqlite'),
            ('old.sqlite', 'new.sqlite'),
        )

    def test_parse_pair_rejects_empty_or_malformed_values(self):
        """parse_pair should reject missing or over-specified report pairs."""

        reader = DiffReportReader()
        for value in ('', 'old.sqlite', 'old.sqlite:', ':new.sqlite', 'a:b:c'):
            with self.subTest(value=value):
                with self.assertRaises(DiffValidationError):
                    reader.parse_pair(value)

    def test_detect_format_rejects_missing_directory_and_unsupported_files(self):
        """detect_format should gracefully reject invalid paths and formats."""

        reader = DiffReportReader()
        unsupported = self.path('report.txt')
        with open(unsupported, 'w', encoding='utf-8') as handler:
            handler.write('not supported')

        with self.assertRaisesRegex(DiffValidationError, 'does not exist'):
            reader.detect_format(self.path('missing.sqlite'))

        with self.assertRaisesRegex(DiffValidationError, 'not a file'):
            reader.detect_format(self.tmpdir.name)

        with self.assertRaisesRegex(DiffValidationError, 'Unsupported diff report format'):
            reader.detect_format(unsupported)

    def test_read_pair_rejects_mixed_supported_formats(self):
        """Diff MVP should not compare SQLite and JSON in one command."""

        sqlite_path = self.write_sqlite_report('old.sqlite')
        json_path = self.write_json_report('new.json')

        with self.assertRaisesRegex(DiffValidationError, 'same supported format'):
            DiffReportReader().read_pair('{0}:{1}'.format(sqlite_path, json_path))

    def test_read_pair_loads_two_sqlite_reports(self):
        """Reader should load two same-format SQLite reports."""

        old_path = self.write_sqlite_report('old.sqlite', rows=[
            ('forbidden', 'https://example.com/admin', '403', '10B'),
        ])
        new_path = self.write_sqlite_report('new.sqlite', rows=[
            ('success', 'https://example.com/admin', '200', '12B'),
        ])

        previous, current = DiffReportReader().read_pair('{0}:{1}'.format(old_path, new_path))

        self.assertEqual(previous.format, 'sqlite')
        self.assertEqual(current.format, 'sqlite')
        self.assertEqual(previous.target, 'example.com')
        self.assertEqual(previous.findings[0].bucket, 'forbidden')
        self.assertEqual(current.findings[0].status, '200')

    def test_read_pair_loads_two_json_reports(self):
        """Reader should load two same-format JSON reports."""

        old_path = self.write_json_report('old.json')
        new_path = self.write_json_report('new.json', payload={
            'target': 'example.com',
            'report_items': {
                'secret': [
                    {
                        'url': 'https://example.com/config.json',
                        'code': 200,
                        'size': '1KB',
                        'method': 'get',
                    },
                ],
            },
        })

        previous, current = DiffReportReader().read_pair('{0}:{1}'.format(old_path, new_path))

        self.assertEqual(previous.format, 'json')
        self.assertEqual(current.findings[0].bucket, 'secret')
        self.assertEqual(current.findings[0].method, 'GET')

    def test_sqlite_reader_rejects_invalid_sqlite_file(self):
        """Invalid SQLite files should become graceful diff errors."""

        path = self.path('broken.sqlite')
        with open(path, 'w', encoding='utf-8') as handler:
            handler.write('not sqlite')

        with self.assertRaisesRegex(DiffValidationError, 'Invalid SQLite report'):
            DiffReportReader().read(path)

    def test_sqlite_reader_rejects_missing_opendoor_schema(self):
        """SQLite reports must contain OpenDoor report tables and columns."""

        path = self.path('empty.sqlite')
        connection = sqlite3.connect(path)
        try:
            connection.execute('CREATE TABLE unrelated (id INTEGER)')
            connection.commit()
        finally:
            connection.close()

        with self.assertRaisesRegex(DiffValidationError, 'missing OpenDoor table'):
            DiffReportReader().read(path)

    def test_sqlite_reader_rejects_missing_item_columns(self):
        """SQLite items table must expose the minimal diff columns."""

        path = self.path('bad-schema.sqlite')
        connection = sqlite3.connect(path)
        try:
            connection.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            connection.execute('CREATE TABLE items (id INTEGER PRIMARY KEY, url TEXT)')
            connection.commit()
        finally:
            connection.close()

        with self.assertRaisesRegex(DiffValidationError, 'missing item column'):
            DiffReportReader().read(path)

    def test_json_reader_rejects_invalid_json_and_missing_report_items(self):
        """JSON reports must be valid OpenDoor report objects."""

        invalid = self.path('invalid.json')
        with open(invalid, 'w', encoding='utf-8') as handler:
            handler.write('{')

        missing_items = self.write_json_report('missing-items.json', payload={'target': 'example.com'})

        with self.assertRaisesRegex(DiffValidationError, 'Invalid JSON report'):
            DiffReportReader().read(invalid)

        with self.assertRaisesRegex(DiffValidationError, 'missing OpenDoor report items'):
            DiffReportReader().read(missing_items)

    def test_json_reader_rejects_invalid_bucket_and_item_shapes(self):
        """JSON bucket and item shapes should be validated before diffing."""

        bad_bucket = self.write_json_report('bad-bucket.json', payload={
            'report_items': {'success': {'url': 'https://example.com/admin'}},
        })
        bad_item = self.write_json_report('bad-item.json', payload={
            'report_items': {'success': ['https://example.com/admin']},
        })

        with self.assertRaisesRegex(DiffValidationError, 'bucket success must contain a list'):
            DiffReportReader().read(bad_bucket)

        with self.assertRaisesRegex(DiffValidationError, 'report item must be an object'):
            DiffReportReader().read(bad_item)

    def test_json_reader_accepts_plain_items_fallback(self):
        """Older JSON reports with items buckets should remain readable."""

        path = self.write_json_report('plain-items.json', payload={
            'host': 'legacy.local',
            'items': {
                'success': ['https://legacy.local/admin'],
            },
        })

        report = DiffReportReader().read(path)

        self.assertEqual(report.target, 'legacy.local')
        self.assertEqual(report.findings[0].url, 'https://legacy.local/admin')
        self.assertEqual(report.findings[0].status, '-')

    def test_reader_rejects_items_without_url(self):
        """Every normalized finding needs a URL identity."""

        path = self.write_json_report('missing-url.json', payload={
            'report_items': {'success': [{'code': 200, 'size': '1B'}]},
        })

        with self.assertRaisesRegex(DiffValidationError, 'url is required'):
            DiffReportReader().read(path)


if __name__ == '__main__':
    unittest.main()
