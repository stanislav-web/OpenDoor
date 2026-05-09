# -*- coding: utf-8 -*-

import csv
import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from src.core import helper
from src.lib.browser.browser import Browser
from src.lib.reporter.plugins.csv import CsvReportPlugin
from src.lib.reporter.plugins.html import render_html_report
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.provider.provider import PluginProvider
from src.lib.reporter.plugins.sarif import SarifReportPlugin
from src.lib.reporter.plugins.sqlite import SqliteReportPlugin
from src.lib.reporter.plugins.txt import TextReportPlugin


class TestStacktraceDebugReportMetadata(unittest.TestCase):
    """Report and Browser metadata tests for stacktrace debug findings."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'debug.local'
        self.debug_detection = {
            'type': 'stacktrace',
            'runtime': 'python',
            'signal': 'python-traceback',
            'confidence': 95,
        }
        self.data = {
            'items': {
                'debug': ['https://debug.local/error'],
            },
            'report_items': {
                'debug': [
                    {
                        'url': 'https://debug.local/error',
                        'code': '500',
                        'size': '2KB',
                        'debug_detection': dict(self.debug_detection),
                    }
                ],
            },
            'total': {'debug': 1},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_browser_keeps_debug_detection_metadata_as_nested_object(self):
        """Browser.__catch_report_data() should preserve debug_detection as one nested object."""

        br = Browser.__new__(Browser)
        setattr(br, '_Browser__result', {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()})

        br._Browser__catch_report_data(
            'debug',
            'https://debug.local/error',
            '2KB',
            '500',
            metadata={'debug_detection': dict(self.debug_detection)},
        )

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['debug'], 1)
        self.assertEqual(result['items']['debug'], ['https://debug.local/error'])
        self.assertEqual(result['report_items']['debug'][0]['debug_detection'], self.debug_detection)

    def test_txt_format_includes_compact_debug_detection_summary(self):
        """Plain text item formatting should expose stacktrace evidence."""

        actual = PluginProvider.format_report_item(self.data['report_items']['debug'][0])

        self.assertEqual(
            actual,
            'https://debug.local/error - 500 - 2KB | '
            'debug=stacktrace, runtime=python, signal=python-traceback, confidence=95%'
        )

    def test_csv_report_exposes_queryable_debug_columns(self):
        """CSV report should flatten debug_detection into stable columns."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, self.target, self.target + '.csv')
        with open(report_file, 'r', newline='', encoding='utf-8') as handler:
            rows = list(csv.DictReader(handler))

        self.assertEqual(rows[0]['status'], 'debug')
        self.assertEqual(rows[0]['debug_detection'], 'stacktrace')
        self.assertEqual(rows[0]['debug_runtime'], 'python')
        self.assertEqual(rows[0]['debug_signal'], 'python-traceback')
        self.assertEqual(rows[0]['debug_confidence'], '95')

    def test_sqlite_report_exposes_queryable_debug_columns(self):
        """SQLite report should flatten debug_detection into queryable columns."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        database_path = os.path.join(self.base_dir, self.target, self.target + '.sqlite')
        connection = sqlite3.connect(database_path)
        row = connection.execute(
            'SELECT status, debug_detection, debug_runtime, debug_signal, debug_confidence FROM items'
        ).fetchone()
        connection.close()

        self.assertEqual(row, ('debug', 'stacktrace', 'python', 'python-traceback', 95))

    def test_json_report_preserves_nested_debug_detection_object(self):
        """JSON report should serialize the original nested debug_detection object."""

        with patch('src.lib.reporter.plugins.json.filesystem.clear'), \
                patch('src.lib.reporter.plugins.json.JsonReportPlugin.record') as record_mock:
            plugin = JsonReportPlugin(self.target, self.data, directory=self.base_dir)
            plugin.process()

        payload = json.loads(record_mock.call_args.args[2])
        self.assertEqual(payload['report_items']['debug'][0]['debug_detection'], self.debug_detection)

    def test_html_report_renders_nested_debug_detection_object(self):
        """HTML report should render nested debug_detection details."""

        html = render_html_report(self.target, self.data)

        self.assertIn('debug_detection', html)
        self.assertIn('python-traceback', html)
        self.assertIn('stacktrace', html)

    def test_txt_report_process_writes_debug_bucket_file(self):
        """TXT reporter should write debug bucket lines with compact evidence."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear'):
            plugin = TextReportPlugin(self.target, self.data, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        record_mock.assert_called_once_with(
            '/tmp/reports',
            'debug',
            [
                'https://debug.local/error - 500 - 2KB | '
                'debug=stacktrace, runtime=python, signal=python-traceback, confidence=95%'
            ],
            '\n'
        )

    def test_txt_format_handles_minimal_debug_detection_metadata(self):
        """Plain text formatter should tolerate missing optional debug evidence fields."""

        actual = PluginProvider.format_report_item({
            'url': 'https://debug.local/error',
            'code': '500',
            'size': '2KB',
            'debug_detection': {'type': 'stacktrace'},
        })

        self.assertEqual(actual, 'https://debug.local/error - 500 - 2KB | debug=stacktrace')

    def test_sarif_report_uses_debug_rule_and_preserves_nested_properties(self):
        """SARIF report should classify debug findings and preserve debugDetection properties."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir)
        sarif = plugin.build_sarif_log()
        run = sarif['runs'][0]
        result = run['results'][0]

        self.assertEqual(run['tool']['driver']['rules'][0]['id'], 'opendoor.finding.debug')
        self.assertEqual(result['ruleId'], 'opendoor.finding.debug')
        self.assertEqual(result['level'], 'warning')
        self.assertIn('exposed debug stacktrace', result['message']['text'])
        self.assertEqual(result['properties']['debugDetection'], self.debug_detection)


class TestStacktraceMysqlDetection(unittest.TestCase):
    """Tests for MySQL (mysql_*) stacktrace detection in reports."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'mysql-debug.local'
        self.mysql_detection = {
            'type': 'stacktrace',
            'runtime': 'mysql',
            'signal': 'mysql-error',
            'confidence': 90,
        }
        self.data = {
            'items': {
                'debug': ['https://mysql-debug.local/metrics.php'],
            },
            'report_items': {
                'debug': [
                    {
                        'url': 'https://mysql-debug.local/metrics.php',
                        'code': '200',
                        'size': '4KB',
                        'debug_detection': dict(self.mysql_detection),
                    }
                ],
            },
            'total': {'debug': 1},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_txt_format_includes_mysql_error_summary(self):
        """Plain text should expose mysql_error signal."""

        actual = PluginProvider.format_report_item(self.data['report_items']['debug'][0])

        self.assertEqual(
            actual,
            'https://mysql-debug.local/metrics.php - 200 - 4KB | '
            'debug=stacktrace, runtime=mysql, signal=mysql-error, confidence=90%'
        )

    def test_csv_report_exposes_mysql_debug_columns(self):
        """CSV should flatten mysql debug_detection."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, self.target, self.target + '.csv')
        with open(report_file, 'r', newline='', encoding='utf-8') as handler:
            rows = list(csv.DictReader(handler))

        self.assertEqual(rows[0]['status'], 'debug')
        self.assertEqual(rows[0]['debug_detection'], 'stacktrace')
        self.assertEqual(rows[0]['debug_runtime'], 'mysql')
        self.assertEqual(rows[0]['debug_signal'], 'mysql-error')
        self.assertEqual(rows[0]['debug_confidence'], '90')

    def test_sqlite_report_exposes_mysql_columns(self):
        """SQLite should store mysql detection data."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        database_path = os.path.join(self.base_dir, self.target, self.target + '.sqlite')
        connection = sqlite3.connect(database_path)
        row = connection.execute(
            'SELECT status, debug_detection, debug_runtime, debug_signal, debug_confidence FROM items'
        ).fetchone()
        connection.close()

        self.assertEqual(row, ('debug', 'stacktrace', 'mysql', 'mysql-error', 90))

    def test_json_report_preserves_mysql_nested_object(self):
        """JSON should keep nested mysql debug_detection."""

        with patch('src.lib.reporter.plugins.json.filesystem.clear'), \
                patch('src.lib.reporter.plugins.json.JsonReportPlugin.record') as record_mock:
            plugin = JsonReportPlugin(self.target, self.data, directory=self.base_dir)
            plugin.process()

        payload = json.loads(record_mock.call_args.args[2])
        self.assertEqual(
            payload['report_items']['debug'][0]['debug_detection'],
            self.mysql_detection
        )

    def test_sarif_report_classifies_mysql_as_debug(self):
        """SARIF should tag mysql findings under debug rule."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir)
        sarif = plugin.build_sarif_log()
        result = sarif['runs'][0]['results'][0]

        self.assertEqual(result['ruleId'], 'opendoor.finding.debug')
        self.assertEqual(result['properties']['debugDetection'], self.mysql_detection)


class TestStacktracePdoDetection(unittest.TestCase):
    """Tests for PDO (PDOException / PDO::*) stacktrace detection in reports."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'pdo-debug.local'
        self.pdo_detection = {
            'type': 'stacktrace',
            'runtime': 'pdo',
            'signal': 'pdo-exception',
            'confidence': 90,
        }
        self.data = {
            'items': {
                'debug': ['https://pdo-debug.local/api/users'],
            },
            'report_items': {
                'debug': [
                    {
                        'url': 'https://pdo-debug.local/api/users',
                        'code': '500',
                        'size': '1KB',
                        'debug_detection': dict(self.pdo_detection),
                    }
                ],
            },
            'total': {'debug': 1},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_txt_format_includes_pdo_exception_summary(self):
        """Plain text should expose pdo-exception signal."""

        actual = PluginProvider.format_report_item(self.data['report_items']['debug'][0])

        self.assertEqual(
            actual,
            'https://pdo-debug.local/api/users - 500 - 1KB | '
            'debug=stacktrace, runtime=pdo, signal=pdo-exception, confidence=90%'
        )

    def test_csv_report_exposes_pdo_debug_columns(self):
        """CSV should flatten PDO debug_detection."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, self.target, self.target + '.csv')
        with open(report_file, 'r', newline='', encoding='utf-8') as handler:
            rows = list(csv.DictReader(handler))

        self.assertEqual(rows[0]['status'], 'debug')
        self.assertEqual(rows[0]['debug_detection'], 'stacktrace')
        self.assertEqual(rows[0]['debug_runtime'], 'pdo')
        self.assertEqual(rows[0]['debug_signal'], 'pdo-exception')
        self.assertEqual(rows[0]['debug_confidence'], '90')

    def test_sqlite_report_exposes_pdo_columns(self):
        """SQLite should store PDO detection data."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        database_path = os.path.join(self.base_dir, self.target, self.target + '.sqlite')
        connection = sqlite3.connect(database_path)
        row = connection.execute(
            'SELECT status, debug_detection, debug_runtime, debug_signal, debug_confidence FROM items'
        ).fetchone()
        connection.close()

        self.assertEqual(row, ('debug', 'stacktrace', 'pdo', 'pdo-exception', 90))

    def test_json_report_preserves_pdo_nested_object(self):
        """JSON should keep nested PDO debug_detection."""

        with patch('src.lib.reporter.plugins.json.filesystem.clear'), \
                patch('src.lib.reporter.plugins.json.JsonReportPlugin.record') as record_mock:
            plugin = JsonReportPlugin(self.target, self.data, directory=self.base_dir)
            plugin.process()

        payload = json.loads(record_mock.call_args.args[2])
        self.assertEqual(
            payload['report_items']['debug'][0]['debug_detection'],
            self.pdo_detection
        )

    def test_html_report_renders_pdo_detection(self):
        """HTML should include pdo-exception details."""

        html = render_html_report(self.target, self.data)

        self.assertIn('debug_detection', html)
        self.assertIn('pdo-exception', html)
        self.assertIn('pdo', html)

    def test_sarif_report_classifies_pdo_as_debug(self):
        """SARIF should tag PDO findings under debug rule."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir)
        sarif = plugin.build_sarif_log()
        result = sarif['runs'][0]['results'][0]

        self.assertEqual(result['ruleId'], 'opendoor.finding.debug')
        self.assertEqual(result['properties']['debugDetection'], self.pdo_detection)

    def test_txt_report_process_writes_pdo_bucket_file(self):
        """TXT reporter should write PDO debug bucket lines."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear'):
            plugin = TextReportPlugin(self.target, self.data, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        record_mock.assert_called_once_with(
            '/tmp/reports',
            'debug',
            [
                'https://pdo-debug.local/api/users - 500 - 1KB | '
                'debug=stacktrace, runtime=pdo, signal=pdo-exception, confidence=90%'
            ],
            '\n'
        )


if __name__ == '__main__':
    unittest.main()