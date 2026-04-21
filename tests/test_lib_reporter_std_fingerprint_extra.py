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