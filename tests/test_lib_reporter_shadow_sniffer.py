# -*- coding: utf-8 -*-

import csv
import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from src.lib.reporter.plugins.csv import CsvReportPlugin
from src.lib.reporter.plugins.html import render_html_report
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.provider.provider import PluginProvider
from src.lib.reporter.plugins.sarif import SarifReportPlugin
from src.lib.reporter.plugins.sqlite import SqliteReportPlugin


class TestShadowSnifferReportMetadata(unittest.TestCase):
    """Report metadata tests for active Shadow Copy findings."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'shadow.local'
        self.shadow_detection = {
            'type': 'backup_copy',
            'confidence': 95,
            'reason': 'content_match',
            'base_url': 'https://shadow.local/index.php',
            'url': 'https://shadow.local/index.php.bak',
            'variant': '.bak',
            'variant_type': 'suffix',
            'similarity': 1.0,
            'base_size': 21,
            'shadow_size': 21,
            'content_type': 'text/html',
        }
        self.data = {
            'items': {
                'shadow': ['https://shadow.local/index.php.bak'],
            },
            'report_items': {
                'shadow': [
                    {
                        'url': 'https://shadow.local/index.php.bak',
                        'code': '200',
                        'size': '21B',
                        'shadow_detection': dict(self.shadow_detection),
                    }
                ],
            },
            'total': {'shadow': 1, 'shadow_probes': 12},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_txt_format_includes_shadow_detection_summary(self):
        """Plain text item formatting should expose compact shadow evidence."""

        actual = PluginProvider.format_report_item(self.data['report_items']['shadow'][0])

        self.assertEqual(
            actual,
            'https://shadow.local/index.php.bak - 200 - 21B | '
            'shadow=backup_copy, variant=.bak, base=https://shadow.local/index.php, '
            'confidence=95%, similarity=1.0'
        )

    def test_csv_report_exposes_queryable_shadow_columns(self):
        """CSV report should flatten shadow_detection into stable columns."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, self.target, self.target + '.csv')
        with open(report_file, 'r', newline='', encoding='utf-8') as handler:
            rows = list(csv.DictReader(handler))

        self.assertEqual(rows[0]['status'], 'shadow')
        self.assertEqual(rows[0]['shadow_detection'], 'backup_copy')
        self.assertEqual(rows[0]['shadow_confidence'], '95')
        self.assertEqual(rows[0]['shadow_reason'], 'content_match')
        self.assertEqual(rows[0]['shadow_base_url'], 'https://shadow.local/index.php')
        self.assertEqual(rows[0]['shadow_variant'], '.bak')
        self.assertEqual(rows[0]['shadow_similarity'], '1.0')
        self.assertEqual(rows[0]['shadow_base_size'], '21')
        self.assertEqual(rows[0]['shadow_size'], '21')

    def test_sqlite_report_exposes_queryable_shadow_columns(self):
        """SQLite report should flatten shadow_detection into queryable columns."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        database_path = os.path.join(self.base_dir, self.target, self.target + '.sqlite')
        connection = sqlite3.connect(database_path)
        row = connection.execute(
            'SELECT status, shadow_detection, shadow_confidence, shadow_reason, '
            'shadow_base_url, shadow_variant, shadow_similarity, shadow_base_size, shadow_size FROM items'
        ).fetchone()
        summary = dict(connection.execute('SELECT status, total FROM summary').fetchall())
        connection.close()

        self.assertEqual(
            row,
            (
                'shadow',
                'backup_copy',
                95,
                'content_match',
                'https://shadow.local/index.php',
                '.bak',
                1.0,
                21,
                21,
            )
        )
        self.assertEqual(summary['shadow_probes'], 12)

    def test_json_report_preserves_nested_shadow_detection_object(self):
        """JSON report should serialize the nested shadow_detection object."""

        with patch('src.lib.reporter.plugins.json.filesystem.clear'), \
                patch('src.lib.reporter.plugins.json.JsonReportPlugin.record') as record_mock:
            JsonReportPlugin(self.target, self.data, directory=self.base_dir).process()

        payload = json.loads(record_mock.call_args[0][2])
        self.assertEqual(payload['report_items']['shadow'][0]['shadow_detection'], self.shadow_detection)

    def test_html_report_renders_nested_shadow_detection_object(self):
        """HTML report should render shadow_detection details."""

        html = render_html_report(self.target, self.data)

        self.assertIn('shadow_detection', html)
        self.assertIn('backup_copy', html)
        self.assertIn('.bak', html)
        self.assertIn('https://shadow.local/index.php', html)

    def test_sarif_report_preserves_shadow_metadata(self):
        """SARIF result should include shadow metadata and shadow-specific rule text."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir)
        result = plugin.result_for_item('shadow', self.data['report_items']['shadow'][0])

        self.assertEqual(result['ruleId'], 'opendoor.finding.shadow')
        self.assertEqual(result['level'], 'warning')
        self.assertEqual(result['properties']['shadowDetection'], self.shadow_detection)
        self.assertIn('exposed shadow copy', result['message']['text'])


if __name__ == '__main__':
    unittest.main()
