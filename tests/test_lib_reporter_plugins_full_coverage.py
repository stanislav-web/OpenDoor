# -*- coding: utf-8 -*-

import copy
import os
import unittest
from unittest.mock import patch

from src.core.filesystem.exceptions import FileSystemError
from src.lib.reporter.plugins.html import HtmlReportPlugin
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.txt import TextReportPlugin


class TestReporterPluginsFullCoverage(unittest.TestCase):
    """Extra branch tests to close html/json/txt reporter plugin coverage."""

    def setUp(self):
        """Prepare common payloads."""

        self.target = 'test.local'
        self.plain_data = {
            'items': {
                'success': ['http://example.com/admin'],
                'failed': ['http://example.com/missing'],
                'indexof': ['http://example.com/public'],
            }
        }
        self.rich_data = {
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
        }

    def test_html_process_preserves_existing_report_items_and_does_not_mutate_source(self):
        """HtmlReportPlugin should keep existing report_items and avoid mutating source data."""

        source = copy.deepcopy(self.rich_data)

        with patch('src.lib.reporter.plugins.html.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.html.filesystem.clear'), \
                patch('src.lib.reporter.plugins.html.Json2Html') as json2html_cls:
            json2html_cls.return_value.convert.return_value = '<table>ok</table>'

            plugin = HtmlReportPlugin(self.target, source, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        payload = json2html_cls.return_value.convert.call_args.kwargs['json']
        self.assertEqual(payload['report_items'], self.rich_data['report_items'])
        self.assertEqual(source, self.rich_data)
        record_mock.assert_called_once_with('/tmp/reports', self.target, '<table>ok</table>')

    def test_html_process_handles_missing_items_key(self):
        """HtmlReportPlugin should build an empty report_items map when items are missing."""

        data = {'total': {'items': 0}}

        with patch('src.lib.reporter.plugins.html.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.html.filesystem.clear'), \
                patch('src.lib.reporter.plugins.html.Json2Html') as json2html_cls:
            json2html_cls.return_value.convert.return_value = '<table>ok</table>'

            plugin = HtmlReportPlugin(self.target, data, directory='/custom/')
            with patch.object(plugin, 'record'):
                plugin.process()

        payload = json2html_cls.return_value.convert.call_args.kwargs['json']
        self.assertEqual(payload, {'total': {'items': 0}, 'report_items': {}})

    def test_html_process_wraps_record_filesystem_error(self):
        """HtmlReportPlugin should wrap FileSystemError raised during record."""

        with patch('src.lib.reporter.plugins.html.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.html.filesystem.clear'), \
                patch('src.lib.reporter.plugins.html.Json2Html') as json2html_cls:
            json2html_cls.return_value.convert.return_value = '<table>ok</table>'

            plugin = HtmlReportPlugin(self.target, self.plain_data, directory='/custom/')
            with patch.object(plugin, 'record', side_effect=FileSystemError('boom')):
                with self.assertRaises(Exception):
                    plugin.process()

    def test_text_process_skips_when_only_failed_bucket_exists(self):
        """TextReportPlugin should not write reports when only failed items are present."""

        data = {'items': {'failed': ['http://example.com/missing']}}

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear') as clear_mock:
            plugin = TextReportPlugin(self.target, data, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        clear_mock.assert_called_once_with('/tmp/reports', extension='.txt')
        record_mock.assert_not_called()

    def test_text_process_handles_empty_items_bucket(self):
        """TextReportPlugin should not write reports when items are empty."""

        data = {'items': {}}

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear') as clear_mock:
            plugin = TextReportPlugin(self.target, data, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        clear_mock.assert_called_once_with('/tmp/reports', extension='.txt')
        record_mock.assert_not_called()

    def test_text_process_prefers_detailed_report_items(self):
        """TextReportPlugin should use report_items instead of plain item URLs when present."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear'):
            plugin = TextReportPlugin(self.target, self.rich_data, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        record_mock.assert_any_call('/tmp/reports', 'success', ['http://example.com/admin - 200 - 9B'], '\n')
        record_mock.assert_any_call('/tmp/reports', 'indexof', ['http://example.com/public - 200 - 1KB'], '\n')

    def test_text_process_wraps_record_exception(self):
        """TextReportPlugin should wrap generic record exceptions."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear'):
            plugin = TextReportPlugin(self.target, self.rich_data, directory='/custom/')
            with patch.object(plugin, 'record', side_effect=Exception('boom')):
                with self.assertRaises(Exception):
                    plugin.process()

    def test_json_init_joins_custom_directory_without_separator(self):
        """JsonReportPlugin should join custom directories without requiring a trailing separator."""

        with patch('src.lib.reporter.plugins.json.filesystem.makedir', return_value='/tmp/reports') as makedir_mock:
            JsonReportPlugin(self.target, self.plain_data, directory='/custom/reports')

        makedir_mock.assert_called_once_with(os.path.join('/custom/reports', self.target))

    def test_json_process_uses_serialized_payload(self):
        """JsonReportPlugin should record the serialized JSON returned by helper.to_json."""

        with patch('src.lib.reporter.plugins.json.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.json.helper.to_json', return_value='{"ok": true}') as to_json_mock, \
                patch('src.lib.reporter.plugins.json.filesystem.clear'):
            plugin = JsonReportPlugin(self.target, self.plain_data, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        to_json_mock.assert_called_once_with(self.plain_data)
        record_mock.assert_called_once_with('/tmp/reports', self.target, '{"ok": true}')

    def test_json_process_propagates_to_json_runtime_error(self):
        """JsonReportPlugin should propagate errors raised before entering the filesystem try block."""

        with patch('src.lib.reporter.plugins.json.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.json.helper.to_json', side_effect=RuntimeError('boom')):
            plugin = JsonReportPlugin(self.target, self.plain_data, directory='/custom/')
            with self.assertRaises(RuntimeError):
                plugin.process()

    def test_json_process_wraps_record_filesystem_error(self):
        """JsonReportPlugin should wrap FileSystemError raised during record."""

        with patch('src.lib.reporter.plugins.json.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.json.helper.to_json', return_value='{"ok": true}'), \
                patch('src.lib.reporter.plugins.json.filesystem.clear'):
            plugin = JsonReportPlugin(self.target, self.plain_data, directory='/custom/')
            with patch.object(plugin, 'record', side_effect=FileSystemError('boom')):
                with self.assertRaises(Exception):
                    plugin.process()


if __name__ == '__main__':
    unittest.main()