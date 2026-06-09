# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, call

from urllib3.response import HTTPResponse

from src.core.http.plugins.response_plugin import ResponsePlugin
from src.core.http.response import Response

from src.core import helper
from src.lib import browser
from src.lib.browser.config import Config
from src.lib.browser.crawl import CrawlState


class TestBrowserCrawlRuntime(unittest.TestCase):

    def make_browser(self):
        """Create a browser instance with just enough runtime state for __http_request."""

        br = browser.__new__(browser)
        config = Config({
            'host': 'example.com',
            'port': 80,
            'reports': 'std',
            'crawl': True,
            'method': 'GET',
        })

        result = {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list(), 'filtered_items': []}
        response = MagicMock()
        response.handle.return_value = ('success', 'http://example.com/page', '42B', '200')
        response.debug_response_data.return_value = True
        response._response_plugins = []

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__result', result)
        setattr(br, '_Browser__report_item_keys', {})
        setattr(br, '_Browser__report_item_keys_result_id', id(result))
        setattr(br, '_Browser__visited_recursive', set())
        setattr(br, '_Browser__queued_recursive', set())
        setattr(br, '_Browser__crawl_state', CrawlState())
        setattr(br, '_Browser__response', response)
        setattr(br, '_Browser__debug', MagicMock())
        setattr(br, '_Browser__reader', MagicMock(get_ignored_list=MagicMock(return_value=[]), total_lines=10))
        setattr(br, '_Browser__pool', MagicMock(items_size=2, total_items_size=10))
        setattr(br, '_Browser__client', MagicMock())
        getattr(br, '_Browser__client').request.return_value = SimpleNamespace(
            data=b'<a href="/admin">Admin</a><a href="/admin#top">Duplicate</a><a href="/login">Login</a>',
            headers={'Content-Type': 'text/html'},
            status=200,
        )
        setattr(br, '_Browser__session_snapshot', None)
        setattr(br, '_Browser__session_dirty', False)
        setattr(br, '_Browser__session', None)
        setattr(br, '_Browser__pending_requests', {})
        setattr(br, '_Browser__completed_requests', set())
        setattr(br, '_Browser__transient_request_keys', set())
        setattr(br, '_Browser__seen_scan_urls', set())
        setattr(br, '_Browser__transport_failure_lock', MagicMock())
        setattr(br, '_Browser__transport_failure_streak', 0)
        setattr(br, '_Browser__transport_failures_skipped', 0)
        setattr(br, '_Browser__transport_failure_summary_emitted', False)
        setattr(br, '_Browser__shared_cookie_header', '')
        setattr(br, '_Browser__active_sniffer_names', set())
        setattr(br, '_Browser__open_redirect_probe', None)
        setattr(br, '_Browser__shadow_probe', None)
        setattr(br, '_Browser__calibration', None)
        setattr(br, '_Browser__waf_safe_active', False)
        setattr(br, '_Browser__waf_safe_lock', MagicMock())
        setattr(br, '_Browser__waf_safe_delay', 0.0)
        setattr(br, '_Browser__waf_safe_next_at', 0.0)
        setattr(br, '_Browser__waf_safe_recovery_count', 0)
        setattr(br, '_Browser__waf_safe_block_events', [])
        setattr(br, '_Browser__waf_guard_lock', MagicMock())
        setattr(br, '_Browser__waf_guard_classified', 0)
        setattr(br, '_Browser__waf_guard_blocked', 0)
        setattr(br, '_Browser__waf_guard_stopped', False)

        # Keep this runtime test focused on crawl queue integration, not adjacent sniffers/guards.
        setattr(br, '_Browser__match_dns_wildcard_response', MagicMock(return_value=None))
        setattr(br, '_Browser__match_calibrated_response', MagicMock(return_value=None))
        setattr(br, '_Browser__match_js_cookie_reload_challenge', MagicMock(return_value=None))
        setattr(br, '_Browser__collect_passive_sniffer_findings', MagicMock(return_value=[]))
        setattr(br, '_Browser__should_suppress_primary_response', MagicMock(return_value=False))
        setattr(br, '_Browser__activate_waf_safe_mode', MagicMock())
        setattr(br, '_Browser__is_explicit_waf_safe_activation_detection', MagicMock(return_value=False))
        setattr(br, '_Browser__is_explicit_waf_safe_backoff_signal', MagicMock(return_value=False))
        setattr(br, '_Browser__update_waf_safe_backoff', MagicMock())
        setattr(br, '_Browser__record_waf_guard_response', MagicMock(return_value=False))
        setattr(br, '_Browser__probe_header_bypass', MagicMock())
        setattr(br, '_Browser__run_inline_active_sniffers', MagicMock())
        setattr(br, '_Browser__emit_passive_sniffer_findings', MagicMock())
        setattr(br, '_Browser__run_deferred_active_sniffers', MagicMock())
        setattr(br, '_Browser__should_suspend_recursive_expansion', MagicMock(return_value=True))

        return br

    def test_http_request_enqueues_unique_crawl_candidates_once(self):
        """Allowed non-crawl responses should enqueue unique same-origin crawl URLs once."""

        br = self.make_browser()

        br._Browser__http_request('http://example.com/page')

        pool = getattr(br, '_Browser__pool')
        pool.extend_total_items.assert_called_once_with(2)
        pool.add.assert_has_calls([
            call(getattr(br, '_Browser__http_request'), 'http://example.com/admin', 0, 'crawl', 'http://example.com/page'),
            call(getattr(br, '_Browser__http_request'), 'http://example.com/login', 0, 'crawl', 'http://example.com/page'),
        ])
        self.assertEqual(getattr(br, '_Browser__crawl_state').enqueued, 2)

    def test_http_request_does_not_recrawl_crawl_owned_response(self):
        """Crawl-owned requests should not expand the queue again in the one-hop MVP."""

        br = self.make_browser()

        br._Browser__http_request('http://example.com/admin', request_source='crawl')

        pool = getattr(br, '_Browser__pool')
        pool.extend_total_items.assert_not_called()
        pool.add.assert_not_called()

    def test_http_request_does_not_crawl_forbidden_response_templates(self):
        """Forbidden/error templates should not seed crawl noise from shared HTML navigation."""

        br = self.make_browser()
        getattr(br, '_Browser__response').handle.return_value = (
            'forbidden',
            'http://example.com/.env',
            '751KB',
            '403',
        )
        getattr(br, '_Browser__client').request.return_value = SimpleNamespace(
            data=b'<a href="/css/"></a><a href="/temp/"></a>',
            headers={'Content-Type': 'text/html'},
            status=403,
        )

        br._Browser__http_request('http://example.com/.env')

        pool = getattr(br, '_Browser__pool')
        pool.extend_total_items.assert_not_called()
        pool.add.assert_not_called()
        self.assertEqual(getattr(br, '_Browser__crawl_state').enqueued, 0)

    def test_crawl_source_response_allows_only_success_2xx(self):
        """Crawl queue enrichment should be limited to successful primary responses."""

        self.assertTrue(browser._Browser__is_crawl_source_response(('success', 'http://example.com/', '1KB', '200')))
        self.assertTrue(browser._Browser__is_crawl_source_response(('success', 'http://example.com/', '1KB', '204')))
        self.assertFalse(browser._Browser__is_crawl_source_response(('forbidden', 'http://example.com/.env', '1KB', '403')))
        self.assertFalse(browser._Browser__is_crawl_source_response(('redirect', 'http://example.com/', '1KB', '302')))
        self.assertFalse(browser._Browser__is_crawl_source_response(('success', 'http://example.com/', '1KB', 'not-a-code')))

    def test_http_request_passes_crawl_progress_marker_for_crawled_item(self):
        """Crawl-owned response progress should include the crawl source marker and accepted delta."""

        br = self.make_browser()
        getattr(br, '_Browser__crawl_state').reserve('http://example.com/admin')

        br._Browser__http_request('http://example.com/admin', request_source='crawl')

        getattr(br, '_Browser__response').debug_response_data.assert_called_once()
        _, kwargs = getattr(br, '_Browser__response').debug_response_data.call_args
        self.assertEqual(kwargs.get('request_source'), 'crawl')
        self.assertEqual(kwargs.get('crawl_enqueued_size'), 1)
        self.assertEqual(kwargs.get('base_total_size'), 10)

    def test_crawl_owned_response_runs_malware_sniffer_and_preserves_bucket(self):
        """Crawl-owned responses should still pass through enabled sniffers and normal buckets."""

        br = self.make_browser()
        response_handler = getattr(br, '_Browser__response')
        response_handler._response_plugins = [ResponsePlugin.load('malware')]
        response_handler.handle.return_value = ('success', 'http://example.com/load.js', '42B', '200')
        getattr(br, '_Browser__client').request.return_value = SimpleNamespace(
            data=b'<html><title>WSO Shell</title><body>FilesMan</body></html>',
            headers={'Content-Type': 'application/javascript'},
            status=200,
        )
        setattr(
            br,
            '_Browser__collect_passive_sniffer_findings',
            browser._Browser__collect_passive_sniffer_findings.__get__(br, browser),
        )
        setattr(
            br,
            '_Browser__emit_passive_sniffer_findings',
            browser._Browser__emit_passive_sniffer_findings.__get__(br, browser),
        )
        setattr(br, '_Browser__emit_sniffer_finding', MagicMock(return_value=True))

        br._Browser__http_request('http://example.com/load.js', request_source='crawl')

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['items']['malware'], ['http://example.com/load.js'])
        self.assertEqual(
            result['report_items']['malware'][0]['malware_detection']['subtype'],
            'webshell',
        )
        self.assertEqual(
            result['report_items']['malware'][0]['passive_finding']['bucket'],
            'malware',
        )

    def test_crawl_ignore_extensions_blocks_static_scripts_before_enqueue(self):
        """Ignored extensions should prevent crawl-discovered assets from reaching sniffer processing."""

        br = self.make_browser()
        config = getattr(br, '_Browser__config')
        setattr(config, '_is_ignore_extension_filter', True)
        setattr(config, '_ignore_extensions', ['js'])
        response = SimpleNamespace(
            data=b'<script src="/load.js"></script><a href="/form.php"></a>',
            headers={'Content-Type': 'text/html'},
        )

        queued = br._Browser__enqueue_crawl_candidates(
            response,
            ('success', 'http://example.com/page', '1KB', '200'),
        )

        self.assertEqual(queued, 1)
        self.assertEqual(getattr(br, '_Browser__crawl_state').skipped, 1)
        added_urls = [call_args.args[1] for call_args in getattr(br, '_Browser__pool').add.call_args_list]
        self.assertEqual(added_urls, ['http://example.com/form.php'])
        self.assertNotIn('http://example.com/load.js', added_urls)

    def test_crawl_owned_html_page_does_not_enqueue_second_hop_script(self):
        """One-hop crawl should not follow scripts discovered inside crawl-owned pages."""

        br = self.make_browser()
        getattr(br, '_Browser__client').request.return_value = SimpleNamespace(
            data=b'<html><script src="/load.js"></script></html>',
            headers={'Content-Type': 'text/html'},
            status=200,
        )
        getattr(br, '_Browser__response').handle.return_value = (
            'success',
            'http://example.com/form.php',
            '42B',
            '200',
        )

        br._Browser__http_request('http://example.com/form.php', request_source='crawl')

        getattr(br, '_Browser__pool').extend_total_items.assert_not_called()
        getattr(br, '_Browser__pool').add.assert_not_called()
        self.assertEqual(getattr(br, '_Browser__crawl_state').enqueued, 0)

    def test_register_pending_request_stores_crawl_source_for_sessions(self):
        """Session-enabled pending items should retain crawl source metadata for resume UI."""

        br = self.make_browser()
        setattr(getattr(br, '_Browser__config'), '_session_save', '/tmp/session.json')

        self.assertTrue(br._Browser__register_pending_request(
            'http://example.com/admin',
            0,
            source='crawl',
            source_url='http://example.com/page',
        ))

        pending = getattr(br, '_Browser__pending_requests')
        self.assertEqual(pending['0::http://example.com/admin']['source'], 'crawl')
        self.assertEqual(pending['0::http://example.com/admin']['source_url'], 'http://example.com/page')

    def test_resume_pending_requests_preserves_crawl_source_args(self):
        """Restored crawl pending items should be re-enqueued with source metadata."""

        br = self.make_browser()
        setattr(br, '_Browser__pending_requests', {
            '0::http://example.com/admin': {
                'url': 'http://example.com/admin',
                'depth': 0,
                'source': 'crawl',
                'source_url': 'http://example.com/page',
            }
        })

        br._Browser__resume_pending_requests()

        getattr(br, '_Browser__pool').add.assert_called_once_with(
            getattr(br, '_Browser__http_request'),
            'http://example.com/admin',
            0,
            'crawl',
            'http://example.com/page',
        )


    def test_crawl_private_guards_handle_disabled_state_and_bad_payloads(self):
        """Crawl helpers should fail closed when state or response data is unavailable."""

        br = self.make_browser()
        setattr(br, '_Browser__crawl_state', None)

        self.assertFalse(br._Browser__is_crawl_enabled())
        self.assertEqual(br._Browser__crawl_progress_enqueued(), 0)
        self.assertEqual(br._Browser__crawl_progress_processed(), 0)
        self.assertEqual(br._Browser__record_crawl_processed_request(), 0)
        self.assertEqual(br._Browser__enqueue_crawl_candidates(SimpleNamespace(data=b''), None), 0)

        setattr(br, '_Browser__crawl_state', CrawlState())
        self.assertEqual(br._Browser__enqueue_crawl_candidates(SimpleNamespace(data=b''), ()), 0)

    def test_crawl_response_header_handles_mapping_like_and_invalid_headers(self):
        """Crawl header lookup should support mapping-like objects and fail closed on invalid containers."""

        br = self.make_browser()

        mapping_response = SimpleNamespace(headers=[('content-type', 'text/html')])
        self.assertEqual(br._Browser__response_header(mapping_response, 'Content-Type'), 'text/html')

        invalid_response = SimpleNamespace(headers=object())
        self.assertIsNone(br._Browser__response_header(invalid_response, 'Content-Type'))

    def test_crawl_enqueue_counts_state_duplicates_limits_and_pending_rejects(self):
        """Crawl enqueue should account for dedup, limit and global pending rejections."""

        br = self.make_browser()
        response = SimpleNamespace(
            data=(
                b'<a href="/admin"></a>'
                b'<a href="/limit"></a>'
                b'<a href="/pending"></a>'
            ),
            headers={'Content-Type': 'text/html'},
        )
        state = CrawlState(max_enqueued=1)
        state.reserve('http://example.com/admin')
        setattr(br, '_Browser__crawl_state', state)

        self.assertEqual(br._Browser__enqueue_crawl_candidates(response, ('success', 'http://example.com/page', '1KB', '200')), 0)
        self.assertEqual(state.duplicates, 1)
        self.assertEqual(state.skipped_limit, 2)
        getattr(br, '_Browser__pool').add.assert_not_called()

        br = self.make_browser()
        response = SimpleNamespace(data=b'<a href="/pending"></a>', headers={'Content-Type': 'text/html'})
        setattr(br, '_Browser__register_pending_request', MagicMock(return_value=False))

        self.assertEqual(br._Browser__enqueue_crawl_candidates(response, ('success', 'http://example.com/page', '1KB', '200')), 0)
        self.assertEqual(getattr(br, '_Browser__crawl_state').duplicates, 1)
        getattr(br, '_Browser__pool').add.assert_not_called()

    def test_crawl_private_ignores_extension_filter_when_disabled(self):
        """Crawl ignore-extension helper should return an empty list when the filter is disabled."""

        br = self.make_browser()
        setattr(getattr(br, '_Browser__config'), '_is_ignore_extension_filter', False)
        setattr(getattr(br, '_Browser__config'), '_ignore_extensions', ['js'])

        self.assertEqual(br._Browser__crawl_ignore_extensions(), [])

    def test_crawl_record_processed_handles_legacy_state_without_method(self):
        """Processed accounting should fail closed for legacy crawl-state-like objects."""

        br = self.make_browser()
        setattr(br, '_Browser__crawl_state', SimpleNamespace(enqueued=0, processed=0))

        self.assertEqual(br._Browser__record_crawl_processed_request(), 0)


    def test_runtime_diagnostics_reports_crawl_discovered_consumed_and_pending(self):
        """Runtime diagnostics should show crawl counters when crawl mode is active."""

        br = self.make_browser()
        crawl_state = getattr(br, '_Browser__crawl_state')
        crawl_state.reserve('http://example.com/admin')
        crawl_state.reserve('http://example.com/login')
        crawl_state.reserve('http://example.com/account')
        crawl_state.record_processed()
        crawl_state.record_processed()
        crawl_state.skip_duplicate('http://example.com/login')
        setattr(br, '_Browser__pool', SimpleNamespace(
            total_items_size=13,
            items_size=12,
            submitted_size=12,
            workers_size=1,
        ))
        setattr(br, '_Browser__reader', SimpleNamespace(total_lines=10))
        setattr(br, '_Browser__debug', SimpleNamespace(is_scan_debug=lambda: False))
        setattr(br, '_Browser__runtime_started_at', None)
        setattr(br, '_Browser__runtime_active_seconds_offset', 0.0)
        setattr(br, '_Browser__pre_request_skipped', 0)
        setattr(br, '_Browser__transport_failure_lock', MagicMock())
        setattr(br, '_Browser__transport_failures_skipped', 0)
        setattr(br, '_Browser__traffic_response_body_bytes', 2048)
        setattr(br, '_Browser__traffic_response_header_bytes', 128)
        setattr(br, '_Browser__traffic_requests', 12)

        rendered = br._Browser__format_runtime_diagnostics(status='completed')

        self.assertIn('| crawl       | 3 discovered, 2 consumed, 1 pending, 1 duplicate, 0 skipped |', rendered)
        self.assertIn('| traffic     | response bodies 2.0 KB, headers 128 B, requests 12', rendered)


class TestResponseCrawlProgressMetadata(unittest.TestCase):
    """Crawl progress metadata coverage for deferred response rendering."""

    def test_debug_response_data_forwards_crawl_progress_metadata(self):
        """Deferred runtime rendering should preserve crawl progress metadata for progress output."""

        cfg = SimpleNamespace(
            is_sniff=False,
            sniffers=[],
            SUBDOMAINS_SCAN='subdomains',
            scan='directories',
        )
        debug = SimpleNamespace(
            level=0,
            debug_request_uri=MagicMock(),
            debug_classification=MagicMock(),
        )
        response_handler = Response(cfg, debug, tpl=MagicMock())

        response_handler.debug_response_data(
            ('success', 'http://example.com/admin', '1KB', '200'),
            'http://example.com/admin',
            5,
            10,
            HTTPResponse(status=200, body=b'ok', headers={}),
            request_source='crawl',
            crawl_enqueued_size=3,
            crawl_processed_size=2,
            base_total_size=4,
        )

        kwargs = debug.debug_request_uri.call_args.kwargs
        self.assertEqual(kwargs['request_source'], 'crawl')
        self.assertEqual(kwargs['crawl_enqueued_size'], 3)
        self.assertEqual(kwargs['crawl_processed_size'], 2)
        self.assertEqual(kwargs['base_total_size'], 4)
        debug.debug_classification.assert_called_once()


if __name__ == '__main__':
    unittest.main()
