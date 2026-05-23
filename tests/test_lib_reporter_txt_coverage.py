# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from src.core.filesystem.exceptions import FileSystemError
from src.lib.reporter.plugins.txt import TextReportPlugin


class TestTextReportPluginCoverage(unittest.TestCase):
    """Regression coverage for the plain text report plugin."""

    def setUp(self):
        """Prepare common report input."""

        self.target = 'test.local'
        self.target_dir = '/tmp/reports'

    def test_should_use_default_reports_directory_when_directory_is_missing(self):
        """TextReportPlugin should resolve the default reports directory from CoreConfig."""

        with patch('src.lib.reporter.plugins.txt.CoreConfig', {'data': {'reports': '/reports'}}), \
                patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value=self.target_dir) as makedir_mock:
            TextReportPlugin(self.target, {'items': {}}, directory=None)

        makedir_mock.assert_called_once_with('/reports/' + self.target)

    def test_should_wrap_directory_creation_errors(self):
        """TextReportPlugin should wrap filesystem errors raised during directory creation."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                TextReportPlugin(self.target, {'items': {}}, directory='/custom')

    def test_should_process_non_failed_buckets_with_detailed_report_items(self):
        """TextReportPlugin.process() should write every non-failed status bucket."""

        data = {
            'items': {
                'success': ['http://example.com/admin'],
                'failed': ['http://example.com/missing'],
                'indexof': ['http://example.com/public'],
            },
            'report_items': {
                'success': [
                    {
                        'url': 'http://example.com/admin',
                        'code': '200',
                        'size': '12B',
                    }
                ],
                'failed': [
                    {
                        'url': 'http://example.com/missing',
                        'code': '404',
                        'size': '0B',
                    }
                ],
                'indexof': [
                    {
                        'url': 'http://example.com/public',
                        'code': '200',
                        'size': '1KB',
                    }
                ],
            },
        }

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value=self.target_dir), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear') as clear_mock:
            plugin = TextReportPlugin(self.target, data, directory='/custom/reports')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        clear_mock.assert_called_once_with(self.target_dir, extension='.txt')
        self.assertEqual(record_mock.call_count, 2)
        record_mock.assert_any_call(
            self.target_dir,
            'success',
            ['http://example.com/admin - 200 - 12B'],
            '\n'
        )
        record_mock.assert_any_call(
            self.target_dir,
            'indexof',
            ['http://example.com/public - 200 - 1KB'],
            '\n'
        )

    def test_should_process_legacy_url_items_when_report_items_are_missing(self):
        """TextReportPlugin.process() should keep legacy URL-only buckets supported."""

        data = {
            'items': {
                'success': ['http://example.com/legacy'],
            }
        }

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value=self.target_dir), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear'):
            plugin = TextReportPlugin(self.target, data, directory='/custom/reports')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        record_mock.assert_called_once_with(
            self.target_dir,
            'success',
            ['http://example.com/legacy - - - 0B'],
            '\n'
        )

    def test_should_process_empty_items_without_writing_report_files(self):
        """TextReportPlugin.process() should clear stale txt reports even when no items exist."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value=self.target_dir), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear') as clear_mock:
            plugin = TextReportPlugin(self.target, {'items': {}}, directory='/custom/reports')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        clear_mock.assert_called_once_with(self.target_dir, extension='.txt')
        record_mock.assert_not_called()

    def test_should_wrap_filesystem_clear_errors(self):
        """TextReportPlugin.process() should wrap clear failures."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value=self.target_dir), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear', side_effect=FileSystemError('boom')):
            plugin = TextReportPlugin(self.target, {'items': {'success': ['http://example.com']}}, directory='/custom')

            with self.assertRaises(Exception):
                plugin.process()

    def test_should_wrap_record_errors_after_formatting_items(self):
        """TextReportPlugin.process() should wrap record failures after building txt payload."""

        data = {
            'items': {
                'success': ['http://example.com/admin'],
            },
            'report_items': {
                'success': [
                    {
                        'url': 'http://example.com/admin',
                        'code': '200',
                        'size': '12B',
                    }
                ],
            },
        }

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value=self.target_dir), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear'):
            plugin = TextReportPlugin(self.target, data, directory='/custom')
            with patch.object(plugin, 'record', side_effect=Exception('boom')):
                with self.assertRaises(Exception):
                    plugin.process()

    def test_should_format_plain_string_report_item(self):
        """Text report formatter should preserve non-dict legacy items."""

        self.assertEqual(
            TextReportPlugin.format_report_item('http://example.com/plain'),
            'http://example.com/plain'
        )

    def test_should_format_full_waf_and_bypass_report_metadata(self):
        """Text report formatter should include WAF and bypass metadata in one line."""

        actual = TextReportPlugin.format_report_item({
            'url': 'http://example.com/admin',
            'code': '200',
            'size': '90B',
            'waf': 'Cloudflare',
            'waf_confidence': 95,
            'bypass': 'header',
            'bypass_header': 'X-Original-URL',
            'bypass_value': '/admin',
            'bypass_from_code': '403',
            'bypass_to_code': '200',
        })

        self.assertEqual(
            actual,
            'http://example.com/admin - 200 - 90B - WAF: Cloudflare (95%) | '
            'bypass=header, header=X-Original-URL, value=/admin, 403->200'
        )

    def test_should_render_fingerprint_evidence_signals(self):
        """Text fingerprint report should expose compact evidence for QA/debugging."""

        plugin = TextReportPlugin.__new__(TextReportPlugin)
        plugin._data = {
            'fingerprint': {
                'category': 'custom',
                'name': 'Unknown custom stack',
                'confidence': 45,
                'signals': [
                    {'type': 'route', 'value': '.php route marker', 'weight': 4.5},
                ],
                'runtime': {
                    'name': 'PHP',
                    'confidence': 61,
                    'signals': [
                        {'type': 'cookie', 'value': 'PHPSESSID', 'weight': 7},
                    ],
                },
                'infrastructure': {
                    'provider': 'Cloudflare',
                    'confidence': 80,
                    'signals': [
                        {'type': 'header', 'value': 'cf-ray', 'weight': 7},
                    ],
                },
                'security_headers': {
                    'hsts': {
                        'grade': 'weak',
                        'max_age': 300,
                        'include_subdomains': False,
                        'preload_ready': False,
                        'warnings': ['max-age below preload requirement'],
                    },
                },
            },
        }

        rows = plugin.format_fingerprint_summary()

        self.assertIn('signals: route:.php route marker(4.5)', rows)
        self.assertIn('runtime_signals: cookie:PHPSESSID(7)', rows)
        self.assertIn('infrastructure_signals: header:cf-ray(7)', rows)
        self.assertIn('hsts_warnings: max-age below preload requirement', rows)


    def test_should_format_signal_without_weight(self):
        """Fingerprint signal formatter should omit weight suffix when no score exists."""

        plugin = TextReportPlugin.__new__(TextReportPlugin)
        plugin._data = {
            'fingerprint': {
                'category': 'custom',
                'name': 'Unknown',
                'confidence': 10,
                'signals': [
                    {'type': 'header', 'value': 'server=nginx'},
                ],
            },
        }

        rows = plugin.format_fingerprint_summary()

        self.assertIn('signals: header:server=nginx', rows)

    def test_should_format_scalar_signal_list_value(self):
        """Fingerprint signal formatter should preserve scalar values."""

        plugin = TextReportPlugin.__new__(TextReportPlugin)
        plugin._data = {
            'fingerprint': {
                'category': 'custom',
                'name': 'Unknown',
                'confidence': 10,
                'signals': 'server=nginx',
            },
        }

        rows = plugin.format_fingerprint_summary()

        self.assertIn('signals: server=nginx', rows)

    def test_should_process_non_dict_items_as_empty(self):
        """TextReportPlugin.process() should ignore malformed non-dict items payload."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value=self.target_dir), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear') as clear_mock:
            plugin = TextReportPlugin(self.target, {'items': ['bad']}, directory='/custom/reports')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        clear_mock.assert_called_once_with(self.target_dir, extension='.txt')
        record_mock.assert_not_called()

    def test_should_format_supercookie_warning_and_signal_lists(self):
        """Text fingerprint summary should include optional supercookie warning and signal lists."""

        plugin = TextReportPlugin.__new__(TextReportPlugin)
        plugin._data = {
            'fingerprint': {
                'category': 'custom',
                'name': 'Unknown custom stack',
                'confidence': 35,
                'privacy_risks': {
                    'supercookie': {
                        'risk': 'medium',
                        'score': 45,
                        'warnings': ['persistent ETag/cache validator'],
                        'signals': ['persistent_etag:"abc"'],
                    }
                },
            }
        }

        rows = plugin.format_fingerprint_summary()

        self.assertIn('privacy_supercookie_warnings: persistent ETag/cache validator', rows)
        self.assertIn('supercookie_signals: persistent_etag:"abc"', rows)

    def test_should_format_supercookie_rows_without_optional_warning_lists(self):
        """Text fingerprint summary should handle supercookie metadata without optional lists."""

        plugin = TextReportPlugin.__new__(TextReportPlugin)
        plugin._data = {
            'fingerprint': {
                'category': 'custom',
                'name': 'Unknown custom stack',
                'confidence': 35,
                'privacy_risks': {
                    'supercookie': {
                        'risk': 'none',
                        'score': 0,
                        'hsts_tracking_surface': False,
                        'etag_tracking_surface': False,
                        'cache_tracking_surface': False,
                        'persistent_cookie_surface': False,
                        'warnings': [],
                        'signals': [],
                    }
                },
            }
        }

        rows = plugin.format_fingerprint_summary()

        self.assertIn('supercookie_risk: none', rows)
        self.assertIn('supercookie_score: 0', rows)
        self.assertNotIn('privacy_supercookie_warnings: ', rows)
        self.assertNotIn('supercookie_signals: ', rows)

if __name__ == '__main__':
    unittest.main()
