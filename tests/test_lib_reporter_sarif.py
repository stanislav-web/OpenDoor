# -*- coding: utf-8 -*-

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from src.core import FileSystemError
from src.lib.reporter import Reporter
from src.lib.reporter.plugins.sarif import SarifReportPlugin


class TestSarifReportPlugin(unittest.TestCase):
    """SarifReportPlugin test cases."""

    def setUp(self):
        """Prepare report data with detailed findings, bypass evidence and fingerprint metadata."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'test.local'
        Reporter.external_directory = None
        self.data = {
            'items': {
                'success': ['https://example.com/admin'],
                'blocked': ['https://example.com/login'],
                'failed': ['https://example.com/missing'],
                'bypass': ['https://example.com/admin'],
            },
            'report_items': {
                'success': [{'url': 'https://example.com/admin', 'size': '9B', 'code': '200'}],
                'blocked': [
                    {
                        'url': 'https://example.com/login',
                        'size': '25B',
                        'code': '403',
                        'waf': 'Cloudflare',
                        'waf_confidence': 92,
                        'waf_signals': ['cf-ray', 'server-header'],
                    }
                ],
                'failed': [{'url': 'https://example.com/missing', 'size': '0B', 'code': '404'}],
                'bypass': [
                    {
                        'url': 'https://example.com/admin',
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
                'signals': [{'type': 'meta-generator', 'value': 'Open Journal Systems 3.2.1.2'}],
                'infrastructure': {'provider': 'Cloudflare', 'confidence': 90},
            },
            'total': {'success': 1, 'blocked': 1, 'failed': 1, 'bypass': 1},
        }

    def tearDown(self):
        """Reset reporter state and remove temporary report files."""

        Reporter.external_directory = None
        self.temp_dir.cleanup()

    def read_report(self):
        """
        Read the generated SARIF file.

        :return: SARIF payload
        :rtype: dict
        """

        report_file = os.path.join(self.base_dir, self.target, self.target + '.sarif')
        with open(report_file, 'r', encoding='utf-8') as handler:
            return json.load(handler)

    def test_reporter_load_returns_sarif_plugin(self):
        """Reporter.load() should resolve the SARIF report plugin."""

        Reporter.external_directory = self.base_dir + os.path.sep
        plugin = Reporter.load('sarif', self.target, self.data)

        self.assertIsInstance(plugin, SarifReportPlugin)

    def test_sarif_plugin_writes_github_friendly_sarif_21_payload(self):
        """SarifReportPlugin.process() should write a SARIF 2.1.0 log with rules and results."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        sarif = self.read_report()
        run = sarif['runs'][0]
        rules = run['tool']['driver']['rules']
        results = run['results']

        self.assertEqual(sarif['version'], '2.1.0')
        self.assertEqual(sarif['$schema'], 'https://json.schemastore.org/sarif-2.1.0.json')
        self.assertEqual(run['tool']['driver']['name'], 'OpenDoor')
        self.assertEqual(run['tool']['driver']['version'], '5.15.0')
        self.assertEqual(run['properties']['target'], self.target)
        self.assertEqual(len(results), 4)
        self.assertNotIn('https://example.com/missing', json.dumps(results))
        self.assertEqual(
            sorted([rule['id'] for rule in rules]),
            [
                'opendoor.finding.blocked',
                'opendoor.finding.bypass',
                'opendoor.finding.success',
                'opendoor.fingerprint.detected',
            ],
        )

    def test_sarif_result_preserves_url_status_size_waf_bypass_and_fingerprint_metadata(self):
        """SARIF results should preserve OpenDoor-specific report metadata in properties."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        results = plugin.build_sarif_log()['runs'][0]['results']

        blocked = next(result for result in results if result['ruleId'] == 'opendoor.finding.blocked')
        self.assertEqual(blocked['level'], 'warning')
        self.assertEqual(blocked['locations'][0]['physicalLocation']['artifactLocation']['uri'], 'https://example.com/login')
        self.assertEqual(blocked['properties']['statusCode'], 403)
        self.assertEqual(blocked['properties']['responseSize'], '25B')
        self.assertEqual(blocked['properties']['waf'], 'Cloudflare')
        self.assertEqual(blocked['properties']['wafConfidence'], 92)
        self.assertEqual(blocked['properties']['wafSignals'], ['cf-ray', 'server-header'])
        self.assertEqual(blocked['properties']['fingerprintName'], 'Open Journal Systems')
        self.assertEqual(blocked['properties']['infrastructureProvider'], 'Cloudflare')

        bypass = next(result for result in results if result['ruleId'] == 'opendoor.finding.bypass')
        self.assertEqual(bypass['properties']['bypass'], 'header')
        self.assertEqual(bypass['properties']['bypassHeader'], 'X-Original-URL')
        self.assertEqual(bypass['properties']['bypassValue'], '/admin')
        self.assertEqual(bypass['properties']['bypassFromCode'], 403)
        self.assertEqual(bypass['properties']['bypassToCode'], 200)
        self.assertIn('access bypass candidate', bypass['message']['text'])

    def test_sarif_plugin_adds_fingerprint_note_result_when_fingerprint_exists(self):
        """Target-level fingerprint metadata should be exposed as a note result."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        result = next(
            item for item in plugin.build_sarif_log()['runs'][0]['results']
            if item['ruleId'] == 'opendoor.fingerprint.detected'
        )

        self.assertEqual(result['level'], 'note')
        self.assertEqual(result['locations'][0]['physicalLocation']['artifactLocation']['uri'], self.target)
        self.assertEqual(result['properties']['fingerprintCategory'], 'cms')
        self.assertEqual(result['properties']['fingerprintConfidence'], 95)
        self.assertEqual(result['properties']['infrastructureConfidence'], 90)

    def test_sarif_plugin_falls_back_to_legacy_items(self):
        """SarifReportPlugin should support legacy URL-only report payloads."""

        data = {'items': {'indexof': ['https://example.com/public']}}
        plugin = SarifReportPlugin(self.target, data, directory=self.base_dir + os.path.sep)
        result = plugin.build_sarif_log()['runs'][0]['results'][0]

        self.assertEqual(result['ruleId'], 'opendoor.finding.indexof')
        self.assertEqual(result['level'], 'warning')
        self.assertEqual(result['properties']['url'], 'https://example.com/public')
        self.assertEqual(result['properties']['statusCodeRaw'], '-')
        self.assertNotIn('statusCode', result['properties'])

    def test_sarif_plugin_handles_unknown_statuses_and_non_dict_fingerprint_infrastructure(self):
        """Unknown buckets and malformed fingerprint infrastructure should still produce stable SARIF."""

        data = {
            'items': {'custom status!': ['https://example.com/custom']},
            'fingerprint': {
                'category': 'custom',
                'name': 'Custom Stack',
                'confidence': 'not-number',
                'infrastructure': 'Cloudflare',
            },
        }
        plugin = SarifReportPlugin(self.target, data, directory=self.base_dir + os.path.sep)
        sarif = plugin.build_sarif_log()
        result = sarif['runs'][0]['results'][0]
        fingerprint = sarif['runs'][0]['results'][1]

        self.assertEqual(result['ruleId'], 'opendoor.finding.custom_status')
        self.assertEqual(result['level'], 'note')
        self.assertEqual(sarif['runs'][0]['tool']['driver']['rules'][0]['properties']['security-severity'], '1.0')
        self.assertNotIn('infrastructureProvider', fingerprint['properties'])
        self.assertNotIn('fingerprintConfidence', fingerprint['properties'])

    def test_result_helpers_accept_raw_string_items_and_reuse_existing_rules(self):
        """Raw string report items and duplicate buckets should remain stable."""

        data = {
            'items': {'success': ['https://example.com/one', 'https://example.com/two']},
            'report_items': {'success': ['https://example.com/one', 'https://example.com/two']},
        }
        plugin = SarifReportPlugin(self.target, data, directory=self.base_dir + os.path.sep)
        sarif = plugin.build_sarif_log()

        self.assertEqual(len(sarif['runs'][0]['tool']['driver']['rules']), 1)
        self.assertEqual(len(sarif['runs'][0]['results']), 2)
        self.assertEqual(sarif['runs'][0]['results'][0]['properties']['statusCodeRaw'], '-')
        self.assertEqual(
            sarif['runs'][0]['results'][1]['locations'][0]['physicalLocation']['artifactLocation']['uri'],
            'https://example.com/two',
        )

    def test_private_item_helpers_accept_raw_string_items(self):
        """Low-level item helpers should normalize raw string values defensively."""

        plugin = SarifReportPlugin(self.target, {}, directory=self.base_dir + os.path.sep)

        properties = plugin.item_properties('success', 'https://example.com/raw')
        message = plugin.message_for_item('success', 'https://example.com/raw')

        self.assertEqual(properties['url'], 'https://example.com/raw')
        self.assertEqual(properties['statusCodeRaw'], '-')
        self.assertEqual(message, 'OpenDoor classified https://example.com/raw as success')

    def test_sarif_plugin_uses_default_reports_directory(self):
        """SarifReportPlugin.__init__() should use default reports directory when custom directory is absent."""

        with patch('src.lib.reporter.plugins.sarif.CoreConfig', {'data': {'reports': '/reports/'}}), \
                patch('src.lib.reporter.plugins.sarif.filesystem.makedir', return_value='/tmp/reports') as makedir_mock:
            SarifReportPlugin(self.target, self.data)

        makedir_mock.assert_called_once_with('/reports/' + self.target)

    def test_sarif_plugin_wraps_makedir_errors(self):
        """SarifReportPlugin.__init__() should wrap directory creation failures."""

        with patch('src.lib.reporter.plugins.sarif.filesystem.makedir', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                SarifReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)

    def test_sarif_plugin_wraps_processing_errors(self):
        """SarifReportPlugin.process() should wrap filesystem and JSON write failures."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)

        with patch('src.lib.reporter.plugins.sarif.filesystem.clear', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                plugin.process()

        with patch('src.lib.reporter.plugins.sarif.filesystem.makefile', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                plugin.process()

        with patch('src.lib.reporter.plugins.sarif.json.dump', side_effect=TypeError('boom')):
            with self.assertRaises(Exception):
                plugin.process()

    def test_sarif_plugin_logs_created_report(self):
        """SarifReportPlugin.process() should emit a report notification."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)

        with patch('src.lib.reporter.plugins.sarif.tpl.info') as info_mock:
            plugin.process()

        info_mock.assert_called_once()

    def test_rule_helpers_normalize_values(self):
        """SARIF helper methods should normalize rule ids, numbers and empty property values."""

        self.assertEqual(SarifReportPlugin.rule_id('Bad Status!'), 'opendoor.finding.bad_status')
        self.assertEqual(SarifReportPlugin.rule_id(None), 'opendoor.finding.unknown')
        self.assertEqual(SarifReportPlugin.rule_id('forbidden', item={'bypass': 'path'}), 'opendoor.finding.bypass')
        self.assertEqual(SarifReportPlugin.maybe_int('200'), 200)
        self.assertIsNone(SarifReportPlugin.maybe_int('abc'))
        self.assertEqual(
            SarifReportPlugin.clean_properties({'keep_false': False, 'keep_zero': 0, 'drop': None, 'drop_empty': ''}),
            {'keep_false': False, 'keep_zero': 0},
        )


if __name__ == '__main__':
    unittest.main()
