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


class TestSecretSnifferReportMetadata(unittest.TestCase):
    """Report and Browser metadata tests for Secret Sniffer findings."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'secret.local'
        self.raw_secret = 'AKIA1234567890ABCDEF'
        self.secret_detection = {
            'type': 'aws_access_key',
            'redacted': 'AKIA****CDEF',
            'confidence': 95,
            'count': 1,
            'types': ['aws_access_key'],
            'matches': [
                {
                    'type': 'aws_access_key',
                    'redacted': 'AKIA****CDEF',
                    'confidence': 95,
                    'position': 42,
                }
            ],
        }
        self.data = {
            'items': {
                'secret': ['https://secret.local/config.json'],
            },
            'report_items': {
                'secret': [
                    {
                        'url': 'https://secret.local/config.json',
                        'code': '200',
                        'size': '1KB',
                        'secret_detection': dict(self.secret_detection),
                    }
                ],
            },
            'total': {'secret': 1},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_browser_keeps_secret_detection_metadata_as_nested_object(self):
        """Browser.__catch_report_data() should preserve secret_detection as one nested object."""

        br = Browser.__new__(Browser)
        setattr(br, '_Browser__result', {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()})

        br._Browser__catch_report_data(
            'secret',
            'https://secret.local/config.json',
            '1KB',
            '200',
            metadata={'secret_detection': dict(self.secret_detection)},
        )

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['secret'], 1)
        self.assertEqual(result['items']['secret'], ['https://secret.local/config.json'])
        self.assertEqual(result['report_items']['secret'][0]['secret_detection'], self.secret_detection)

    def test_txt_format_includes_redacted_secret_detection_summary(self):
        """Plain text item formatting should expose redacted secret evidence only."""

        actual = PluginProvider.format_report_item(self.data['report_items']['secret'][0])

        self.assertEqual(
            actual,
            'https://secret.local/config.json - 200 - 1KB | '
            'secret=aws_access_key, redacted=AKIA****CDEF, confidence=95%, count=1, types=aws_access_key'
        )
        self.assertNotIn(self.raw_secret, actual)

    def test_csv_report_exposes_queryable_secret_columns(self):
        """CSV report should flatten secret_detection into stable columns."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, self.target, self.target + '.csv')
        with open(report_file, 'r', newline='', encoding='utf-8') as handler:
            rows = list(csv.DictReader(handler))

        self.assertEqual(rows[0]['status'], 'secret')
        self.assertEqual(rows[0]['secret_detection'], 'aws_access_key')
        self.assertEqual(rows[0]['secret_redacted'], 'AKIA****CDEF')
        self.assertEqual(rows[0]['secret_confidence'], '95')
        self.assertEqual(rows[0]['secret_count'], '1')
        self.assertEqual(rows[0]['secret_types'], 'aws_access_key')
        self.assertNotIn(self.raw_secret, json.dumps(rows, sort_keys=True))

    def test_sqlite_report_exposes_queryable_secret_columns(self):
        """SQLite report should flatten secret_detection into queryable columns."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        database_path = os.path.join(self.base_dir, self.target, self.target + '.sqlite')
        connection = sqlite3.connect(database_path)
        row = connection.execute(
            'SELECT status, secret_detection, secret_redacted, secret_confidence, secret_count, secret_types FROM items'
        ).fetchone()
        connection.close()

        self.assertEqual(row, ('secret', 'aws_access_key', 'AKIA****CDEF', 95, 1, 'aws_access_key'))

    def test_json_report_preserves_nested_secret_detection_object(self):
        """JSON report should serialize the original nested secret_detection object."""

        with patch('src.lib.reporter.plugins.json.filesystem.clear'), \
                patch('src.lib.reporter.plugins.json.JsonReportPlugin.record') as record_mock:
            JsonReportPlugin(self.target, self.data, directory=self.base_dir).process()

        payload = json.loads(record_mock.call_args[0][2])
        self.assertEqual(payload['report_items']['secret'][0]['secret_detection'], self.secret_detection)
        self.assertNotIn(self.raw_secret, json.dumps(payload, sort_keys=True))

    def test_html_report_renders_nested_secret_detection_object(self):
        """HTML report should render nested redacted secret_detection details."""

        html = render_html_report(self.target, self.data)

        self.assertIn('secret_detection', html)
        self.assertIn('AKIA****CDEF', html)
        self.assertNotIn(self.raw_secret, html)

    def test_sarif_report_preserves_secret_metadata(self):
        """SARIF result should include secret metadata and secret-specific rule text."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir)
        result = plugin.result_for_item('secret', self.data['report_items']['secret'][0])

        self.assertEqual(result['ruleId'], 'opendoor.finding.secret')
        self.assertEqual(result['level'], 'warning')
        self.assertEqual(result['properties']['secretDetection'], self.secret_detection)
        self.assertIn('possible exposed secret', result['message']['text'])
        self.assertNotIn(self.raw_secret, json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    unittest.main()
