# -*- coding: utf-8 -*-

import tempfile
import unittest

from src.lib.reporter.plugins.csv import CsvReportPlugin
from src.lib.reporter.plugins.html import render_html_report
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.provider.provider import PluginProvider
from src.lib.reporter.plugins.sarif import SarifReportPlugin
from src.lib.reporter.plugins.sqlite import SqliteReportPlugin
from src.lib.reporter.plugins.txt import TextReportPlugin
from tests.reporting_helpers import fetch_sqlite_row, read_bucket_report, read_csv_report, read_json_report


class TestEndpointReporterMetadata(unittest.TestCase):
    """Report metadata tests for endpoint findings."""

    def setUp(self):
        """Prepare a report payload and temporary output directory."""

        self.tmpdir = tempfile.TemporaryDirectory()
        self.endpoint_detection = {
            'type': 'ajax',
            'confidence': 90,
            'count': 2,
            'types': ['ajax', 'websocket'],
            'endpoints': [
                {
                    'type': 'ajax',
                    'method': 'POST',
                    'endpoint': '/api/login',
                    'source': 'fetch_call',
                    'confidence': 90,
                },
                {
                    'type': 'websocket',
                    'endpoint': '/ws/live',
                    'source': 'websocket_constructor',
                    'confidence': 95,
                },
            ],
        }
        self.passive_finding = {
            'bucket': 'endpoint',
            'type': 'ajax',
            'url': 'https://api.example.com/app.js',
            'severity': 'info',
            'reason': 'client_endpoint_reference',
            'confidence': 'high',
            'evidence': {
                'endpoint_type': 'ajax',
                'confidence_score': 90,
                'count': 2,
                'types': ['ajax', 'websocket'],
                'endpoints': list(self.endpoint_detection['endpoints']),
            },
            'source': {
                'signal': 'response_body',
                'request_method': 'GET',
                'status': 200,
            },
        }
        self.report_data = {
            'total': {'endpoint': 1},
            'items': {'endpoint': ['https://api.example.com/app.js']},
            'report_items': {
                'endpoint': [
                    {
                        'url': 'https://api.example.com/app.js',
                        'code': '200',
                        'size': '2KB',
                        'endpoint_detection': dict(self.endpoint_detection),
                        'passive_finding': dict(self.passive_finding),
                    }
                ]
            },
        }

    def tearDown(self):
        """Remove temporary report files."""

        self.tmpdir.cleanup()

    def test_text_format_includes_endpoint_detection_summary(self):
        """Plain text reports should include compact endpoint evidence."""

        item = self.report_data['report_items']['endpoint'][0]
        rendered = PluginProvider.format_report_item(item)

        self.assertIn('endpoint=ajax', rendered)
        self.assertIn('confidence=90%', rendered)
        self.assertIn('count=2', rendered)
        self.assertIn('types=ajax;websocket', rendered)
        self.assertIn('samples=POST /api/login;/ws/live', rendered)
        self.assertIn('finding=ajax', rendered)
        self.assertIn('reason=client_endpoint_reference', rendered)

    def test_json_report_preserves_nested_endpoint_detection(self):
        """JSON reports should serialize nested endpoint metadata unchanged."""

        JsonReportPlugin('api.example.com', self.report_data, directory=self.tmpdir.name).process()
        payload = read_json_report(self.tmpdir.name, 'api.example.com')

        self.assertEqual(payload['report_items']['endpoint'][0]['endpoint_detection'], self.endpoint_detection)
        self.assertEqual(payload['report_items']['endpoint'][0]['passive_finding'], self.passive_finding)

    def test_csv_report_exposes_endpoint_passive_finding_columns(self):
        """CSV reports should expose endpoint metadata through shared finding columns."""

        CsvReportPlugin('api.example.com', self.report_data, directory=self.tmpdir.name).process()
        rows = read_csv_report(self.tmpdir.name, 'api.example.com')

        self.assertEqual(rows[0]['status'], 'endpoint')
        self.assertEqual(rows[0]['finding_type'], 'ajax')
        self.assertEqual(rows[0]['finding_severity'], 'info')
        self.assertEqual(rows[0]['finding_reason'], 'client_endpoint_reference')
        self.assertEqual(rows[0]['finding_confidence'], 'high')
        self.assertIn('response_body', rows[0]['finding_source'])
        self.assertIn('/api/login', rows[0]['finding_evidence'])
        self.assertIn('/ws/live', rows[0]['finding_evidence'])

    def test_sqlite_report_exposes_endpoint_passive_finding_columns(self):
        """SQLite reports should store endpoint metadata through shared finding columns."""

        SqliteReportPlugin('api.example.com', self.report_data, directory=self.tmpdir.name).process()
        row = fetch_sqlite_row(
            self.tmpdir.name,
            'api.example.com',
            'SELECT status, finding_type, finding_severity, finding_reason, finding_confidence, '
            'finding_source, finding_evidence FROM items',
        )

        self.assertEqual(row[:5], (
            'endpoint',
            'ajax',
            'info',
            'client_endpoint_reference',
            'high',
        ))
        self.assertIn('response_body', row[5])
        self.assertIn('/api/login', row[6])
        self.assertIn('/ws/live', row[6])

    def test_html_report_renders_endpoint_detection_object(self):
        """HTML reports should render nested endpoint evidence fields."""

        html = render_html_report('api.example.com', self.report_data)

        self.assertIn('endpoint_detection', html)
        self.assertIn('passive_finding', html)
        self.assertIn('client_endpoint_reference', html)
        self.assertIn('/api/login', html)
        self.assertIn('/ws/live', html)

    def test_sarif_report_classifies_endpoint_as_note(self):
        """SARIF reports should use a dedicated endpoint rule and properties."""

        payload = SarifReportPlugin('api.example.com', self.report_data, directory=self.tmpdir.name).build_sarif_log()
        result = payload['runs'][0]['results'][0]

        self.assertEqual(result['ruleId'], 'opendoor.finding.endpoint')
        self.assertEqual(result['level'], 'note')
        self.assertEqual(result['properties']['endpointDetection'], self.endpoint_detection)
        self.assertEqual(result['properties']['passiveFinding'], self.passive_finding)
        self.assertIn('client-exposed endpoint', result['message']['text'])

    def test_text_report_writes_endpoint_bucket_file(self):
        """TXT reports should write one endpoint bucket file."""

        TextReportPlugin('api.example.com', self.report_data, directory=self.tmpdir.name).process()
        content = read_bucket_report(self.tmpdir.name, 'api.example.com', 'endpoint')

        self.assertIn('endpoint=ajax', content)
        self.assertIn('client_endpoint_reference', content)
        self.assertIn('/api/login', content)


if __name__ == '__main__':
    unittest.main()
