# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch

from src.core import FileSystemError
from src.lib.reporter import Reporter
from src.lib.reporter.plugins.csv import CsvReportPlugin
from tests.reporting_helpers import read_csv_report, report_file_path


class TestCsvReportPlugin(unittest.TestCase):
    """CsvReportPlugin test cases."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'test.local'
        Reporter.external_directory = None
        self.data = {
            'items': {
                'success': ['http://example.com/admin'],
                'blocked': ['http://example.com/login'],
                'failed': ['http://example.com/missing'],
                'bypass': ['http://example.com/admin'],
            },
            'report_items': {
                'success': [
                    {
                        'url': 'http://example.com/admin?role=admin,owner',
                        'size': '9B',
                        'code': '200',
                    }
                ],
                'blocked': [
                    {
                        'url': 'http://example.com/login',
                        'size': '25B',
                        'code': '403',
                        'waf': 'Cloudflare',
                        'waf_confidence': 92,
                        'waf_signals': ['cf-ray', 'server-header'],
                    }
                ],
                'failed': [
                    {
                        'url': 'http://example.com/missing',
                        'size': '0B',
                        'code': '404',
                    }
                ],
                'bypass': [
                    {
                        'url': 'http://example.com/admin',
                        'size': '90B',
                        'code': '200',
                        'bypass': 'header',
                        'bypass_header': 'X-Original-URL',
                        'bypass_value': '/admin',
                        'bypass_from_code': '403',
                        'bypass_to_code': '200',
                    }
                ],
            },
            'fingerprint': {
                'category': 'cms',
                'name': 'Open Journal Systems',
                'confidence': 95,
                'runtime': {'name': 'PHP', 'category': 'runtime', 'confidence': 88, 'signals': [{'type': 'technology', 'value': 'Open Journal Systems'}]},
                'infrastructure': {
                    'provider': 'Cloudflare',
                    'confidence': 90,
                },
                'security_headers': {
                    'hsts': {
                        'present': True,
                        'grade': 'strong',
                        'max_age': 31536000,
                        'include_subdomains': True,
                        'preload': False,
                        'preload_ready': False,
                        'http_to_https_redirect': True,
                        'warnings': [],
                    }
                },
            },
            'total': {
                'success': 1,
                'blocked': 1,
                'failed': 1,
                'items': 3,
                'workers': 1,
                'bypass': 1,
            },
        }

    def tearDown(self):
        Reporter.external_directory = None
        self.temp_dir.cleanup()

    def read_report_rows(self):
        """
        Read generated CSV rows as dictionaries.

        :return: list
        """

        return read_csv_report(self.base_dir, self.target)

    def test_reporter_load_returns_csv_plugin(self):
        """Reporter.load() should resolve the csv report plugin."""

        Reporter.external_directory = self.base_dir + os.path.sep
        plugin = Reporter.load('csv', self.target, self.data)

        self.assertIsInstance(plugin, CsvReportPlugin)

    def test_csv_plugin_writes_header_and_item_rows(self):
        """CsvReportPlugin.process() should write stable columns and non-failed item rows."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        rows = self.read_report_rows()

        self.assertEqual(len(rows), 3)
        self.assertEqual(list(rows[0].keys()), CsvReportPlugin.COLUMNS)
        self.assertEqual(rows[0]['target'], self.target)
        self.assertEqual(rows[0]['status'], 'success')
        self.assertEqual(rows[0]['url'], 'http://example.com/admin?role=admin,owner')
        self.assertEqual(rows[0]['code'], '200')
        self.assertEqual(rows[0]['size'], '9B')
        self.assertEqual(rows[0]['fingerprint_name'], 'Open Journal Systems')
        self.assertEqual(rows[0]['infrastructure_provider'], 'Cloudflare')
        self.assertEqual(rows[0]['hsts_grade'], 'strong')
        self.assertEqual(rows[0]['hsts_max_age'], '31536000')
        self.assertEqual(rows[1]['status'], 'blocked')
        self.assertEqual(rows[1]['waf'], 'Cloudflare')
        self.assertEqual(rows[1]['waf_confidence'], '92')
        self.assertEqual(rows[1]['waf_signals'], 'cf-ray;server-header')
        self.assertEqual(rows[2]['status'], 'bypass')
        self.assertEqual(rows[2]['bypass'], 'header')
        self.assertEqual(rows[2]['bypass_header'], 'X-Original-URL')
        self.assertEqual(rows[2]['bypass_value'], '/admin')
        self.assertEqual(rows[2]['bypass_from_code'], '403')
        self.assertEqual(rows[2]['bypass_to_code'], '200')

    def test_csv_plugin_falls_back_to_legacy_items(self):
        """CsvReportPlugin.process() should support legacy URL-only report payloads."""

        legacy_data = {
            'items': {
                'success': ['http://example.com/legacy'],
            },
        }

        plugin = CsvReportPlugin(self.target, legacy_data, directory=self.base_dir + os.path.sep)
        plugin.process()

        rows = self.read_report_rows()

        self.assertEqual(rows[0]['status'], 'success')
        self.assertEqual(rows[0]['url'], 'http://example.com/legacy')
        self.assertEqual(rows[0]['code'], '-')
        self.assertEqual(rows[0]['size'], '0B')
        self.assertEqual(rows[0]['fingerprint_name'], '')

    def test_csv_plugin_writes_header_when_no_items_exist(self):
        """CsvReportPlugin.process() should still create a valid empty CSV with columns."""

        plugin = CsvReportPlugin(self.target, {'items': {}}, directory=self.base_dir + os.path.sep)
        plugin.process()

        with open(report_file_path(self.base_dir, self.target, 'csv'), encoding='utf-8') as handler:
            content = handler.read()

        self.assertIn(
            'target,status,url,code,size,waf,waf_confidence,waf_signals,'
            'bypass,bypass_profile,bypass_header,bypass_value,bypass_variant,bypass_url,'
            'bypass_from_status,bypass_to_status,bypass_from_code,bypass_to_code,'
            'bypass_score,bypass_reasons',
            content
        )

    def test_csv_plugin_uses_default_reports_directory(self):
        """CsvReportPlugin.__init__() should use default reports directory when custom directory is absent."""

        with patch('src.lib.reporter.plugins.csv.CoreConfig', {'data': {'reports': '/reports/'}}), \
                patch('src.lib.reporter.plugins.csv.filesystem.makedir', return_value='/tmp/reports') as makedir_mock:
            CsvReportPlugin(self.target, self.data)

        makedir_mock.assert_called_once_with('/reports/' + self.target)

    def test_csv_plugin_wraps_makedir_errors(self):
        """CsvReportPlugin.__init__() should wrap directory creation failures."""

        with patch('src.lib.reporter.plugins.csv.filesystem.makedir', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)

    def test_csv_plugin_wraps_clear_errors(self):
        """CsvReportPlugin.process() should wrap filesystem clear failures."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)

        with patch('src.lib.reporter.plugins.csv.filesystem.clear', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                plugin.process()

    def test_csv_plugin_logs_created_report(self):
        """CsvReportPlugin.process() should emit a report notification."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)

        with patch('src.lib.reporter.plugins.csv.tpl.info') as info_mock:
            plugin.process()

        info_mock.assert_called_once()

    def test_csv_format_list_handles_none_and_scalar_values(self):
        """CsvReportPlugin.__format_list() should normalize None and scalar values."""

        self.assertEqual(CsvReportPlugin._CsvReportPlugin__format_list(None), '')
        self.assertEqual(CsvReportPlugin._CsvReportPlugin__format_list('single-signal'), 'single-signal')
        self.assertEqual(CsvReportPlugin._CsvReportPlugin__format_list(123), '123')

    def test_csv_plugin_handles_non_dict_fingerprint_infrastructure(self):
        """CsvReportPlugin.process() should fallback to empty infrastructure fields for non-dict data."""

        data = {
            'items': {
                'success': ['http://example.com/ojs'],
            },
            'report_items': {
                'success': [
                    {
                        'url': 'http://example.com/ojs',
                        'size': '12B',
                        'code': '200',
                    }
                ],
            },
            'fingerprint': {
                'category': 'cms',
                'name': 'Open Journal Systems',
                'confidence': 95,
                'runtime': {'name': 'PHP', 'category': 'runtime', 'confidence': 88, 'signals': [{'type': 'technology', 'value': 'Open Journal Systems'}]},
                'infrastructure': 'Cloudflare',
            },
        }

        plugin = CsvReportPlugin(self.target, data, directory=self.base_dir + os.path.sep)
        plugin.process()

        rows = self.read_report_rows()

        self.assertEqual(rows[0]['fingerprint_category'], 'cms')
        self.assertEqual(rows[0]['fingerprint_name'], 'Open Journal Systems')
        self.assertEqual(rows[0]['fingerprint_confidence'], '95')
        self.assertEqual(rows[0]['infrastructure_provider'], '')
        self.assertEqual(rows[0]['infrastructure_confidence'], '')

    def test_csv_plugin_supports_non_dict_report_items(self):
        """CsvReportPlugin.process() should support legacy non-dict detailed report items."""

        data = {
            'items': {
                'success': ['http://example.com/legacy'],
            },
            'report_items': {
                'success': ['http://example.com/legacy'],
            },
        }

        plugin = CsvReportPlugin(self.target, data, directory=self.base_dir + os.path.sep)
        plugin.process()

        rows = self.read_report_rows()

        self.assertEqual(rows[0]['target'], self.target)
        self.assertEqual(rows[0]['status'], 'success')
        self.assertEqual(rows[0]['url'], 'http://example.com/legacy')
        self.assertEqual(rows[0]['code'], '-')
        self.assertEqual(rows[0]['size'], '0B')

    def test_csv_plugin_wraps_open_errors(self):
        """CsvReportPlugin.process() should wrap file write failures."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)

        with patch('builtins.open', side_effect=OSError('boom')):
            with self.assertRaises(Exception):
                plugin.process()


if __name__ == '__main__':
    unittest.main()


class TestCsvReportRedirectClassification(unittest.TestCase):
    """CSV redirect classification report tests."""

    def test_csv_plugin_preserves_redirect_classification_columns(self):
        """CSV rows should expose redirect classification as nullable columns."""

        with tempfile.TemporaryDirectory() as temp_dir:
            data = {
                'items': {'redirect': ['https://example.com/login']},
                'report_items': {
                    'redirect': [{
                        'url': 'https://example.com/login',
                        'code': '302',
                        'size': '0B',
                        'redirect_classification': {
                            'type': 'login',
                            'reason': 'auth_gate_redirect',
                            'location': '/login?next=/admin',
                            'target_host': 'example.com',
                            'same_origin': True,
                            'cross_origin': False,
                            'confidence': 'high',
                        },
                    }]
                },
                'total': {'redirect': 1},
            }
            plugin = CsvReportPlugin('example.com', data, directory=temp_dir + os.path.sep)
            plugin.process()

            rows = read_csv_report(temp_dir, 'example.com')

        self.assertEqual(rows[0]['redirect_type'], 'login')
        self.assertEqual(rows[0]['redirect_reason'], 'auth_gate_redirect')
        self.assertEqual(rows[0]['redirect_location'], '/login?next=/admin')
        self.assertEqual(rows[0]['redirect_target_host'], 'example.com')
        self.assertEqual(rows[0]['redirect_same_origin'], 'True')
        self.assertEqual(rows[0]['redirect_cross_origin'], 'False')
        self.assertEqual(rows[0]['redirect_confidence'], 'high')
