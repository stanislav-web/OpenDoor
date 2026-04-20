# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch

from src.core import FileSystemError
from src.core.logger.logger import Logger
from src.lib.reporter import Reporter, ReporterError
from src.lib.reporter.plugins.provider.provider import PluginProvider
from src.lib.reporter.plugins.std import StdReportPlugin
from src.lib.reporter.plugins.txt import TextReportPlugin
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.html import HtmlReportPlugin


class TestReporter(unittest.TestCase):
    """TestReporter class."""

    def setUp(self):
        self.mockdata = {
            'items': {
                'failed': ['http://test.local/failed.php'],
                'success': ['http://test.local/success.php'],
                'index': ['http://test.local/index/'],
            },
            'total': {
                'failed': 1,
                'items': 3,
                'success': 1,
                'workers': 1,
            },
        }
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        Reporter.external_directory = None

    def tearDown(self):
        Reporter.external_directory = None
        logger = Logger.log()
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
        self.temp_dir.cleanup()

    def test_is_reported_uses_default_reports_directory(self):
        """Reporter.is_reported() should use the default reports directory when no external directory is set."""

        Reporter.config = {'reports': self.base_dir}
        with open(os.path.join(self.base_dir, 'resource'), 'w', encoding='utf-8'):
            pass

        self.assertTrue(Reporter.is_reported('resource'))

    def test_is_reported_uses_external_directory_and_appends_separator(self):
        """Reporter.is_reported() should normalize an external directory path before checking it."""

        Reporter.external_directory = self.base_dir.rstrip(os.path.sep)
        with open(os.path.join(self.base_dir, 'resource'), 'w', encoding='utf-8'):
            pass

        self.assertTrue(Reporter.is_reported('resource'))
        self.assertTrue(Reporter.external_directory.endswith(os.path.sep))

    def test_is_reported_wraps_filesystem_errors(self):
        """Reporter.is_reported() should wrap filesystem failures into ReporterError."""

        Reporter.config = {'reports': self.base_dir}
        with patch('src.lib.reporter.reporter.filesystem.is_exist', side_effect=FileSystemError('boom')):
            with self.assertRaises(ReporterError):
                Reporter.is_reported('resource')

    def test_load_returns_plugin_instance(self):
        """Reporter.load() should return a plugin instance for known plugins."""

        plugin = Reporter.load('std', 'test.local', self.mockdata)
        self.assertIsInstance(plugin, PluginProvider)

    def test_load_raises_for_unknown_plugin(self):
        """Reporter.load() should reject unknown plugin names."""

        with self.assertRaises(ReporterError):
            Reporter.load('undefined', 'test.local', self.mockdata)

    def test_load_wraps_import_errors(self):
        """Reporter.load() should wrap import failures into ReporterError."""

        with patch('src.lib.reporter.reporter.importlib.import_module', side_effect=ImportError):
            with self.assertRaises(ReporterError):
                Reporter.load('std', 'test.local', self.mockdata)

    def test_load_wraps_plugin_construction_errors(self):
        """Reporter.load() should wrap plugin construction failures into ReporterError."""

        class BrokenModule(object):
            @staticmethod
            def std(*args, **kwargs):
                raise TypeError('broken plugin')

        with patch('src.lib.reporter.reporter.importlib.import_module', return_value=BrokenModule):
            with self.assertRaises(ReporterError):
                Reporter.load('std', 'test.local', self.mockdata)

    def test_plugin_provider_rejects_invalid_data(self):
        """PluginProvider should reject non-dict report data."""

        with self.assertRaises(TypeError):
            PluginProvider('test.local', 'wrongdata')

    def test_plugin_provider_process_returns_none(self):
        """PluginProvider.process() should keep the base no-op behavior."""

        provider = PluginProvider('test.local', self.mockdata)
        self.assertIsNone(provider.process())

    def test_plugin_provider_record_writes_file_and_logs(self):
        """PluginProvider.record() should create the file and emit a report notification."""

        target_dir = os.path.join(self.base_dir, 'reports')
        os.makedirs(target_dir, exist_ok=True)

        with patch('src.lib.reporter.plugins.provider.provider.tpl.info') as info_mock:
            PluginProvider.record(target_dir, 'success', ['line1', 'line2'], '\n')

        report_file = os.path.join(target_dir, 'success.pp')
        self.assertTrue(os.path.isfile(report_file))
        with open(report_file, 'r', encoding='utf-8') as handler:
            self.assertEqual(handler.read(), 'line1\nline2')
        info_mock.assert_called_once()

    def test_plugin_provider_record_wraps_filesystem_errors(self):
        """PluginProvider.record() should wrap filesystem errors."""

        with patch('src.lib.reporter.plugins.provider.provider.filesystem.makefile', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                PluginProvider.record(self.base_dir, 'success', ['line'])

    def test_std_plugin_process_writes_table_to_stdout(self):
        """StdReportPlugin.process() should render the summary table to stdout."""

        plugin = StdReportPlugin('test.local', self.mockdata)

        with patch('src.lib.reporter.plugins.std.sys.writeln') as writeln_mock:
            self.assertIsNone(plugin.process())

        rendered = writeln_mock.call_args[0][0]
        self.assertIn('Statistics (test.local)', rendered)
        self.assertIn('workers', rendered)

    def test_text_plugin_init_wraps_makedir_errors(self):
        """TextReportPlugin.__init__() should wrap directory creation failures."""

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                TextReportPlugin('test.local', self.mockdata, directory=self.base_dir + os.path.sep)

    def test_text_plugin_process_writes_only_non_failed_statuses(self):
        """TextReportPlugin.process() should create text files only for non-failed statuses."""

        plugin = TextReportPlugin('test.local', self.mockdata, directory=self.base_dir + os.path.sep)
        plugin.process()

        target_dir = os.path.join(self.base_dir, 'test.local')
        self.assertTrue(os.path.isfile(os.path.join(target_dir, 'success.txt')))
        self.assertTrue(os.path.isfile(os.path.join(target_dir, 'index.txt')))
        self.assertFalse(os.path.exists(os.path.join(target_dir, 'failed.txt')))

    def test_text_plugin_process_wraps_clear_errors(self):
        """TextReportPlugin.process() should wrap filesystem.clear() failures."""

        plugin = TextReportPlugin('test.local', self.mockdata, directory=self.base_dir + os.path.sep)
        with patch('src.lib.reporter.plugins.txt.filesystem.clear', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                plugin.process()

    def test_json_plugin_init_wraps_makedir_errors(self):
        """JsonReportPlugin.__init__() should wrap directory creation failures."""

        with patch('src.lib.reporter.plugins.json.filesystem.makedir', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                JsonReportPlugin('test.local', self.mockdata, directory=self.base_dir + os.path.sep)

    def test_json_plugin_process_writes_json_file(self):
        """JsonReportPlugin.process() should write a JSON report file."""

        plugin = JsonReportPlugin('test.local', self.mockdata, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, 'test.local', 'test.local.json')
        self.assertTrue(os.path.isfile(report_file))
        with open(report_file, 'r', encoding='utf-8') as handler:
            content = handler.read()
        self.assertIn('"items"', content)
        self.assertIn('"total"', content)

    def test_json_plugin_process_wraps_record_errors(self):
        """JsonReportPlugin.process() should wrap record failures."""

        plugin = JsonReportPlugin('test.local', self.mockdata, directory=self.base_dir + os.path.sep)
        with patch.object(JsonReportPlugin, 'record', side_effect=Exception('boom')):
            with self.assertRaises(Exception):
                plugin.process()

    def test_html_plugin_init_wraps_makedir_errors(self):
        """HtmlReportPlugin.__init__() should wrap directory creation failures."""

        with patch('src.lib.reporter.plugins.html.filesystem.makedir', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                HtmlReportPlugin('test.local', self.mockdata, directory=self.base_dir + os.path.sep)

    def test_html_plugin_process_writes_html_file(self):
        """HtmlReportPlugin.process() should write an HTML report file."""

        plugin = HtmlReportPlugin('test.local', self.mockdata, directory=self.base_dir + os.path.sep)
        plugin.process()

        report_file = os.path.join(self.base_dir, 'test.local', 'test.local.html')
        self.assertTrue(os.path.isfile(report_file))
        with open(report_file, 'r', encoding='utf-8') as handler:
            content = handler.read()
        self.assertIn('<table', content)

    def test_html_plugin_process_wraps_filesystem_errors(self):
        """HtmlReportPlugin.process() should wrap filesystem.clear() failures."""

        plugin = HtmlReportPlugin('test.local', self.mockdata, directory=self.base_dir + os.path.sep)
        with patch('src.lib.reporter.plugins.html.filesystem.clear', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                plugin.process()

    def test_reporter_load_uses_external_directory_without_separator_for_nested_reports(self):
        """Reporter.load() should pass external directories without forcing callers to add a trailing separator."""

        Reporter.external_directory = self.base_dir

        with patch('src.lib.reporter.plugins.json.filesystem.makedir', return_value=os.path.join(self.base_dir, 'test.local')) as makedir_mock:
            plugin = Reporter.load('json', 'test.local', self.mockdata)

        self.assertIsInstance(plugin, JsonReportPlugin)
        makedir_mock.assert_called_once_with(os.path.join(self.base_dir, 'test.local'))


if __name__ == '__main__':
    unittest.main()