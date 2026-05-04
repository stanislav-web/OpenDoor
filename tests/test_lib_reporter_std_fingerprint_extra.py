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
        self.assertIn('fingerprint_category', rendered)
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

        self.assertIn('fingerprint_signals', rendered)
        self.assertIn('fingerprint_runtime_signals', rendered)
        self.assertIn('fingerprint_infra_signals', rendered)

    def test_process_tolerates_malformed_total(self):
        """StdReportPlugin.process() should tolerate malformed total payloads."""

        plugin = StdReportPlugin('test.local', {'total': ['invalid']})

        with patch('src.lib.reporter.plugins.std.sys.writeln') as writeln_mock:
            plugin.process()

        rendered = writeln_mock.call_args[0][0]
        self.assertIn('Statistics (test.local)', rendered)

