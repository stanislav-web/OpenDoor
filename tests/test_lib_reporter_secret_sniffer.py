# -*- coding: utf-8 -*-

import json
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
from tests.reporting_helpers import fetch_sqlite_row, read_csv_report


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
        self.passive_finding = {
            'bucket': 'secret',
            'type': 'aws_access_key',
            'url': 'https://secret.local/config.json',
            'severity': 'high',
            'reason': 'secret_exposed',
            'confidence': 'high',
            'evidence': {
                'secret_type': 'aws_access_key',
                'redacted': 'AKIA****CDEF',
                'confidence_score': 95,
                'count': 1,
                'types': ['aws_access_key'],
                'matches': [
                    {
                        'type': 'aws_access_key',
                        'redacted': 'AKIA****CDEF',
                        'confidence_score': 95,
                        'position': 42,
                    }
                ],
            },
            'source': {
                'signal': 'response_body',
                'request_method': 'GET',
                'status': 200,
            },
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
                        'passive_finding': dict(self.passive_finding),
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
            'secret=aws_access_key, redacted=AKIA****CDEF, confidence=95%, count=1, types=aws_access_key | '
            'finding=aws_access_key, severity=high, reason=secret_exposed, confidence=high'
        )
        self.assertNotIn(self.raw_secret, actual)

    def test_csv_report_exposes_queryable_secret_columns(self):
        """CSV report should flatten secret_detection into stable columns."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        rows = read_csv_report(self.base_dir, self.target)

        self.assertEqual(rows[0]['status'], 'secret')
        self.assertEqual(rows[0]['secret_detection'], 'aws_access_key')
        self.assertEqual(rows[0]['secret_redacted'], 'AKIA****CDEF')
        self.assertEqual(rows[0]['secret_confidence'], '95')
        self.assertEqual(rows[0]['secret_count'], '1')
        self.assertEqual(rows[0]['secret_types'], 'aws_access_key')
        self.assertEqual(rows[0]['finding_type'], 'aws_access_key')
        self.assertEqual(rows[0]['finding_severity'], 'high')
        self.assertEqual(rows[0]['finding_reason'], 'secret_exposed')
        self.assertEqual(rows[0]['finding_confidence'], 'high')
        self.assertIn('\"secret_type\":\"aws_access_key\"', rows[0]['finding_evidence'])
        self.assertIn('\"redacted\":\"AKIA****CDEF\"', rows[0]['finding_evidence'])
        self.assertNotIn(self.raw_secret, json.dumps(rows, sort_keys=True))

    def test_sqlite_report_exposes_queryable_secret_columns(self):
        """SQLite report should flatten secret_detection into queryable columns."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        row = fetch_sqlite_row(
            self.base_dir,
            self.target,
            'SELECT status, secret_detection, secret_redacted, secret_confidence, secret_count, secret_types, '
            'finding_type, finding_severity, finding_reason, finding_confidence, finding_source, finding_evidence '
            'FROM items',
        )

        self.assertEqual(row[0:6], ('secret', 'aws_access_key', 'AKIA****CDEF', 95, 1, 'aws_access_key'))
        self.assertEqual(row[6:10], ('aws_access_key', 'high', 'secret_exposed', 'high'))
        self.assertIn('\"signal\":\"response_body\"', row[10])
        self.assertIn('\"secret_type\":\"aws_access_key\"', row[11])
        self.assertIn('\"redacted\":\"AKIA****CDEF\"', row[11])

    def test_json_report_preserves_nested_secret_detection_object(self):
        """JSON report should serialize the original nested secret_detection object."""

        with patch('src.lib.reporter.plugins.json.filesystem.clear'), \
                patch('src.lib.reporter.plugins.json.JsonReportPlugin.record') as record_mock:
            JsonReportPlugin(self.target, self.data, directory=self.base_dir).process()

        payload = json.loads(record_mock.call_args[0][2])
        self.assertEqual(payload['report_items']['secret'][0]['secret_detection'], self.secret_detection)
        self.assertEqual(payload['report_items']['secret'][0]['passive_finding'], self.passive_finding)
        self.assertNotIn(self.raw_secret, json.dumps(payload, sort_keys=True))

    def test_html_report_renders_nested_secret_detection_object(self):
        """HTML report should render nested redacted secret_detection details."""

        html = render_html_report(self.target, self.data)

        self.assertIn('secret_detection', html)
        self.assertIn('passive_finding', html)
        self.assertIn('secret_exposed', html)
        self.assertIn('AKIA****CDEF', html)
        self.assertNotIn(self.raw_secret, html)

    def test_sarif_report_preserves_secret_metadata(self):
        """SARIF result should include secret metadata and secret-specific rule text."""

        plugin = SarifReportPlugin(self.target, self.data, directory=self.base_dir)
        result = plugin.result_for_item('secret', self.data['report_items']['secret'][0])

        self.assertEqual(result['ruleId'], 'opendoor.finding.secret')
        self.assertEqual(result['level'], 'warning')
        self.assertEqual(result['properties']['secretDetection'], self.secret_detection)
        self.assertEqual(result['properties']['passiveFinding'], self.passive_finding)
        self.assertIn('possible exposed secret', result['message']['text'])
        self.assertNotIn(self.raw_secret, json.dumps(result, sort_keys=True))


    def test_browser_builds_secret_passive_finding_without_raw_values(self):
        """Browser metadata helper should add redacted passive finding data for secrets."""

        response = type('Response', (), {})()
        response.status = 200
        response.opendoor_secret_detection = dict(self.secret_detection)

        metadata = Browser._Browser__metadata_for_sniffer_bucket(
            'secret',
            response,
            url='https://secret.local/config.json',
            code='200',
            method='GET',
        )

        self.assertEqual(metadata['secret_detection'], self.secret_detection)
        passive_finding = metadata['passive_finding']
        self.assertEqual(passive_finding['bucket'], 'secret')
        self.assertEqual(passive_finding['type'], 'aws_access_key')
        self.assertEqual(passive_finding['severity'], 'high')
        self.assertEqual(passive_finding['reason'], 'secret_exposed')
        self.assertEqual(passive_finding['confidence'], 'high')
        self.assertEqual(passive_finding['source']['signal'], 'response_body')
        self.assertEqual(passive_finding['evidence']['redacted'], 'AKIA****CDEF')
        self.assertNotIn(self.raw_secret, json.dumps(passive_finding, sort_keys=True))

    def test_private_key_secret_passive_finding_is_critical(self):
        """Private key detections should be severity=critical in the shared contract."""

        response = type('Response', (), {})()
        response.status = 200
        response.opendoor_secret_detection = {
            'type': 'private_key',
            'redacted': '----****KEY-',
            'confidence': 98,
            'count': 1,
            'types': ['private_key'],
            'matches': [{'type': 'private_key', 'redacted': '----****KEY-', 'confidence': 98}],
        }

        metadata = Browser._Browser__metadata_for_sniffer_bucket(
            'secret',
            response,
            url='https://secret.local/key.txt',
            code='200',
            method='GET',
        )

        self.assertEqual(metadata['passive_finding']['severity'], 'critical')
        self.assertEqual(metadata['passive_finding']['evidence']['redacted'], '----****KEY-')

    def test_secret_passive_finding_confidence_medium_and_non_numeric_status(self):
        """Medium-confidence secret metadata should keep non-numeric statuses safely."""

        response = type('Response', (), {})()
        response.status = 'not-a-status'
        response.opendoor_secret_detection = {
            'type': 'generic_token',
            'redacted': 'tok_****1234',
            'confidence': 70,
            'count': 1,
            'types': ['generic_token'],
            'matches': [{'type': 'generic_token', 'redacted': 'tok_****1234', 'confidence': 70}],
        }

        metadata = Browser._Browser__metadata_for_sniffer_bucket(
            'secret',
            response,
            url='https://secret.local/token.txt',
            code='not-a-status',
            method='POST',
        )

        passive_finding = metadata['passive_finding']
        self.assertEqual(passive_finding['confidence'], 'medium')
        self.assertEqual(passive_finding['source']['status'], 'not-a-status')
        self.assertEqual(passive_finding['source']['request_method'], 'POST')
        self.assertEqual(passive_finding['evidence']['matches'][0]['confidence_score'], 70)

    def test_secret_passive_finding_confidence_low_and_skips_invalid_matches(self):
        """Low-confidence metadata should skip malformed match entries without failing."""

        response = type('Response', (), {})()
        response.status = 200
        response.opendoor_secret_detection = {
            'type': 'generic_token',
            'redacted': 'tok_****0000',
            'confidence': 30,
            'count': 2,
            'types': ['generic_token'],
            'matches': [
                'not-a-dict',
                {'type': 'generic_token', 'redacted': 'tok_****0000', 'confidence': 30, 'position': 9},
            ],
        }

        metadata = Browser._Browser__metadata_for_sniffer_bucket(
            'secret',
            response,
            url='https://secret.local/low.txt',
            code='200',
            method='GET',
        )

        passive_finding = metadata['passive_finding']
        self.assertEqual(passive_finding['confidence'], 'low')
        self.assertEqual(passive_finding['source']['status'], 200)
        self.assertEqual(len(passive_finding['evidence']['matches']), 1)
        self.assertEqual(passive_finding['evidence']['matches'][0]['position'], 9)

    def test_secret_passive_finding_ignores_invalid_inputs(self):
        """Secret passive metadata should be omitted when detection data or URL is invalid."""

        self.assertEqual(
            Browser._Browser__passive_secret_metadata(
                'https://secret.local/config.json',
                '200',
                'GET',
                None,
            ),
            {},
        )
        self.assertEqual(
            Browser._Browser__passive_secret_metadata(
                '',
                '200',
                'GET',
                dict(self.secret_detection),
            ),
            {},
        )


if __name__ == '__main__':
    unittest.main()
