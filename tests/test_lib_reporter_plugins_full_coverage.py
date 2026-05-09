# -*- coding: utf-8 -*-

import copy
import importlib
import os
import unittest
from unittest.mock import patch

from src.lib.reporter.plugins.provider.provider import PluginProvider
from src.core.filesystem.exceptions import FileSystemError
from src.lib.reporter.plugins.html import HtmlReportPlugin, render_html_report
from src.lib.reporter.plugins.json import JsonReportPlugin
from src.lib.reporter.plugins.txt import TextReportPlugin

html_report = importlib.import_module('src.lib.reporter.plugins.html')

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
                patch('src.lib.reporter.plugins.html.render_html_report') as render_html_report_mock:
            render_html_report_mock.return_value = '<html>ok</html>'

            plugin = HtmlReportPlugin(self.target, source, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        payload = render_html_report_mock.call_args.args[1]
        self.assertEqual(payload['report_items'], self.rich_data['report_items'])
        self.assertEqual(source, self.rich_data)
        record_mock.assert_called_once_with('/tmp/reports', self.target, '<html>ok</html>')

    def test_html_process_handles_missing_items_key(self):
        """HtmlReportPlugin should build an empty report_items map when items are missing."""

        data = {'total': {'items': 0}}

        with patch('src.lib.reporter.plugins.html.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.html.filesystem.clear'), \
                patch('src.lib.reporter.plugins.html.render_html_report') as render_html_report_mock:
            render_html_report_mock.return_value = '<html>ok</html>'

            plugin = HtmlReportPlugin(self.target, data, directory='/custom/')
            with patch.object(plugin, 'record'):
                plugin.process()

        payload = render_html_report_mock.call_args.args[1]
        self.assertEqual(payload, {'total': {'items': 0}, 'report_items': {}})

    def test_html_process_wraps_record_filesystem_error(self):
        """HtmlReportPlugin should wrap FileSystemError raised during record."""

        with patch('src.lib.reporter.plugins.html.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.html.filesystem.clear'), \
                patch('src.lib.reporter.plugins.html.render_html_report') as render_html_report_mock:
            render_html_report_mock.return_value = '<html>ok</html>'

            plugin = HtmlReportPlugin(self.target, self.plain_data, directory='/custom/')
            with patch.object(plugin, 'record', side_effect=FileSystemError('boom')):
                with self.assertRaises(Exception):
                    plugin.process()

    def test_html_renderer_covers_empty_report_items_and_metadata(self):
        """HTML renderer should render empty findings and metadata blocks."""

        html = html_report.render_html_report('test.local', {
            'total': {},
            'items': {
                'success': [],
            },
            'report_items': {},
            'scanner': 'opendoor',
            'debug': True,
            'empty': None,
            'tags': ['a', 'b'],
            'nested': {'enabled': False},
        })

        self.assertIn('<!doctype html>', html)
        self.assertIn('OpenDoor Report', html)
        self.assertIn('No findings.', html)
        self.assertIn('Metadata', html)
        self.assertIn('opendoor', html)
        self.assertIn('true', html)
        self.assertIn('false', html)
        self.assertIn('<span class="badge">-</span>', html)

    def test_html_renderer_covers_status_groups_and_table_branches(self):
        """HTML renderer should render status buckets, links, codes, and nested values."""

        html = html_report.render_html_report('example.com', {
            'total': {
                'blocked': 1,
                'success': 2,
            },
            'report_items': {
                'success': [{
                    'url': 'https://example.com/admin',
                    'code': '200',
                    'size': '12KB',
                    'title': 'Admin <Panel>',
                    'content_type': 'text/html',
                    'redirect': 'https://example.com/login',
                    'waf': 'Cloudflare',
                    'waf_confidence': 92,
                    'bypass': True,
                    'details': {'source': 'unit'},
                    'notes': ['safe', 'escaped'],
                }],
                'redirect': [{
                    'url': 'http://example.com/old',
                    'code': '301',
                    'redirect': 'https://example.com/new',
                }],
                'blocked': [{
                    'url': 'https://example.com/private',
                    'code': '403',
                }],
                'failed': [{
                    'url': 'https://example.com/error',
                    'code': '500',
                }],
                'custom': [{
                    'url': 'ftp://example.com/not-linked',
                    'code': '-',
                    'value': None,
                }],
            },
        })

        self.assertIn('Summary', html)
        self.assertIn('Findings', html)
        self.assertIn('https://example.com/admin', html)
        self.assertIn('target="_blank"', html)
        self.assertIn('Admin &lt;Panel&gt;', html)
        self.assertIn('badge-success', html)
        self.assertIn('badge-warning', html)
        self.assertIn('badge-danger', html)
        self.assertIn('ftp://example.com/not-linked', html)
        self.assertIn('unit', html)
        self.assertIn('safe', html)

    def test_html_renderer_covers_plain_list_and_empty_status_items(self):
        """HTML renderer should render legacy plain lists and empty status buckets."""

        html = html_report.render_html_report('plain.local', {
            'total': {
                'items': 2,
            },
            'report_items': {
                'success': [
                    'http://plain.local/admin',
                    None,
                    True,
                    False,
                    {'nested': 'value'},
                    ['child'],
                ],
                'warning': [],
            },
        })

        self.assertIn('http://plain.local/admin', html)
        self.assertIn('No items in this bucket.', html)
        self.assertIn('<th>#</th><th>value</th>', html)
        self.assertIn('nested', html)
        self.assertIn('child', html)
        self.assertIn('true', html)
        self.assertIn('false', html)


    def test_html_renderer_helpers_should_cover_duplicate_columns_and_slugs(self):
        """HTML helper branches should handle duplicate keys and repeated slug separators."""

        self.assertEqual(
            html_report._get_total_finding_count({
                'success': ['one'],
                'metadata': {'not': 'a list'},
            }),
            1
        )
        self.assertEqual(
            html_report._get_columns([
                {'url': 'https://example.com/a', 'custom': 'one'},
                {'url': 'https://example.com/b', 'custom': 'two', 'extra': 'three'},
            ]),
            ['url', 'custom', 'extra']
        )
        self.assertEqual(
            html_report._get_status_dom_id('bad!! status'),
            'status-bad-status'
        )

    def test_html_renderer_covers_direct_private_render_helpers(self):
        """HTML renderer helpers should handle empty, unknown, and scalar branches."""

        self.assertEqual(html_report._render_value(None), '<span class="badge">-</span>')
        self.assertIn('empty', html_report._render_value({}))
        self.assertIn('empty', html_report._render_value([]))
        self.assertIn('plain', html_report._render_value('plain'))

        self.assertIn('badge-success', html_report._render_status_code('204'))
        self.assertIn('badge-success', html_report._render_status_code('302'))
        self.assertIn('badge-warning', html_report._render_status_code('404'))
        self.assertIn('badge-danger', html_report._render_status_code('500'))
        self.assertIn('badge', html_report._render_status_code('-'))

        self.assertEqual(html_report._get_status_badge_class('index'), 'badge badge-success')
        self.assertEqual(html_report._get_status_badge_class('indexof'), 'badge badge-success')
        self.assertEqual(html_report._get_status_badge_class('error'), 'badge badge-danger')
        self.assertEqual(html_report._get_status_badge_class('blocked'), 'badge badge-danger')
        self.assertEqual(html_report._get_status_badge_class('warning'), 'badge badge-warning')
        self.assertEqual(html_report._get_status_badge_class('redirect'), 'badge badge-warning')
        self.assertEqual(html_report._get_status_badge_class('unknown'), 'badge')

        self.assertEqual(html_report._get_value_class('url'), 'mono break')
        self.assertEqual(html_report._get_value_class('redirect'), 'mono break')
        self.assertEqual(html_report._get_value_class('content_type'), 'mono break')
        self.assertEqual(html_report._get_value_class('bypass_header'), 'mono break')
        self.assertEqual(html_report._get_value_class('bypass_value'), 'mono break')
        self.assertEqual(html_report._get_value_class('title'), 'break')

        self.assertTrue(html_report._is_http_url('http://example.com'))
        self.assertTrue(html_report._is_http_url('https://example.com'))
        self.assertFalse(html_report._is_http_url('ftp://example.com'))
        self.assertFalse(html_report._is_http_url(None))
        self.assertEqual(html_report._get_total_finding_count(None), 0)
        self.assertEqual(html_report._get_nested_summary('plain'), 'details')

        self.assertEqual(html_report._escape(None), '')
        self.assertEqual(html_report._escape('<x "y">'), '&lt;x &quot;y&quot;&gt;')

    def test_html_renderer_covers_column_order_and_metadata_filtering(self):
        """HTML renderer should keep preferred columns first and exclude noisy metadata."""

        columns = html_report._get_columns([
            {
                'custom': 'x',
                'url': 'https://example.com',
                'code': '200',
                'bypass_value': '/admin',
            },
            {
                'size': '1KB',
                'another': 'y',
            },
        ])

        self.assertEqual(columns[:4], ['url', 'code', 'size', 'bypass_value'])
        self.assertIn('custom', columns)
        self.assertIn('another', columns)

        metadata = html_report._get_metadata({
            'items': {},
            'report_items': {},
            'total': {},
            'scanner': 'opendoor',
        })

        self.assertEqual(metadata, {'scanner': 'opendoor'})

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

    def test_text_process_formats_header_bypass_metadata(self):
        """TextReportPlugin should include header-bypass evidence in bypass report lines."""

        data = {
            'items': {
                'bypass': ['http://example.com/admin'],
            },
            'report_items': {
                'bypass': [
                    {
                        'url': 'http://example.com/admin',
                        'code': '200',
                        'size': '90B',
                        'bypass': 'header',
                        'bypass_header': 'X-Original-URL',
                        'bypass_value': '/admin',
                        'bypass_from_code': '403',
                        'bypass_to_code': '200',
                    }
                ],
            },
        }

        with patch('src.lib.reporter.plugins.txt.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.txt.filesystem.clear'):
            plugin = TextReportPlugin(self.target, data, directory='/custom/')
            with patch.object(plugin, 'record') as record_mock:
                plugin.process()

        record_mock.assert_called_once_with(
            '/tmp/reports',
            'bypass',
            [
                'http://example.com/admin - 200 - 90B | '
                'bypass=header, header=X-Original-URL, value=/admin, 403->200'
            ],
            '\n'
        )

    def test_html_process_preserves_header_bypass_report_items(self):
            """HtmlReportPlugin should preserve header-bypass metadata inside report_items."""

            data = {
                'items': {
                    'bypass': ['http://example.com/admin'],
                },
                'report_items': {
                    'bypass': [
                        {
                            'url': 'http://example.com/admin',
                            'code': '200',
                            'size': '90B',
                            'bypass': 'header',
                            'bypass_header': 'X-Original-URL',
                            'bypass_value': '/admin',
                            'bypass_from_code': '403',
                            'bypass_to_code': '200',
                        }
                    ],
                },
            }

            with patch('src.lib.reporter.plugins.html.filesystem.makedir', return_value='/tmp/reports'), \
                    patch('src.lib.reporter.plugins.html.filesystem.clear'), \
                    patch('src.lib.reporter.plugins.html.render_html_report') as render_html_report_mock:
                render_html_report_mock.return_value = '<html>ok</html>'

                plugin = HtmlReportPlugin(self.target, data, directory='/custom/')
                with patch.object(plugin, 'record'):
                    plugin.process()

            payload = render_html_report_mock.call_args.args[1]

            self.assertEqual(payload['report_items']['bypass'][0]['bypass_header'], 'X-Original-URL')
            self.assertEqual(payload['report_items']['bypass'][0]['bypass_from_code'], '403')
            self.assertEqual(payload['report_items']['bypass'][0]['bypass_to_code'], '200')

    def test_json_process_preserves_header_bypass_payload(self):
            """JsonReportPlugin should serialize the original payload with header-bypass metadata."""

            data = {
                'items': {
                    'bypass': ['http://example.com/admin'],
                },
                'report_items': {
                    'bypass': [
                        {
                            'url': 'http://example.com/admin',
                            'code': '200',
                            'size': '90B',
                            'bypass': 'header',
                            'bypass_header': 'X-Original-URL',
                            'bypass_value': '/admin',
                            'bypass_from_code': '403',
                            'bypass_to_code': '200',
                        }
                    ],
                },
            }

            with patch('src.lib.reporter.plugins.json.filesystem.makedir', return_value='/tmp/reports'), \
                    patch('src.lib.reporter.plugins.json.helper.to_json', return_value='{"ok": true}') as to_json_mock, \
                    patch('src.lib.reporter.plugins.json.filesystem.clear'):
                plugin = JsonReportPlugin(self.target, data, directory='/custom/')
                with patch.object(plugin, 'record'):
                    plugin.process()

            to_json_mock.assert_called_once_with(data)

    def test_format_report_item_formats_waf_without_confidence(self):
        """PluginProvider.format_report_item() should format WAF metadata without confidence."""

        actual = PluginProvider.format_report_item({
            'url': 'https://example.com/login',
            'code': '403',
            'size': '25B',
            'waf': 'Cloudflare',
        })

        self.assertEqual(
            actual,
            'https://example.com/login - 403 - 25B - WAF: Cloudflare'
        )

    def test_format_report_item_formats_bypass_without_header_value_and_codes(self):
        """PluginProvider.format_report_item() should format minimal bypass metadata."""

        actual = PluginProvider.format_report_item({
            'url': 'https://example.com/admin',
            'code': '200',
            'size': '90B',
            'bypass': 'header',
        })

        self.assertEqual(
            actual,
            'https://example.com/admin - 200 - 90B | bypass=header'
        )

    def test_format_report_item_formats_bypass_with_only_transition_codes(self):
        """PluginProvider.format_report_item() should format bypass transition without header/value evidence."""

        actual = PluginProvider.format_report_item({
            'url': 'https://example.com/admin',
            'code': '200',
            'size': '90B',
            'bypass': 'header',
            'bypass_from_code': '403',
            'bypass_to_code': '200',
        })

        self.assertEqual(
            actual,
            'https://example.com/admin - 200 - 90B | bypass=header, 403->200'
        )

    def test_format_report_item_formats_bypass_without_transition_codes(self):
        """PluginProvider.format_report_item() should format header/value bypass metadata without transition codes."""

        actual = PluginProvider.format_report_item({
            'url': 'https://example.com/admin',
            'code': '200',
            'size': '90B',
            'bypass': 'header',
            'bypass_header': 'X-Original-URL',
            'bypass_value': '/admin',
        })

        self.assertEqual(
            actual,
            'https://example.com/admin - 200 - 90B | '
            'bypass=header, header=X-Original-URL, value=/admin'
        )

    def test_format_report_item_formats_full_bypass_evidence(self):
        """PluginProvider.format_report_item() should include extended bypass evidence fields."""

        actual = PluginProvider.format_report_item({
            'url': 'https://example.com/admin',
            'code': '200',
            'size': '90B',
            'bypass': 'path',
            'bypass_profile': 'offensive',
            'bypass_variant': 'double-encoded-trailing-slash',
            'bypass_value': '/admin%252f',
            'bypass_from_code': '403',
            'bypass_to_code': '200',
            'bypass_score': 100,
            'bypass_reasons': ['status-code-changed', 'blocked-status-cleared'],
        })

        self.assertEqual(
            actual,
            'https://example.com/admin - 200 - 90B | '
            'bypass=path, profile=offensive, variant=double-encoded-trailing-slash, '
            'value=/admin%252f, 403->200, score=100, '
            'reasons=status-code-changed;blocked-status-cleared'
        )

    def test_html_renderer_escapes_values_and_renders_pretty_table(self):
        """HTML renderer should escape values and render a standalone styled report."""

        html = render_html_report('example.com', {
            'total': {
                'success': 1,
                'items': 1,
            },
            'report_items': {
                'success': [{
                    'url': 'https://example.com/<admin>',
                    'code': '200',
                    'size': '12KB',
                    'waf': 'Cloudflare',
                }],
            },
        })

        self.assertIn('<!doctype html>', html)
        self.assertIn('OpenDoor Report', html)
        self.assertIn('report-table', html)
        self.assertIn('https://example.com/&lt;admin&gt;', html)
        self.assertIn('Cloudflare', html)
        self.assertNotIn('json2html', html)

    def test_html_renderer_should_include_interactive_controls_and_single_file_assets(self):
        """HTML renderer should keep reports standalone while adding interactive controls."""

        html = html_report.render_html_report('example.com', {
            'total': {
                'items': 2,
                'blocked': 1,
                'success': 1,
            },
            'report_items': {
                'blocked': [{
                    'url': 'https://example.com/private',
                    'code': '403',
                    'waf': 'Cloudflare',
                }],
                'success': [{
                    'url': 'https://example.com/admin',
                    'code': '200',
                    'title': 'Admin',
                }],
            },
            'fingerprint': {'name': 'WordPress'},
        })

        self.assertIn('id="summary"', html)
        self.assertIn('id="findings" data-report-findings', html)
        self.assertIn('id="metadata"', html)
        self.assertIn('data-report-search', html)
        self.assertIn('data-status-filter="all"', html)
        self.assertIn('data-status-filter="blocked"', html)
        self.assertIn('data-report-status="success"', html)
        self.assertIn('data-report-row', html)
        self.assertIn('data-row-search=', html)
        self.assertIn('data-report-url="https://example.com/admin"', html)
        self.assertIn('aria-controls="status-success"', html)
        self.assertIn('data-copy-status', html)
        self.assertIn('data-search-empty', html)
        self.assertIn('Copy visible URLs', html)
        self.assertIn('getVisibleUrls()', html)
        self.assertIn('scrollToActiveGroup()', html)
        self.assertIn('<script>', html)
        self.assertIn('<style>', html)
        self.assertNotIn('<script src=', html)
        self.assertNotIn('<link rel="stylesheet"', html)

    def test_html_renderer_should_make_plain_url_rows_searchable_and_copyable(self):
        """HTML renderer should expose plain URL rows to search and copy controls."""

        html = html_report.render_html_report('example.com', {
            'report_items': {
                'success': [
                    'https://example.com/gs_login.html',
                ],
            },
        })

        self.assertIn('data-report-url="https://example.com/gs_login.html"', html)
        self.assertIn('data-row-search="https://example.com/gs_login.html"', html)
        self.assertIn('getRowUrl(row)', html)
        self.assertIn('fallbackCopy(payload, markCopied, markFailed)', html)


    def test_html_renderer_should_render_nested_metadata_as_collapsible_json(self):
        """HTML renderer should avoid recursive metadata tables for nested values."""

        html = html_report.render_html_report('example.com', {
            'report_items': {
                'success': [{
                    'url': 'https://example.com/admin',
                    'code': '200',
                    'signals': [{'type': 'endpoint', 'value': '/admin'}],
                }],
            },
            'fingerprint': {
                'name': 'Bitrix',
                'signals': [{'type': 'header', 'value': 'x-powered-cms'}],
            },
        })

        self.assertIn('details-block', html)
        self.assertIn('nested-json', html)
        self.assertIn('2 fields', html)
        self.assertIn('&quot;name&quot;: &quot;Bitrix&quot;', html)
        self.assertIn('&quot;value&quot;: &quot;x-powered-cms&quot;', html)


if __name__ == '__main__':
    unittest.main()