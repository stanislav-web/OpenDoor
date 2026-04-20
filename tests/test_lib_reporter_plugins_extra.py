# -*- coding: utf-8 -*-

import os
import unittest
from unittest.mock import patch

from src.core.filesystem.exceptions import FileSystemError
from src.lib.reporter.plugins.html import HtmlReportPlugin
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.txt import TextReportPlugin


class TestReporterPluginsExtra(unittest.TestCase):
    """TestReporterPluginsExtra class."""

    def setUp(self):
        """Prepare a common report payload."""

        self.target = 'test.local'
        self.data = {
            'items': {
                'success': ['http://example.com/admin'],
                'failed': ['http://example.com/missing'],
                'indexof': ['http://example.com/public'],
            }
        }

    def test_html_plugin_uses_default_reports_directory_and_records_html(self):
        """HtmlReportPlugin should resolve default report directory and record converted HTML."""

        with patch('src.lib.reporter.plugins.html.CoreConfig', {'data': {'reports': '/reports/'}}), \
                patch('src.lib.reporter.plugins.html.filesystem.makedir', return_value='/tmp/reports') as makedir_mock, \
                patch('src.lib.reporter.plugins.html.filesystem.clear') as clear_mock, \
                patch('src.lib.reporter.plugins.html.Json2Html') as json2html_cls:
            json2html_cls.return_value.convert.return_value = '<table>ok</table>'

            plugin = HtmlReportPlugin(self.target, self.data)
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        makedir_mock.assert_called_once_with('/reports/' + self.target)
        clear_mock.assert_called_once_with('/tmp/reports', extension='.html')
        json2html_cls.return_value.convert.assert_called_once_with(
            json={
                'items': self.data['items'],
                'report_items': {
                    'success': [{'url': 'http://example.com/admin', 'size': '0B', 'code': '-'}],
                    'failed': [{'url': 'http://example.com/missing', 'size': '0B', 'code': '-'}],
                    'indexof': [{'url': 'http://example.com/public', 'size': '0B', 'code': '-'}],
                },
            },
            table_attributes='border="1" cellpadding="2"',
        )
        record_mock.assert_called_once_with('/tmp/reports', self.target, '<table>ok</table>')

    def test_html_plugin_uses_custom_directory(self):
        """HtmlReportPlugin should honor a custom output directory."""

        with patch('src.lib.reporter.plugins.html.filesystem.makedir', return_value='/tmp/custom') as makedir_mock:
            HtmlReportPlugin(self.target, self.data, directory='/custom/')

        makedir_mock.assert_called_once_with('/custom/' + self.target)

    def test_html_plugin_wraps_filesystem_errors(self):
        """HtmlReportPlugin should wrap filesystem errors from constructor and process."""

        with patch('src.lib.reporter.plugins.html.filesystem.makedir', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                HtmlReportPlugin(self.target, self.data, directory='/custom/')

        with patch('src.lib.reporter.plugins.html.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.html.filesystem.clear', side_effect=FileSystemError('boom')):
            plugin = HtmlReportPlugin(self.target, self.data, directory='/custom/')
            with self.assertRaises(Exception):
                plugin.process()

    def test_json_plugin_uses_default_reports_directory_and_records_json(self):
        """JsonReportPlugin should resolve default report directory and record serialized JSON."""

        with patch('src.lib.reporter.plugins.json.CoreConfig', {'data': {'reports': '/reports/'}}), \
                patch('src.lib.reporter.plugins.json.filesystem.makedir', return_value='/tmp/reports') as makedir_mock, \
                patch('src.lib.reporter.plugins.json.filesystem.clear') as clear_mock, \
                patch('src.lib.reporter.plugins.json.helper.to_json', return_value='{"ok": true}') as to_json_mock:
            plugin = JsonReportPlugin(self.target, self.data)
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        makedir_mock.assert_called_once_with('/reports/' + self.target)
        clear_mock.assert_called_once_with('/tmp/reports', extension='.json')
        to_json_mock.assert_called_once_with(self.data)
        record_mock.assert_called_once_with('/tmp/reports', self.target, '{"ok": true}')

    def test_json_plugin_wraps_processing_errors(self):
        """JsonReportPlugin should wrap conversion and filesystem failures."""

        with patch('src.lib.reporter.plugins.json.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.json.helper.to_json', side_effect=RuntimeError('boom')):
            plugin = JsonReportPlugin(self.target, self.data, directory='/custom/')
            with self.assertRaises(Exception):
                plugin.process()

        with patch('src.lib.reporter.plugins.json.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.json.helper.to_json', return_value='{}'), \
                patch('src.lib.reporter.plugins.json.filesystem.clear', side_effect=FileSystemError('boom')):
            plugin = JsonReportPlugin(self.target, self.data, directory='/custom/')
            with self.assertRaises(Exception):
                plugin.process()

    def test_text_plugin_uses_default_reports_directory_and_skips_failed_items(self):
        """TextReportPlugin should record non-failed buckets only."""

        with patch('src.lib.reporter.plugins.txt.CoreConfig', {'data': {'reports': '/reports/'}}), \
                patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports') as makedir_mock, \
                patch('src.lib.reporter.plugins.txt.filesystem.clear') as clear_mock:
            plugin = TextReportPlugin(self.target, self.data)
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        makedir_mock.assert_called_once_with('/reports/' + self.target)
        clear_mock.assert_called_once_with('/tmp/reports', extension='.txt')

        self.assertEqual(record_mock.call_count, 2)
        record_mock.assert_any_call('/tmp/reports', 'success', ['http://example.com/admin - - - 0B'], '\n')
        record_mock.assert_any_call('/tmp/reports', 'indexof', ['http://example.com/public - - - 0B'], '\n')

    def test_text_plugin_wraps_constructor_and_process_errors(self):
        """TextReportPlugin should wrap constructor and processing filesystem failures."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                TextReportPlugin(self.target, self.data, directory='/custom/')

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear', side_effect=FileSystemError('boom')):
            plugin = TextReportPlugin(self.target, self.data, directory='/custom/')
            with self.assertRaises(Exception):
                plugin.process()

    def test_plugins_join_directory_without_separator(self):
        """Report plugins should create nested target directories when base path has no trailing separator."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/text') as text_makedir:
            TextReportPlugin(self.target, self.data, directory='/custom/reports')
        text_makedir.assert_called_once_with(os.path.join('/custom/reports', self.target))

        with patch('src.lib.reporter.plugins.json.filesystem.makedir', return_value='/tmp/json') as json_makedir:
            JsonReportPlugin(self.target, self.data, directory='/custom/reports')
        json_makedir.assert_called_once_with(os.path.join('/custom/reports', self.target))

        with patch('src.lib.reporter.plugins.html.filesystem.makedir', return_value='/tmp/html') as html_makedir:
            HtmlReportPlugin(self.target, self.data, directory='/custom/reports')
        html_makedir.assert_called_once_with(os.path.join('/custom/reports', self.target))


if __name__ == '__main__':
    unittest.main()