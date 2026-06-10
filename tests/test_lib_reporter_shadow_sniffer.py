# -*- coding: utf-8 -*-

import json
import tempfile
import unittest
from unittest.mock import patch

from src.lib.reporter.plugins.csv import CsvReportPlugin
from src.lib.reporter.plugins.html import render_html_report
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.provider.provider import PluginProvider
from src.lib.reporter.plugins.sarif import SarifReportPlugin
from src.lib.reporter.plugins.sqlite import SqliteReportPlugin
from tests.reporting_helpers import fetch_sqlite_row_and_summary, read_csv_report


class TestShadowSnifferReportMetadata(unittest.TestCase):
    """Report metadata tests for active Shadow Copy findings."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'shadow.local'
        self.shadow_detection = {
            'type': 'backup_copy',
            'confidence': 90,
            'reason': 'content_diff',
            'base_url': 'https://shadow.local/index.php',
            'url': 'https://shadow.local/index.php.bak',
            'variant': '.bak',
            'variant_type': 'suffix',
            'similarity': 0.96,
            'base_size': 21,
            'shadow_size': 21,
            'content_type': 'text/html',
        }
        self.passive_finding = {
            'bucket': 'shadow',
            'type': 'backup_copy',
            'url': 'https://shadow.local/index.php.bak',
            'severity': 'high',
            'reason': 'backup_copy_exposed',
            'confidence': 'high',
            'evidence': {
                'shadow_type': 'backup_copy',
                'detection_reason': 'content_diff',
                'base_url': 'https://shadow.local/index.php',
                'candidate_url': 'https://shadow.local/index.php.bak',
                'variant': '.bak',
                'variant_type': 'suffix',
                'similarity': 0.96,
                'confidence_score': 90,
                'base_size': 21,
                'shadow_size': 21,
                'content_type': 'text/html',
            },
            'source': {
                'signal': 'active_followup_response',
                'request_method': 'GET',
                'status': 200,
            },
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
                        'passive_finding': dict(self.passive_finding),
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
            'confidence=90%, similarity=0.96 | '
            'finding=backup_copy, severity=high, reason=backup_copy_exposed, confidence=high'
        )

    def test_csv_report_exposes_queryable_shadow_columns(self):
        """CSV report should flatten shadow_detection into stable columns."""

        plugin = CsvReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        rows = read_csv_report(self.base_dir, self.target)

        self.assertEqual(rows[0]['status'], 'shadow')
        self.assertEqual(rows[0]['shadow_detection'], 'backup_copy')
        self.assertEqual(rows[0]['shadow_confidence'], '90')
        self.assertEqual(rows[0]['shadow_reason'], 'content_diff')
        self.assertEqual(rows[0]['shadow_base_url'], 'https://shadow.local/index.php')
        self.assertEqual(rows[0]['shadow_variant'], '.bak')
        self.assertEqual(rows[0]['shadow_similarity'], '0.96')
        self.assertEqual(rows[0]['shadow_base_size'], '21')
        self.assertEqual(rows[0]['shadow_size'], '21')
        self.assertEqual(rows[0]['finding_type'], 'backup_copy')
        self.assertEqual(rows[0]['finding_severity'], 'high')
        self.assertEqual(rows[0]['finding_reason'], 'backup_copy_exposed')
        self.assertEqual(rows[0]['finding_confidence'], 'high')
        self.assertIn('active_followup_response', rows[0]['finding_source'])
        self.assertIn('https://shadow.local/index.php', rows[0]['finding_evidence'])

    def test_sqlite_report_exposes_queryable_shadow_columns(self):
        """SQLite report should flatten shadow_detection into queryable columns."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        row, summary = fetch_sqlite_row_and_summary(
            self.base_dir,
            self.target,
            'SELECT status, shadow_detection, shadow_confidence, shadow_reason, '
            'shadow_base_url, shadow_variant, shadow_similarity, shadow_base_size, shadow_size, '
            'finding_type, finding_severity, finding_reason, finding_confidence, finding_source, finding_evidence FROM items',
        )

        self.assertEqual(
            row[:9],
            (
                'shadow',
                'backup_copy',
                90,
                'content_diff',
                'https://shadow.local/index.php',
                '.bak',
                0.96,
                21,
                21,
            )
        )
        self.assertEqual(row[9:13], ('backup_copy', 'high', 'backup_copy_exposed', 'high'))
        self.assertIn('active_followup_response', row[13])
        self.assertIn('https://shadow.local/index.php', row[14])
        self.assertEqual(summary['shadow_probes'], 12)

    def test_json_report_preserves_nested_shadow_detection_object(self):
        """JSON report should serialize the nested shadow_detection object."""

        with patch('src.lib.reporter.plugins.json.filesystem.clear'), \
                patch('src.lib.reporter.plugins.json.JsonReportPlugin.record') as record_mock:
            JsonReportPlugin(self.target, self.data, directory=self.base_dir).process()

        payload = json.loads(record_mock.call_args[0][2])
        self.assertEqual(payload['report_items']['shadow'][0]['shadow_detection'], self.shadow_detection)
        self.assertEqual(payload['report_items']['shadow'][0]['passive_finding'], self.passive_finding)

    def test_html_report_renders_nested_shadow_detection_object(self):
        """HTML report should render shadow_detection details."""

        html = render_html_report(self.target, self.data)

        self.assertIn('shadow_detection', html)
        self.assertIn('passive_finding', html)
        self.assertIn('backup_copy_exposed', html)
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
        self.assertEqual(result['properties']['passiveFinding'], self.passive_finding)
        self.assertIn('exposed shadow copy', result['message']['text'])


if __name__ == '__main__':
    unittest.main()
