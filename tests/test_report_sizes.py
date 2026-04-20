# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib3.response import HTTPResponse

from src.core import helper
from src.core.http.response import Response
from src.lib.browser.browser import Browser
from src.lib.reporter.plugins.html import HtmlReportPlugin
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.provider.provider import PluginProvider
from src.lib.reporter.plugins.txt import TextReportPlugin


class TestResponseAndBrowser(unittest.TestCase):
    """Regression tests for propagating response size into report data."""

    @staticmethod
    def make_cfg(**kwargs):
        base = dict(is_sniff=False, sniffers=[], SUBDOMAINS_SCAN='subdomains', scan='directories')
        base.update(kwargs)
        return SimpleNamespace(**base)

    @staticmethod
    def make_debug():
        return SimpleNamespace(
            level=0,
            debug_load_sniffer_plugin=MagicMock(),
            debug_response=MagicMock(),
            debug_request_uri=MagicMock(),
        )

    @staticmethod
    def make_response(status=200, body=b'', headers=None):
        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_response_handle_returns_content_size_for_success_and_subdomain_fallback(self):
        """Response.handle() should return content size for reporter consumers."""

        response_handler = Response(self.make_cfg(scan='directories'), self.make_debug(), tpl=MagicMock())
        status, url, size, code = response_handler.handle(
            self.make_response(status=200, body=b'ok', headers={'Content-Length': '2'}),
            'http://example.com/path',
            1,
            2,
            [],
        )

        self.assertEqual((status, url, size, code), ('success', 'http://example.com/path', '2B', '200'))

        subdomain_handler = Response(self.make_cfg(scan='subdomains'), self.make_debug(), tpl=MagicMock())
        status, url, size, code = subdomain_handler.handle(SimpleNamespace(data=b'xyz', headers={}), 'http://sub.example.com', 1, 1, [])
        self.assertEqual((status, url, size, code), ('failed', 'http://sub.example.com', '3B', '-'))

    def test_browser_catch_report_data_keeps_legacy_items_and_detailed_report_items(self):
        """Browser.__catch_report_data() should preserve old buckets and add report metadata."""

        browser = Browser.__new__(Browser)
        setattr(browser, '_Browser__result', {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
        })

        browser._Browser__catch_report_data('success', 'http://example.com/admin', '10B', '200')
        browser._Browser__catch_report_data('ignored', 'http://example.com/ignored')

        result = getattr(browser, '_Browser__result')
        self.assertEqual(result['items']['success'], ['http://example.com/admin'])
        self.assertEqual(result['report_items']['success'], [{'url': 'http://example.com/admin', 'size': '10B', 'code': '200'}])
        self.assertEqual(result['report_items']['ignored'], [{'url': 'http://example.com/ignored', 'size': '0B', 'code': '-'}])
        self.assertEqual(result['total']['success'], 1)
        self.assertEqual(result['total']['ignored'], 1)


class TestReporterPlugins(unittest.TestCase):
    """Report plugin tests for response size export."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'test.local'
        self.data = {
            'items': {
                'success': ['http://example.com/admin'],
                'failed': ['http://example.com/missing'],
                'indexof': ['http://example.com/public'],
            },
            'report_items': {
                'success': [{'url': 'http://example.com/admin', 'size': '9B', 'code': '200'}],
                'failed': [{'url': 'http://example.com/missing', 'size': '0B', 'code': '404'}],
                'indexof': [{'url': 'http://example.com/public', 'size': '1KB', 'code': '200'}],
            },
            'total': {
                'success': 1,
                'failed': 1,
                'indexof': 1,
                'items': 3,
                'workers': 1,
            },
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_plugin_provider_falls_back_to_legacy_items_when_report_items_are_missing(self):
        """PluginProvider should enrich legacy URL-only buckets with default sizes."""

        provider = PluginProvider(self.target, {'items': {'legacy': ['http://legacy.local']}})

        self.assertEqual(provider.get_report_items('legacy'), [{'url': 'http://legacy.local', 'size': '0B', 'code': '-'}])
        self.assertEqual(provider.format_report_item({'url': 'http://legacy.local', 'size': '0B', 'code': '-'}), 'http://legacy.local - - - 0B')
        self.assertEqual(provider.format_report_item('http://legacy.local'), 'http://legacy.local')

    def test_text_report_includes_size_and_skips_failed_bucket(self):
        """Text reports should include response size for non-failed buckets only."""

        plugin = TextReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        target_dir = os.path.join(self.base_dir, self.target)
        success_file = os.path.join(target_dir, 'success.txt')
        index_file = os.path.join(target_dir, 'indexof.txt')
        failed_file = os.path.join(target_dir, 'failed.txt')

        self.assertTrue(os.path.isfile(success_file))
        self.assertTrue(os.path.isfile(index_file))
        self.assertFalse(os.path.exists(failed_file))

        with open(success_file, 'r', encoding='utf-8') as handler:
            self.assertIn('http://example.com/admin - 200 - 9B', handler.read())

        with open(index_file, 'r', encoding='utf-8') as handler:
            self.assertIn('http://example.com/public - 200 - 1KB', handler.read())

    def test_text_report_falls_back_to_default_size_for_legacy_payload(self):
        """Text reports should remain backward compatible with URL-only payloads."""

        plugin = TextReportPlugin(self.target, {'items': {'success': ['http://example.com/legacy']}}, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, self.target, 'success.txt')
        with open(report_file, 'r', encoding='utf-8') as handler:
            self.assertIn('http://example.com/legacy - - - 0B', handler.read())

    def test_json_report_contains_report_items_with_size_metadata(self):
        """JSON reports should expose detailed report_items with response sizes."""

        plugin = JsonReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, self.target, self.target + '.json')
        with open(report_file, 'r', encoding='utf-8') as handler:
            content = handler.read()

        self.assertIn('"report_items"', content)
        self.assertIn('"size": "9B"', content)
        self.assertIn('"url": "http://example.com/admin"', content)

    def test_html_report_uses_detailed_report_items_and_builds_fallbacks(self):
        """HTML reports should receive report_items regardless of input payload shape."""

        with patch('src.lib.reporter.plugins.html.Json2Html') as json2html_cls:
            json2html_cls.return_value.convert.return_value = '<table>ok</table>'

            plugin = HtmlReportPlugin(self.target, self.data, directory=self.base_dir + os.path.sep)
            plugin.process()

            report_payload = json2html_cls.return_value.convert.call_args.kwargs['json']
            self.assertEqual(report_payload['report_items']['success'], [{'url': 'http://example.com/admin', 'size': '9B', 'code': '200'}])

        with patch('src.lib.reporter.plugins.html.Json2Html') as json2html_cls:
            json2html_cls.return_value.convert.return_value = '<table>ok</table>'
            legacy_data = {'items': {'success': ['http://example.com/legacy']}}

            plugin = HtmlReportPlugin(self.target, legacy_data, directory=self.base_dir + os.path.sep)
            plugin.process()

            report_payload = json2html_cls.return_value.convert.call_args.kwargs['json']
            self.assertEqual(
                report_payload['report_items']['success'],
                [{'url': 'http://example.com/legacy', 'size': '0B', 'code': '-'}],
            )


if __name__ == '__main__':
    unittest.main()