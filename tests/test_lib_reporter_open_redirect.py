# -*- coding: utf-8 -*-

import csv
import json
import os
import sqlite3
import tempfile
import unittest

from src.lib.reporter.plugins.csv import CsvReportPlugin
from src.lib.reporter.plugins.html import HtmlReportPlugin, render_html_report
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.provider.provider import PluginProvider
from src.lib.reporter.plugins.sarif import SarifReportPlugin
from src.lib.reporter.plugins.sqlite import SqliteReportPlugin
from src.lib.reporter.plugins.txt import TextReportPlugin


class TestOpenRedirectReporterMetadata(unittest.TestCase):
    """Report metadata tests for confirmed open redirect findings."""

    def setUp(self):
        """Prepare a report payload and temporary output directory."""

        self.tmpdir = tempfile.TemporaryDirectory()
        self.openredirect_detection = {
            'type': 'open_redirect',
            'confidence': 100,
            'source_url': 'https://api.example.com/login?next=/home',
            'probe_url': 'https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F',
            'parameter': 'next',
            'payload': 'https://redirect.invalid/',
            'variant': 'absolute-external-url',
            'location': 'https://redirect.invalid/',
            'marker_host': 'redirect.invalid',
        }
        self.report_data = {
            'total': {'openredirect': 1},
            'items': {'openredirect': ['https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F']},
            'report_items': {
                'openredirect': [
                    {
                        'url': 'https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F',
                        'code': '302',
                        'size': '0B',
                        'openredirect_detection': dict(self.openredirect_detection),
                    }
                ]
            },
        }

    def tearDown(self):
        """Remove temporary report files."""

        self.tmpdir.cleanup()

    def test_text_format_includes_openredirect_detection_summary(self):
        """Plain text reports should include compact openredirect evidence."""

        item = self.report_data['report_items']['openredirect'][0]
        rendered = PluginProvider.format_report_item(item)

        self.assertIn('openredirect=open_redirect', rendered)
        self.assertIn('param=next', rendered)
        self.assertIn('variant=absolute-external-url', rendered)
        self.assertIn('location=https://redirect.invalid/', rendered)
        self.assertIn('confidence=100%', rendered)

    def test_csv_report_flattens_openredirect_detection(self):
        """CSV reports should expose stable openredirect columns."""

        CsvReportPlugin('api.example.com', self.report_data, directory=self.tmpdir.name).process()
        path = os.path.join(self.tmpdir.name, 'api.example.com', 'api.example.com.csv')

        with open(path, newline='', encoding='utf-8') as handler:
            rows = list(csv.DictReader(handler))

        self.assertEqual(rows[0]['status'], 'openredirect')
        self.assertEqual(rows[0]['openredirect_detection'], 'open_redirect')
        self.assertEqual(rows[0]['openredirect_parameter'], 'next')
        self.assertEqual(rows[0]['openredirect_variant'], 'absolute-external-url')
        self.assertEqual(rows[0]['openredirect_location'], 'https://redirect.invalid/')
        self.assertEqual(rows[0]['openredirect_confidence'], '100')

    def test_sqlite_report_flattens_openredirect_detection(self):
        """SQLite reports should store openredirect evidence in queryable columns."""

        SqliteReportPlugin('api.example.com', self.report_data, directory=self.tmpdir.name).process()
        path = os.path.join(self.tmpdir.name, 'api.example.com', 'api.example.com.sqlite')

        connection = sqlite3.connect(path)
        try:
            row = connection.execute(
                'SELECT status, openredirect_detection, openredirect_parameter, openredirect_variant, '
                'openredirect_location, openredirect_confidence FROM items'
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(row, (
            'openredirect',
            'open_redirect',
            'next',
            'absolute-external-url',
            'https://redirect.invalid/',
            100,
        ))

    def test_json_report_preserves_nested_openredirect_detection(self):
        """JSON reports should serialize nested openredirect metadata unchanged."""

        JsonReportPlugin('api.example.com', self.report_data, directory=self.tmpdir.name).process()
        path = os.path.join(self.tmpdir.name, 'api.example.com', 'api.example.com.json')

        with open(path, encoding='utf-8') as handler:
            payload = json.load(handler)

        self.assertEqual(
            payload['report_items']['openredirect'][0]['openredirect_detection'],
            self.openredirect_detection,
        )

    def test_html_report_renders_openredirect_detection_object(self):
        """HTML reports should render nested openredirect evidence fields."""

        html = render_html_report('api.example.com', self.report_data)

        self.assertIn('openredirect_detection', html)
        self.assertIn('open_redirect', html)
        self.assertIn('https://redirect.invalid/', html)

    def test_txt_report_writes_openredirect_bucket(self):
        """TXT reports should create an openredirect report file."""

        TextReportPlugin('api.example.com', self.report_data, directory=self.tmpdir.name).process()
        path = os.path.join(self.tmpdir.name, 'api.example.com', 'openredirect.txt')

        with open(path, encoding='utf-8') as handler:
            contents = handler.read()

        self.assertIn('openredirect=open_redirect', contents)
        self.assertIn('param=next', contents)

    def test_sarif_report_marks_openredirect_as_verified_vulnerability(self):
        """SARIF reports should classify openredirect as a verified vulnerability finding."""

        report = SarifReportPlugin('api.example.com', self.report_data, directory=self.tmpdir.name)
        payload = report.build_sarif_log()
        result = payload['runs'][0]['results'][0]

        self.assertEqual(result['ruleId'], 'opendoor.finding.openredirect')
        self.assertEqual(result['level'], 'error')
        self.assertIn('verified an open redirect vulnerability', result['message']['text'])
        self.assertEqual(result['properties']['openRedirectDetection'], self.openredirect_detection)


if __name__ == '__main__':
    unittest.main()
