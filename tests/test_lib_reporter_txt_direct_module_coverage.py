# -*- coding: utf-8 -*-

import importlib
import tempfile
import unittest
from unittest.mock import patch


class TestTextReportPluginDirectModuleCoverage(unittest.TestCase):
    """Direct coverage for src.lib.reporter.plugins.txt without reporter indirection."""

    def setUp(self):
        """Load the concrete txt.py module."""

        self.module = importlib.import_module('src.lib.reporter.plugins.txt')
        self.plugin_cls = self.module.TextReportPlugin

    def make_plugin(self, data=None):
        """Create a TextReportPlugin instance without running __init__ side effects."""

        plugin = object.__new__(self.plugin_cls)
        setattr(plugin, '_target', 'test.local')
        setattr(plugin, '_data', data or {'items': {}, 'report_items': {}})
        setattr(plugin, '_TextReportPlugin__target_dir', '/tmp/opendoor-txt-test')
        return plugin

    def test_init_uses_default_reports_directory(self):
        """__init__ should resolve the default reports directory from CoreConfig."""

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(self.module.CoreConfig, {'data': {'reports': tmpdir}}, clear=False):
                plugin = self.plugin_cls('test.local', {'items': {}, 'report_items': {}}, directory=None)

        self.assertEqual(getattr(plugin, '_target'), 'test.local')

    def test_init_wraps_filesystem_errors(self):
        """__init__ should wrap filesystem creation failures."""

        error = self.module.FileSystemError('boom')
        with patch.object(self.module.filesystem, 'makedir', side_effect=error):
            with self.assertRaises(Exception) as ctx:
                self.plugin_cls('test.local', {'items': {}, 'report_items': {}}, directory='/tmp')

        self.assertIn('boom', str(ctx.exception))

    def test_format_fingerprint_summary_returns_empty_for_missing_payload(self):
        """format_fingerprint_summary() should ignore absent fingerprint payloads."""

        plugin = self.make_plugin({'items': {}, 'report_items': {}})

        self.assertEqual(plugin.format_fingerprint_summary(), [])

    def test_format_fingerprint_summary_handles_base_payload_without_optional_blocks(self):
        """format_fingerprint_summary() should render base rows without runtime/infra blocks."""

        plugin = self.make_plugin({
            'items': {},
            'report_items': {},
            'fingerprint': {
                'category': 'cms',
                'name': 'WordPress',
                'confidence': 95,
            },
        })

        self.assertEqual(plugin.format_fingerprint_summary(), [
            'category: cms',
            'name: WordPress',
            'confidence: 95%',
        ])

    def test_format_fingerprint_summary_handles_runtime_and_infrastructure(self):
        """format_fingerprint_summary() should render runtime and infrastructure rows."""

        plugin = self.make_plugin({
            'items': {},
            'report_items': {},
            'fingerprint': {
                'category': 'framework',
                'name': 'Next.js',
                'confidence': 96,
                'runtime': {'name': 'Node.js', 'confidence': 94},
                'infrastructure': {'provider': 'Vercel', 'confidence': 98},
            },
        })

        self.assertEqual(plugin.format_fingerprint_summary(), [
            'category: framework',
            'name: Next.js',
            'confidence: 96%',
            'runtime: Node.js',
            'runtime_confidence: 94%',
            'infrastructure: Vercel',
            'infrastructure_confidence: 98%',
        ])

    def test_process_uses_real_txt_module_and_records_fingerprint_summary(self):
        """process() should execute through txt.py and record report/fingerprint files."""

        self.assertEqual(self.plugin_cls.process.__code__.co_filename, self.module.__file__)

        plugin = self.make_plugin({
            'items': {
                'success': ['http://example.com/admin'],
                'bypass': ['http://example.com/bypass'],
                'failed': ['http://example.com/missing'],
            },
            'report_items': {
                'success': [
                    {'url': 'http://example.com/admin', 'size': '10B', 'code': '200'},
                ],
                'bypass': [
                    {
                        'url': 'http://example.com/bypass',
                        'size': '11B',
                        'code': '200',
                        'bypass_header': 'X-Original-URL',
                        'bypass_from_code': '403',
                        'bypass_to_code': '200',
                    },
                ],
                'failed': [
                    {'url': 'http://example.com/missing', 'size': '0B', 'code': '-'},
                ],
            },
            'fingerprint': {
                'category': 'framework',
                'name': 'Next.js',
                'confidence': 96,
                'runtime': {'name': 'Node.js', 'confidence': 94},
                'infrastructure': {'provider': 'Vercel', 'confidence': 98},
            },
        })

        recorded = []

        def record(target_dir, status, data, separator):
            """Capture record calls."""

            recorded.append((target_dir, status, data, separator))

        with patch.object(self.module.filesystem, 'clear') as clear_mock,                 patch.object(plugin, 'record', side_effect=record):
            self.plugin_cls.process(plugin)

        clear_mock.assert_called_once_with('/tmp/opendoor-txt-test', extension='.txt')
        statuses = [item[1] for item in recorded]
        self.assertEqual(statuses, ['success', 'bypass', 'fingerprint'])
        self.assertNotIn('failed', statuses)
        fingerprint_record = recorded[-1]
        self.assertIn('runtime: Node.js', fingerprint_record[2])
        self.assertIn('infrastructure: Vercel', fingerprint_record[2])

    def test_process_wraps_clear_errors(self):
        """process() should wrap filesystem clear failures."""

        plugin = self.make_plugin({'items': {}, 'report_items': {}})
        error = self.module.FileSystemError('boom')

        with patch.object(self.module.filesystem, 'clear', side_effect=error):
            with self.assertRaises(Exception) as ctx:
                self.plugin_cls.process(plugin)

        self.assertIn('boom', str(ctx.exception))

    def test_process_wraps_record_errors(self):
        """process() should wrap record failures."""

        plugin = self.make_plugin({
            'items': {'success': ['http://example.com/admin']},
            'report_items': {'success': [{'url': 'http://example.com/admin', 'size': '10B', 'code': '200'}]},
        })

        with patch.object(self.module.filesystem, 'clear'),                 patch.object(plugin, 'record', side_effect=Exception('record failed')):
            with self.assertRaises(Exception) as ctx:
                self.plugin_cls.process(plugin)

        self.assertIn('record failed', str(ctx.exception))

    def test_legacy_string_item_formatter_is_supported(self):
        """Inherited formatter should support legacy URL-only items."""

        plugin = self.make_plugin()

        self.assertEqual(
            plugin.format_report_item('http://example.com/legacy'),
            'http://example.com/legacy'
        )


if __name__ == '__main__':
    unittest.main()
