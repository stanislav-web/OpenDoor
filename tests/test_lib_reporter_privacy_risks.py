# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch

from src.lib.reporter.plugins.csv import CsvReportPlugin
from src.lib.reporter.plugins.html import HtmlReportPlugin, render_html_report
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.sarif import SarifReportPlugin
from src.lib.reporter.plugins.sqlite import SqliteReportPlugin
from src.lib.reporter.plugins.std import StdReportPlugin
from src.lib.reporter.plugins.txt import TextReportPlugin
from tests.reporting_helpers import fetch_sqlite_row, read_csv_report, read_json_report, report_file_path


class TestReporterPrivacyRisks(unittest.TestCase):
    """Reporter coverage for fingerprint privacy-risk metadata."""

    def setUp(self):
        """Prepare shared report payload."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'test.local'
        self.data = {
            'items': {
                'success': ['https://example.com/admin'],
            },
            'report_items': {
                'success': [
                    {
                        'url': 'https://example.com/admin',
                        'code': '200',
                        'size': '12B',
                    }
                ],
            },
            'total': {
                'items': 1,
                'success': 1,
            },
            'fingerprint': {
                'category': 'custom',
                'name': 'Unknown custom stack',
                'confidence': 45,
                'privacy_risks': {
                    'supercookie': {
                        'risk': 'medium',
                        'score': 45,
                        'signals': ['persistent_etag:"abc123"'],
                        'warnings': ['persistent ETag/cache validator with long cache lifetime'],
                        'hsts_tracking_surface': False,
                        'etag_tracking_surface': True,
                        'cache_tracking_surface': True,
                        'persistent_cookie_surface': False,
                    }
                },
            },
        }

    def tearDown(self):
        """Remove temporary report files."""

        self.temp_dir.cleanup()

    def test_std_report_renders_privacy_risk_rows(self):
        """STD reporter should show target-level privacy-risk counters."""

        plugin = StdReportPlugin(self.target, self.data)

        with patch('src.lib.reporter.plugins.std.sys.writeln') as writeln_mock:
            plugin.process()

        rendered = writeln_mock.call_args[0][0]

        self.assertIn('supercookie_risk', rendered)
        self.assertIn('medium', rendered)
        self.assertNotIn('supercookie_score', rendered)
        self.assertNotIn('privacy_supercookie_etag', rendered)

    def test_text_report_writes_privacy_risk_summary(self):
        """TXT reporter should persist privacy-risk metadata in fingerprint.txt."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value=self.base_dir), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear'):
            plugin = TextReportPlugin(self.target, self.data, directory=self.base_dir)
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        fingerprint_call = next(call for call in record_mock.call_args_list if call.args[1] == 'fingerprint')
        rows = fingerprint_call.args[2]

        self.assertIn('supercookie_risk: medium', rows)
        self.assertIn('supercookie_score: 45', rows)
        self.assertTrue(any(row.startswith('privacy_supercookie_warnings:') for row in rows))

    def test_csv_report_writes_privacy_risk_columns(self):
        """CSV reporter should expose privacy-risk columns on each item row."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        rows = read_csv_report(self.base_dir, self.target)

        self.assertEqual(rows[0]['supercookie_risk'], 'medium')
        self.assertEqual(rows[0]['supercookie_score'], '45')
        self.assertEqual(rows[0]['supercookie_etag_tracking_surface'], 'True')
        self.assertEqual(
            rows[0]['privacy_supercookie_warnings'],
            'persistent ETag/cache validator with long cache lifetime',
        )

    def test_json_report_preserves_privacy_risk_payload(self):
        """JSON reporter should preserve the full fingerprint privacy-risk object."""

        plugin = JsonReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        payload = read_json_report(self.base_dir, self.target)

        self.assertEqual(payload['fingerprint']['privacy_risks']['supercookie']['risk'], 'medium')
        self.assertTrue(payload['fingerprint']['privacy_risks']['supercookie']['etag_tracking_surface'])

    def test_html_report_renders_privacy_risk_metadata(self):
        """HTML reporter should include privacy-risk metadata in the metadata section."""

        html = render_html_report(
            self.target,
            {
                **self.data,
                'report_items': self.data['report_items'],
            },
        )

        self.assertIn('privacy_risks', html)
        self.assertIn('supercookie', html)
        self.assertIn('persistent ETag/cache validator with long cache lifetime', html)

        plugin = HtmlReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()
        report_file = report_file_path(self.base_dir, self.target, 'html')
        self.assertTrue(os.path.isfile(report_file))

    def test_sqlite_report_writes_privacy_risk_columns(self):
        """SQLite reporter should persist privacy-risk columns in fingerprint table."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        row = fetch_sqlite_row(
            self.base_dir,
            self.target,
            'SELECT supercookie_risk, supercookie_score, '
            'supercookie_etag_tracking_surface, privacy_supercookie_warnings, '
            'supercookie_signals FROM fingerprint',
        )

        self.assertEqual(
            row,
            (
                'medium',
                45,
                1,
                'persistent ETag/cache validator with long cache lifetime',
                'persistent_etag:"abc123"',
            ),
        )

    def test_sarif_report_writes_privacy_risk_properties(self):
        """SARIF reporter should expose privacy-risk properties for CI integrations."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        result = next(
            item for item in plugin.build_sarif_log()['runs'][0]['results']
            if item['ruleId'] == 'opendoor.fingerprint.detected'
        )

        self.assertEqual(result['properties']['privacySupercookieRisk'], 'medium')
        self.assertEqual(result['properties']['privacySupercookieScore'], 45)
        self.assertTrue(result['properties']['privacySupercookieEtagTrackingSurface'])
        self.assertEqual(
            result['properties']['privacySupercookieWarnings'],
            ['persistent ETag/cache validator with long cache lifetime'],
        )


if __name__ == '__main__':
    unittest.main()
