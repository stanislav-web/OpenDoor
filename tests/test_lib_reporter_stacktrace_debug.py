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
