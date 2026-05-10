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


class TestStacktraceReportMetadata(unittest.TestCase):
    """Report and Browser metadata tests for stacktrace stacktrace findings."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'debug.local'
        self.stacktrace_detection = {
            'type': 'stacktrace',
            'runtime': 'python',
            'signal': 'python-traceback',
            'confidence': 95,
        }
        self.data = {
            'items': {
                'stacktrace': ['https://debug.local/error'],
            },
            'report_items': {
                'stacktrace': [
                    {
                        'url': 'https://debug.local/error',
                        'code': '500',
                        'size': '2KB',
                        'stacktrace_detection': dict(self.stacktrace_detection),
                    }
                ],
            },
            'total': {'stacktrace': 1},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_browser_keeps_stacktrace_detection_metadata_as_nested_object(self):
        """Browser.__catch_report_data() should preserve stacktrace_detection as one nested object."""

        br = Browser.__new__(Browser)
        setattr(br, '_Browser__result', {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()})

        br._Browser__catch_report_data(
            'stacktrace',
            'https://debug.local/error',
            '2KB',
            '500',
            metadata={'stacktrace_detection': dict(self.stacktrace_detection)},
        )

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['stacktrace'], 1)
        self.assertEqual(result['items']['stacktrace'], ['https://debug.local/error'])
        self.assertEqual(result['report_items']['stacktrace'][0]['stacktrace_detection'], self.stacktrace_detection)

    def test_txt_format_includes_compact_stacktrace_detection_summary(self):
        """Plain text item formatting should expose stacktrace evidence."""

        actual = PluginProvider.format_report_item(self.data['report_items']['stacktrace'][0])

        self.assertEqual(
            actual,
            'https://debug.local/error - 500 - 2KB | '
            'stacktrace=stacktrace, runtime=python, signal=python-traceback, confidence=95%'
        )

    def test_csv_report_exposes_queryable_stacktrace_columns(self):
        """CSV report should flatten stacktrace_detection into stable columns."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, self.target, self.target + '.csv')
        with open(report_file, 'r', newline='', encoding='utf-8') as handler:
            rows = list(csv.DictReader(handler))

        self.assertEqual(rows[0]['status'], 'stacktrace')
        self.assertEqual(rows[0]['stacktrace_detection'], 'stacktrace')
        self.assertEqual(rows[0]['stacktrace_runtime'], 'python')
        self.assertEqual(rows[0]['stacktrace_signal'], 'python-traceback')
        self.assertEqual(rows[0]['stacktrace_confidence'], '95')

    def test_sqlite_report_exposes_queryable_stacktrace_columns(self):
        """SQLite report should flatten stacktrace_detection into queryable columns."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        database_path = os.path.join(self.base_dir, self.target, self.target + '.sqlite')
        connection = sqlite3.connect(database_path)
        row = connection.execute(
            'SELECT status, stacktrace_detection, stacktrace_runtime, stacktrace_signal, stacktrace_confidence FROM items'
        ).fetchone()
        connection.close()

        self.assertEqual(row, ('stacktrace', 'stacktrace', 'python', 'python-traceback', 95))

    def test_json_report_preserves_nested_stacktrace_detection_object(self):
        """JSON report should serialize the original nested stacktrace_detection object."""

        with patch('src.lib.reporter.plugins.json.filesystem.clear'), \
                patch('src.lib.reporter.plugins.json.JsonReportPlugin.record') as record_mock:
            plugin = JsonReportPlugin(self.target, self.data, directory=self.base_dir)
            plugin.process()

        payload = json.loads(record_mock.call_args.args[2])
        self.assertEqual(payload['report_items']['stacktrace'][0]['stacktrace_detection'], self.stacktrace_detection)

    def test_html_report_renders_nested_stacktrace_detection_object(self):
        """HTML report should render nested stacktrace_detection details."""

        html = render_html_report(self.target, self.data)

        self.assertIn('stacktrace_detection', html)
        self.assertIn('python-traceback', html)
        self.assertIn('stacktrace', html)

    def test_txt_report_process_writes_debug_bucket_file(self):
        """TXT reporter should write stacktrace bucket lines with compact evidence."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear'):
            plugin = TextReportPlugin(self.target, self.data, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        record_mock.assert_called_once_with(
            '/tmp/reports',
            'stacktrace',
            [
                'https://debug.local/error - 500 - 2KB | '
                'stacktrace=stacktrace, runtime=python, signal=python-traceback, confidence=95%'
            ],
            '\n'
        )

    def test_txt_format_handles_minimal_stacktrace_detection_metadata(self):
        """Plain text formatter should tolerate missing optional debug evidence fields."""

        actual = PluginProvider.format_report_item({
            'url': 'https://debug.local/error',
            'code': '500',
            'size': '2KB',
            'stacktrace_detection': {'type': 'stacktrace'},
        })

        self.assertEqual(actual, 'https://debug.local/error - 500 - 2KB | stacktrace=stacktrace')

    def test_sarif_report_uses_stacktrace_rule_and_preserves_nested_properties(self):
        """SARIF report should classify stacktrace findings and preserve stacktraceDetection properties."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir)
        sarif = plugin.build_sarif_log()
        run = sarif['runs'][0]
        result = run['results'][0]

        self.assertEqual(run['tool']['driver']['rules'][0]['id'], 'opendoor.finding.stacktrace')
        self.assertEqual(result['ruleId'], 'opendoor.finding.stacktrace')
        self.assertEqual(result['level'], 'warning')
        self.assertIn('exposed stacktrace details', result['message']['text'])
        self.assertEqual(result['properties']['stacktraceDetection'], self.stacktrace_detection)


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
                'stacktrace': ['https://mysql-debug.local/metrics.php'],
            },
            'report_items': {
                'stacktrace': [
                    {
                        'url': 'https://mysql-debug.local/metrics.php',
                        'code': '200',
                        'size': '4KB',
                        'stacktrace_detection': dict(self.mysql_detection),
                    }
                ],
            },
            'total': {'stacktrace': 1},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_txt_format_includes_mysql_error_summary(self):
        """Plain text should expose mysql_error signal."""

        actual = PluginProvider.format_report_item(self.data['report_items']['stacktrace'][0])

        self.assertEqual(
            actual,
            'https://mysql-debug.local/metrics.php - 200 - 4KB | '
            'stacktrace=stacktrace, runtime=mysql, signal=mysql-error, confidence=90%'
        )

    def test_csv_report_exposes_mysql_stacktrace_columns(self):
        """CSV should flatten mysql stacktrace_detection."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, self.target, self.target + '.csv')
        with open(report_file, 'r', newline='', encoding='utf-8') as handler:
            rows = list(csv.DictReader(handler))

        self.assertEqual(rows[0]['status'], 'stacktrace')
        self.assertEqual(rows[0]['stacktrace_detection'], 'stacktrace')
        self.assertEqual(rows[0]['stacktrace_runtime'], 'mysql')
        self.assertEqual(rows[0]['stacktrace_signal'], 'mysql-error')
        self.assertEqual(rows[0]['stacktrace_confidence'], '90')

    def test_sqlite_report_exposes_mysql_columns(self):
        """SQLite should store mysql detection data."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        database_path = os.path.join(self.base_dir, self.target, self.target + '.sqlite')
        connection = sqlite3.connect(database_path)
        row = connection.execute(
            'SELECT status, stacktrace_detection, stacktrace_runtime, stacktrace_signal, stacktrace_confidence FROM items'
        ).fetchone()
        connection.close()

        self.assertEqual(row, ('stacktrace', 'stacktrace', 'mysql', 'mysql-error', 90))

    def test_json_report_preserves_mysql_nested_object(self):
        """JSON should keep nested mysql stacktrace_detection."""

        with patch('src.lib.reporter.plugins.json.filesystem.clear'), \
                patch('src.lib.reporter.plugins.json.JsonReportPlugin.record') as record_mock:
            plugin = JsonReportPlugin(self.target, self.data, directory=self.base_dir)
            plugin.process()

        payload = json.loads(record_mock.call_args.args[2])
        self.assertEqual(
            payload['report_items']['stacktrace'][0]['stacktrace_detection'],
            self.mysql_detection
        )

    def test_sarif_report_classifies_mysql_as_stacktrace(self):
        """SARIF should tag mysql findings under stacktrace rule."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir)
        sarif = plugin.build_sarif_log()
        result = sarif['runs'][0]['results'][0]

        self.assertEqual(result['ruleId'], 'opendoor.finding.stacktrace')
        self.assertEqual(result['properties']['stacktraceDetection'], self.mysql_detection)


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
                'stacktrace': ['https://pdo-debug.local/api/users'],
            },
            'report_items': {
                'stacktrace': [
                    {
                        'url': 'https://pdo-debug.local/api/users',
                        'code': '500',
                        'size': '1KB',
                        'stacktrace_detection': dict(self.pdo_detection),
                    }
                ],
            },
            'total': {'stacktrace': 1},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_txt_format_includes_pdo_exception_summary(self):
        """Plain text should expose pdo-exception signal."""

        actual = PluginProvider.format_report_item(self.data['report_items']['stacktrace'][0])

        self.assertEqual(
            actual,
            'https://pdo-debug.local/api/users - 500 - 1KB | '
            'stacktrace=stacktrace, runtime=pdo, signal=pdo-exception, confidence=90%'
        )

    def test_csv_report_exposes_pdo_stacktrace_columns(self):
        """CSV should flatten PDO stacktrace_detection."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, self.target, self.target + '.csv')
        with open(report_file, 'r', newline='', encoding='utf-8') as handler:
            rows = list(csv.DictReader(handler))

        self.assertEqual(rows[0]['status'], 'stacktrace')
        self.assertEqual(rows[0]['stacktrace_detection'], 'stacktrace')
        self.assertEqual(rows[0]['stacktrace_runtime'], 'pdo')
        self.assertEqual(rows[0]['stacktrace_signal'], 'pdo-exception')
        self.assertEqual(rows[0]['stacktrace_confidence'], '90')

    def test_sqlite_report_exposes_pdo_columns(self):
        """SQLite should store PDO detection data."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        database_path = os.path.join(self.base_dir, self.target, self.target + '.sqlite')
        connection = sqlite3.connect(database_path)
        row = connection.execute(
            'SELECT status, stacktrace_detection, stacktrace_runtime, stacktrace_signal, stacktrace_confidence FROM items'
        ).fetchone()
        connection.close()

        self.assertEqual(row, ('stacktrace', 'stacktrace', 'pdo', 'pdo-exception', 90))

    def test_json_report_preserves_pdo_nested_object(self):
        """JSON should keep nested PDO stacktrace_detection."""

        with patch('src.lib.reporter.plugins.json.filesystem.clear'), \
                patch('src.lib.reporter.plugins.json.JsonReportPlugin.record') as record_mock:
            plugin = JsonReportPlugin(self.target, self.data, directory=self.base_dir)
            plugin.process()

        payload = json.loads(record_mock.call_args.args[2])
        self.assertEqual(
            payload['report_items']['stacktrace'][0]['stacktrace_detection'],
            self.pdo_detection
        )

    def test_html_report_renders_pdo_detection(self):
        """HTML should include pdo-exception details."""

        html = render_html_report(self.target, self.data)

        self.assertIn('stacktrace_detection', html)
        self.assertIn('pdo-exception', html)
        self.assertIn('pdo', html)

    def test_sarif_report_classifies_pdo_as_stacktrace(self):
        """SARIF should tag PDO findings under stacktrace rule."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir)
        sarif = plugin.build_sarif_log()
        result = sarif['runs'][0]['results'][0]

        self.assertEqual(result['ruleId'], 'opendoor.finding.stacktrace')
        self.assertEqual(result['properties']['stacktraceDetection'], self.pdo_detection)

    def test_txt_report_process_writes_pdo_bucket_file(self):
        """TXT reporter should write PDO stacktrace bucket lines."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear'):
            plugin = TextReportPlugin(self.target, self.data, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        record_mock.assert_called_once_with(
            '/tmp/reports',
            'stacktrace',
            [
                'https://pdo-debug.local/api/users - 500 - 1KB | '
                'stacktrace=stacktrace, runtime=pdo, signal=pdo-exception, confidence=90%'
            ],
            '\n'
        )


if __name__ == '__main__':
    unittest.main()