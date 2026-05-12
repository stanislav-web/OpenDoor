# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from src.lib.reporter.plugins.std import StdReportPlugin


class TestStdReportPluginFingerprintExtra(unittest.TestCase):
    """Extra StdReportPlugin coverage for fingerprint rows."""

    def test_process_renders_fingerprint_and_infrastructure_rows(self):
        """
        StdReportPlugin.process() should render fingerprint summary rows when present.

        :return: None
        """

        plugin = StdReportPlugin(
            'test.local',
            {
                'total': {'items': 10, 'success': 2, 'failed': 8, 'workers': 1},
                'fingerprint': {
                    'category': 'framework',
                    'name': 'Next.js',
                    'confidence': 96,
                    'infrastructure': {
                        'provider': 'AWS CloudFront',
                        'confidence': 98,
                    }
                }
            }
        )

        with patch('src.lib.reporter.plugins.std.sys.writeln') as writeln_mock:
            plugin.process()

        rendered = writeln_mock.call_args[0][0]
        self.assertNotIn('fingerprint_category', rendered)
        self.assertIn('Next.js', rendered)
        self.assertIn('fingerprint_infra', rendered)
        self.assertIn('AWS CloudFront', rendered)

    def test_process_renders_plain_statistics_without_fingerprint(self):
        """
        StdReportPlugin.process() should still work when fingerprint data is missing.

        :return: None
        """

        plugin = StdReportPlugin(
            'test.local',
            {
                'total': {'items': 10, 'success': 2, 'failed': 8, 'workers': 1},
            }
        )

        with patch('src.lib.reporter.plugins.std.sys.writeln') as writeln_mock:
            plugin.process()

        rendered = writeln_mock.call_args[0][0]
        self.assertIn('Statistics (test.local)', rendered)
        self.assertNotIn('fingerprint_category', rendered)

    def test_process_hides_noisy_stdout_summary_rows(self):
        """StdReportPlugin.process() should hide noisy rows only from stdout Summary."""

        plugin = StdReportPlugin(
            'test.local',
            {
                'total': {
                    'items': 10,
                    'workers': 1,
                    'calibrated': 8,
                    'ignored': 2,
                    'bad': 1,
                    'skip': 3,
                    'success': 2,
                },
                'fingerprint': {
                    'category': 'cms',
                    'name': 'Bitrix',
                    'confidence': 98,
                    'signals': [{'type': 'body', 'value': 'bitrix'}],
                    'runtime': {
                        'name': 'PHP',
                        'confidence': 98,
                        'signals': [{'type': 'header', 'value': 'x-powered-by'}],
                    },
                    'infrastructure': {
                        'provider': 'Nginx',
                        'confidence': 73,
                        'signals': [{'type': 'header', 'value': 'server'}],
                    },
                    'security_headers': {
                        'hsts': {
                            'grade': 'missing',
                            'max_age': None,
                            'include_subdomains': False,
                            'preload_ready': False,
                        },
                    },
                    'privacy_risks': {
                        'supercookie': {
                            'risk': 'low',
                            'score': 20,
                            'hsts_tracking_surface': False,
                            'etag_tracking_surface': False,
                            'cache_tracking_surface': False,
                            'persistent_cookie_surface': True,
                        },
                    },
                },
            },
        )

        with patch('src.lib.reporter.plugins.std.sys.writeln') as writeln_mock:
            plugin.process()

        rendered = writeln_mock.call_args[0][0]

        self.assertIn('workers', rendered)
        self.assertIn('fingerprint_name', rendered)
        self.assertIn('fingerprint_confidence', rendered)
        self.assertIn('fingerprint_runtime', rendered)
        self.assertIn('fingerprint_infra', rendered)
        self.assertIn('hsts', rendered)
        self.assertIn('privacy_supercookie_risk', rendered)

        for hidden_row in (
            'calibrated',
            'ignored',
            'bad',
            'skip',
            'fingerprint_category',
            'fingerprint_signals',
            'fingerprint_runtime_confidence',
            'fingerprint_runtime_signals',
            'fingerprint_infra_confidence',
            'fingerprint_infra_signals',
            'hsts_max_age',
            'hsts_include_subdomains',
            'hsts_preload_ready',
            'privacy_supercookie_score',
            'privacy_supercookie_hsts',
            'privacy_supercookie_etag',
            'privacy_supercookie_cache',
            'privacy_supercookie_cookie',
        ):
            self.assertNotIn(hidden_row, rendered)

    def test_format_summary_table_should_render_psql_like_output(self):
        """StdReportPlugin.format_summary_table() should render native table output."""

        rendered = StdReportPlugin.format_summary_table(
            [('success', 2), ('failed', 10)],
            ['Statistics (test.local)', 'Summary']
        )

        self.assertIn('+', rendered)
        self.assertIn('| Statistics (test.local) | Summary |', rendered)
        self.assertIn('| success                 | 2       |', rendered)
        self.assertIn('| failed                  | 10      |', rendered)

class TestStdReportPluginHardening(unittest.TestCase):
    """STD reporter hardening regression tests."""

    def test_process_tolerates_missing_total_and_renders_evidence_counts(self):
        """StdReportPlugin.process() should tolerate missing totals and show evidence counts."""

        plugin = StdReportPlugin(
            'test.local',
            {
                'fingerprint': {
                    'category': 'custom',
                    'name': 'Unknown custom stack',
                    'confidence': 45,
                    'signals': [{'type': 'route', 'value': '.php route marker'}],
                    'runtime': {
                        'name': 'PHP',
                        'confidence': 61,
                        'signals': [{'type': 'route', 'value': '.php route marker'}],
                    },
                    'infrastructure': {
                        'provider': 'Cloudflare',
                        'confidence': 80,
                        'signals': [{'type': 'header', 'value': 'cf-ray'}],
                    },
                },
            },
        )

        with patch('src.lib.reporter.plugins.std.sys.writeln') as writeln_mock:
            plugin.process()

        rendered = writeln_mock.call_args[0][0]

        self.assertIn('fingerprint_name', rendered)
        self.assertIn('fingerprint_runtime', rendered)
        self.assertIn('fingerprint_infra', rendered)
        self.assertNotIn('fingerprint_signals', rendered)
        self.assertNotIn('fingerprint_runtime_signals', rendered)
        self.assertNotIn('fingerprint_infra_signals', rendered)

    def test_process_tolerates_malformed_total(self):
        """StdReportPlugin.process() should tolerate malformed total payloads."""

        plugin = StdReportPlugin('test.local', {'total': ['invalid']})

        with patch('src.lib.reporter.plugins.std.sys.writeln') as writeln_mock:
            plugin.process()

        rendered = writeln_mock.call_args[0][0]
        self.assertIn('Statistics (test.local)', rendered)

