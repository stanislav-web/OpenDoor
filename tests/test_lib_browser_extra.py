# -*- coding: utf-8 -*-

import io
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core import ProxyRequestError, helper
from src.lib.browser.browser import Browser
from src.lib.browser.exceptions import BrowserError


class TestBrowserExtra(unittest.TestCase):
    """Extra coverage for Browser branches."""

    def make_browser(self, **config_overrides):
        """Create Browser via __new__ with minimal runtime state."""

        br = Browser.__new__(Browser)

        config = {
            'is_waf_safe_mode': True,
            'is_waf_detect': True,
            'is_session_enabled': False,
            'is_response_filtering': False,
            'is_recursive': True,
            'recursive_depth': 2,
            'recursive_status': ['200', '403'],
            'recursive_exclude': [],
            'DEFAULT_SCAN': 'directories',
            'scan': 'directories',
            'host': 'example.com',
            'scheme': 'http://',
            'is_ssl': False,
            'port': 80,
            'prefix': '',
            'reports': ['std'],
            'proxy': '',
            'headers': [],
            'cookies': [],
            'raw_request': None,
            'request_body': None,
            'accept_cookies': False,
            'keep_alive': False,
            'is_fingerprint': False,
            'wordlist': None,
            'reports_dir': None,
            'is_random_user_agent': False,
            'is_random_list': False,
            'extensions': [],
            'ignore_extensions': [],
            'sniffers': [],
            'include_status': [],
            'exclude_status': [],
            'exclude_size': [],
            'exclude_size_range': [],
            'match_text': [],
            'exclude_text': [],
            'match_regex': [],
            'exclude_regex': [],
            'min_response_length': None,
            'max_response_length': None,
            'threads': 1,
            'delay': 0,
            'timeout': 30,
            'retries': 1,
            'debug': 0,
            'is_builtin_proxy_pool': False,
            'is_external_proxy_list': False,
            'proxy_list': '',
            'requested_method': 'HEAD',
            'session_save': None,
            'session_autosave_sec': 20,
            'session_autosave_items': 200,
        }
        config.update(config_overrides)

        setattr(br, '_Browser__config', SimpleNamespace(**config))
        setattr(br, '_Browser__debug', MagicMock())
        setattr(br, '_Browser__client', MagicMock())
        setattr(br, '_Browser__reader', SimpleNamespace(
            total_lines=3,
            get_ignored_list=MagicMock(return_value=[]),
            get_lines=MagicMock(),
            get_user_agents=MagicMock(return_value=['UA']),
            get_proxies=MagicMock(return_value=[]),
        ))
        setattr(br, '_Browser__response', SimpleNamespace(
            handle=MagicMock(),
            waf_detection=None,
        ))
        setattr(br, '_Browser__pool', SimpleNamespace(
            items_size=1,
            total_items_size=1,
            size=0,
            workers_size=1,
            add=MagicMock(),
            join=MagicMock(),
            extend_total_items=MagicMock(),
            is_started=True,
        ))
        setattr(br, '_Browser__visited_recursive', set())
        setattr(br, '_Browser__queued_recursive', set())
        setattr(br, '_Browser__result', {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
        })
        setattr(br, '_Browser__session_lock', __import__('threading').RLock())
        setattr(br, '_Browser__session', None)
        setattr(br, '_Browser__session_dirty', False)
        setattr(br, '_Browser__completed_requests', set())
        setattr(br, '_Browser__pending_requests', {})
        setattr(br, '_Browser__processed_offset', 0)
        setattr(br, '_Browser__session_snapshot', None)
        setattr(br, '_Browser__waf_safe_lock', __import__('threading').RLock())
        setattr(br, '_Browser__waf_safe_active', False)
        setattr(br, '_Browser__waf_safe_next_at', 0.0)
        setattr(br, '_Browser__waf_safe_delay', 0.75)
        setattr(br, '_Browser__waf_safe_vendor', None)
        setattr(br, '_Browser__waf_safe_confidence', None)
        setattr(br, '_Browser__waf_safe_block_events', [])

        return br

    def test_render_fingerprint_bar_clamps_values(self):
        """Browser should render a bounded fingerprint progress bar."""

        self.assertEqual(Browser._Browser__render_fingerprint_bar(0, 4, width=4), '[----] 0.0%')
        self.assertEqual(Browser._Browser__render_fingerprint_bar(2, 4, width=4), '[##--] 50.0%')
        self.assertEqual(Browser._Browser__render_fingerprint_bar(9, 4, width=4), '[####] 100.0%')
        self.assertEqual(Browser._Browser__render_fingerprint_bar(-1, 0, width=4), '[----] 0.0%')

    def test_fingerprint_should_abort_on_standalone_proxy_error(self):
        """Browser.fingerprint() should fail fast when the explicit proxy is unavailable."""

        br = self.make_browser(is_fingerprint=True, is_standalone_proxy=True)
        detector = MagicMock()
        detector.detect.side_effect = ProxyRequestError(
            'Proxy socks5://127.0.0.1:9050 unavailable after retry for /: connection refused'
        )

        with patch('src.lib.browser.browser.Fingerprint', return_value=detector), \
                patch('src.lib.browser.browser.tpl.info'):
            with self.assertRaises(BrowserError) as context:
                br.fingerprint()

        self.assertIn('connection refused', str(context.exception))

    def test_calibrate_should_abort_on_standalone_proxy_error(self):
        """Browser.calibrate() should not keep probing when the explicit proxy is unavailable."""

        br = self.make_browser(
            is_auto_calibrate=True,
            is_standalone_proxy=True,
            calibration_samples=1,
            calibration_threshold=0.85,
            SUBDOMAINS_SCAN='subdomains',
        )
        client = MagicMock()
        client.request.side_effect = ProxyRequestError(
            'Proxy socks5://127.0.0.1:9050 unavailable after retry for /: connection refused'
        )
        setattr(br, '_Browser__client', client)

        with patch('src.lib.browser.browser.tpl.info'):
            with self.assertRaises(BrowserError) as context:
                br.calibrate()

        self.assertEqual(client.request.call_count, 1)
        self.assertIn('connection refused', str(context.exception))

    def test_fingerprint_progress_writes_line_without_final_newline(self):
        """Browser.__fingerprint_progress() should rotate intermediate progress in-place."""

        browser = object.__new__(Browser)
        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=120)):
                browser._Browser__fingerprint_progress(1, 4, 'root')

        output = stdout.getvalue()

        self.assertIn(chr(13), output)
        self.assertIn('Fingerprint [', output)
        self.assertIn('25.0%', output)
        self.assertIn('root', output)
        self.assertNotIn(chr(10), output)
        self.assertTrue(getattr(browser, '_Browser__fingerprint_progress_active'))
        self.assertGreater(getattr(browser, '_Browser__fingerprint_progress_last_length'), 0)

    def test_fingerprint_progress_writes_final_newline(self):
        """Browser.__fingerprint_progress() should persist only the final done line."""

        browser = object.__new__(Browser)
        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=120)):
                with patch('src.lib.browser.browser.tpl.info') as info_mock:
                    browser._Browser__fingerprint_progress(3, 4, 'analyze')
                    browser._Browser__fingerprint_progress(4, 4, 'done')

        self.assertFalse(getattr(browser, '_Browser__fingerprint_progress_active'))
        self.assertEqual(getattr(browser, '_Browser__fingerprint_progress_last_length'), 0)

        info_mock.assert_called_once()
        message = info_mock.call_args.kwargs.get('msg')
        self.assertIn('Fingerprint [', message)
        self.assertIn('100.0%', message)
        self.assertIn('done', message)
    def test_render_fingerprint_summary_lines_includes_stack_and_security_posture(self):
        """Browser should build compact post-fingerprint summary lines."""

        fingerprint = {
            'name': 'WordPress',
            'runtime': {'name': 'PHP'},
            'infrastructure': {'provider': 'Cloudflare'},
            'security_headers': {
                'hsts': {'grade': 'preload-ready'},
            },
        }

        lines = Browser._Browser__render_fingerprint_summary_lines(fingerprint)

        self.assertEqual(lines, [
            'Web stack: WordPress | PHP | Cloudflare',
            'Security posture: HSTS preload-ready',
        ])

    def test_render_fingerprint_summary_lines_handles_missing_metadata(self):
        """Browser should keep compact summary safe when optional metadata is absent."""

        lines = Browser._Browser__render_fingerprint_summary_lines({'name': 'Unknown custom stack'})

        self.assertEqual(lines, [
            'Web stack: Unknown custom stack | unknown',
            'Security posture: unknown',
        ])

    def test_request_with_waf_safe_mode_active_without_sleep(self):
        """Browser should serialize through safe mode without sleeping when slot is already available."""

        br = self.make_browser()
        br._Browser__client.request.return_value = 'ok'
        br._Browser__waf_safe_active = True
        br._Browser__waf_safe_next_at = 10.0

        with patch('src.lib.browser.browser.time.monotonic', side_effect=[10.5, 10.6]), \
                patch('src.lib.browser.browser.time.sleep') as sleep_mock:
            actual = br._Browser__request_with_waf_safe_mode('http://example.com')

        self.assertEqual(actual, 'ok')
        sleep_mock.assert_not_called()
        self.assertEqual(br._Browser__waf_safe_next_at, 11.35)

    def test_activate_waf_safe_mode_returns_when_safe_mode_disabled(self):
        """Browser should not activate safe mode when the feature is disabled."""

        br = self.make_browser(is_waf_safe_mode=False)

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__activate_waf_safe_mode({'name': 'Cloudflare', 'confidence': 92})

        self.assertFalse(br._Browser__waf_safe_active)
        warning_mock.assert_not_called()

    def test_activate_waf_safe_mode_returns_for_invalid_detection(self):
        """Browser should ignore non-dict WAF detections."""

        br = self.make_browser()

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__activate_waf_safe_mode('bad')

        self.assertFalse(br._Browser__waf_safe_active)
        warning_mock.assert_not_called()

    def test_activate_waf_safe_mode_does_not_warn_twice(self):
        """Browser should not re-activate or re-warn when safe mode is already active."""

        br = self.make_browser()
        br._Browser__waf_safe_active = True

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__activate_waf_safe_mode({'name': 'Cloudflare', 'confidence': 92})

        warning_mock.assert_not_called()

    def test_activate_waf_safe_mode_counts_non_immediate_blocks(self):
        """Browser should defer safe mode for isolated ordinary WAF blocks."""

        br = self.make_browser()

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__activate_waf_safe_mode({'name': 'Cloudflare', 'confidence': 92})

        self.assertFalse(br._Browser__waf_safe_active)
        self.assertEqual(len(br._Browser__waf_safe_block_events), 1)
        warning_mock.assert_not_called()

    def test_http_request_records_ignored_when_response_is_filtered_out(self):
        """Browser should classify filtered responses as ignored."""

        br = self.make_browser(is_response_filtering=True)
        br._Browser__client.request.return_value = SimpleNamespace(data=b'body', headers={})
        br._Browser__response.handle.return_value = ('success', 'http://example.com/admin', '10B', '200')

        with patch.object(Browser, '_Browser__is_response_allowed', return_value=False):
            br._Browser__http_request('http://example.com/admin', depth=0)

        self.assertEqual(br._Browser__result['items']['ignored'], ['http://example.com/admin'])

    def test_is_response_allowed_rejects_excluded_status(self):
        """Browser should reject statuses from exclude-status filters."""

        br = self.make_browser(
            is_response_filtering=True,
            include_status=[],
            exclude_status=['403'],
        )

        response = SimpleNamespace(data=b'', headers={'Content-Length': '0'})
        allowed = br._Browser__is_response_allowed(response, ('forbidden', 'http://example.com', '0B', '403'))

        self.assertFalse(allowed)

    def test_should_expand_recursively_allows_non_excluded_extension(self):
        """Browser recursive expansion should allow files with extensions outside the exclude list."""

        br = self.make_browser(recursive_exclude=['jpg', 'png'])

        actual = br._Browser__should_expand_recursively('200', 'http://example.com/admin.php', 0)

        self.assertTrue(actual)

    def test_enqueue_recursive_children_skips_when_loader_produces_no_urls(self):
        """Browser should not expand totals or enqueue work when recursive loader yields no child URLs."""

        br = self.make_browser()
        br._Browser__reader.get_lines.side_effect = lambda params, loader: loader([])

        with patch('src.lib.browser.browser.tpl.debug') as debug_mock:
            br._Browser__enqueue_recursive_children('http://example.com/panel', 0)

        br._Browser__pool.extend_total_items.assert_not_called()
        br._Browser__pool.add.assert_not_called()
        debug_mock.assert_not_called()

    def test_enqueue_recursive_children_does_not_add_when_request_already_registered(self):
        """Browser should skip pool.add when child request is already registered."""

        br = self.make_browser()
        br._Browser__reader.get_lines.side_effect = lambda params, loader: loader(['http://example.com/admin'])
        with patch.object(Browser, '_Browser__register_pending_request', return_value=False):
            br._Browser__enqueue_recursive_children('http://example.com/panel', 0)

        br._Browser__pool.add.assert_not_called()

    def test_add_urls_skips_pool_add_when_request_registration_returns_false(self):
        """Browser _add_urls should tolerate duplicate or already tracked items."""

        br = self.make_browser()
        with patch.object(Browser, '_Browser__is_ignored', return_value=False), \
                patch.object(Browser, '_Browser__register_pending_request', return_value=False):
            br._add_urls(['http://example.com/admin'])

        br._Browser__pool.add.assert_not_called()
        br._Browser__pool.join.assert_called_once()

    def test_catch_report_data_supports_partial_waf_metadata(self):
        """Browser should persist partial WAF metadata without requiring all fields."""

        br = self.make_browser()
        br._Browser__catch_report_data(
            'blocked',
            'http://example.com/login',
            '10B',
            '403',
            metadata={'confidence': 92}
        )

        self.assertEqual(
            br._Browser__result['report_items']['blocked'],
            [{'url': 'http://example.com/login', 'size': '10B', 'code': '403', 'waf_confidence': 92}]
        )

    def test_export_targets_omits_port_when_missing(self):
        """Browser should export target without port when port is None."""

        br = self.make_browser(port=None)

        actual = br._Browser__export_targets()

        self.assertEqual(actual, [{'host': 'example.com', 'scheme': 'http://', 'ssl': False}])

    def test_save_session_returns_when_manager_is_missing(self):
        """Browser should quietly skip session save when session manager is absent."""

        br = self.make_browser(is_session_enabled=True)
        br._Browser__session = None

        br._Browser__save_session(reason='items', force=False)

        self.assertFalse(br._Browser__session_dirty)

    def test_resume_pending_requests_bumps_total_items_size(self):
        """Browser should grow total-items size when restored pending requests exceed current total."""

        br = self.make_browser()
        br._Browser__processed_offset = 5
        br._Browser__pending_requests = {
            '0::http://example.com/a': {'url': 'http://example.com/a', 'depth': 0},
            '0::http://example.com/b': {'url': 'http://example.com/b', 'depth': 0},
        }
        br._Browser__pool.total_items_size = 1

        br._Browser__resume_pending_requests()

        self.assertEqual(br._Browser__pool.total_items_size, 7)
        self.assertEqual(br._Browser__pool.add.call_count, 2)


    def test_activate_waf_safe_mode_uses_tpl_warning_key(self):
        """Browser should announce safe mode activation through tpl key-based warning."""

        br = self.make_browser()

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__activate_waf_safe_mode({'name': 'Cloudflare', 'confidence': 92}, immediate=True)

        warning_mock.assert_called_once_with(
            key='waf_safe_mode_activated',
            vendor='Cloudflare',
            confidence=92,
            delay=0.75
        )


    def test_start_request_provider_reuses_shared_cookies_for_new_scan_client(self):
        """Browser should apply accepted cookies to a recreated scan request provider."""

        br = self.make_browser(accept_cookies=True, is_proxy=False)
        old_client = MagicMock()
        old_client._push_cookies.return_value = 'session_id=abc123'
        setattr(br, '_Browser__client', old_client)
        setattr(br, '_Browser__shared_cookie_header', None)

        new_client = MagicMock()
        with patch('src.lib.browser.browser.request_http', return_value=new_client):
            br._Browser__start_request_provider()

        old_client._push_cookies.assert_called_once()
        new_client.add_header.assert_called_once_with('Cookie', 'session_id=abc123')
        self.assertEqual(getattr(new_client, '_cookies'), 'session_id=abc123')
        self.assertEqual(getattr(br, '_Browser__shared_cookie_header'), 'session_id=abc123')

    def test_start_request_provider_does_not_apply_shared_cookies_when_disabled(self):
        """Browser should not carry cookies across providers when --accept-cookies is disabled."""

        br = self.make_browser(accept_cookies=False, is_proxy=False)
        old_client = MagicMock()
        old_client._push_cookies.return_value = 'session_id=abc123'
        setattr(br, '_Browser__client', old_client)
        setattr(br, '_Browser__shared_cookie_header', None)

        new_client = MagicMock()
        with patch('src.lib.browser.browser.request_http', return_value=new_client):
            br._Browser__start_request_provider()

        old_client._push_cookies.assert_not_called()
        new_client.add_header.assert_not_called()
        self.assertIsNone(getattr(br, '_Browser__shared_cookie_header'))

    def test_request_with_waf_safe_mode_updates_shared_cookie_snapshot(self):
        """Browser should refresh the shared cookie snapshot after each request."""

        br = self.make_browser(accept_cookies=True)
        client = MagicMock()
        client.request.return_value = object()
        client._push_cookies.return_value = '__js_p_=153,1800,0,0,0'
        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__shared_cookie_header', None)

        br._Browser__request_with_waf_safe_mode('http://example.com/currency')

        client.request.assert_called_once_with('http://example.com/currency')
        client._push_cookies.assert_called_once()
        self.assertEqual(
            getattr(br, '_Browser__shared_cookie_header'),
            '__js_p_=153,1800,0,0,0'
        )


    def test_verify_active_scan_list_returns_for_restored_pending_requests(self):
        """Random-list verification should skip resumed pending-request runs."""

        br = self.make_browser(is_random_list=True)
        br._Browser__session_snapshot = {'pending_requests': []}
        br._Browser__pending_requests = {'0::http://example.com/a': {'url': 'http://example.com/a'}}
        br._Browser__reader.count_active_lines = MagicMock(return_value=0)

        br._Browser__verify_active_scan_list_size()

        br._Browser__reader.count_active_lines.assert_not_called()

    def test_verify_active_scan_list_warns_when_count_fails(self):
        """Random-list verification should warn and continue when the active list cannot be counted."""

        br = self.make_browser(is_random_list=True)
        br._Browser__reader.count_active_lines = MagicMock(side_effect=TypeError('bad count'))

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__verify_active_scan_list_size()

        warning_mock.assert_called_once()
        self.assertIn('Unable to verify active scan list size', warning_mock.call_args.kwargs['msg'])

    def test_warn_if_scan_finished_early_returns_when_all_items_were_submitted(self):
        """Early-finish guard should stay silent when submitted count reaches the planned count."""

        br = self.make_browser()
        br._Browser__pool.submitted_size = 3
        br._Browser__pool.total_items_size = 3

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__warn_if_scan_finished_early()

        warning_mock.assert_not_called()

    def test_fingerprint_summary_private_helpers_handle_invalid_shapes(self):
        """Fingerprint summary helpers should return unknown for invalid metadata shapes."""

        self.assertEqual(Browser._Browser__build_fingerprint_stack_summary('bad'), 'unknown')
        self.assertEqual(Browser._Browser__build_fingerprint_security_summary('bad'), 'unknown')
        self.assertEqual(
            Browser._Browser__build_fingerprint_security_summary({'security_headers': {'hsts': 'bad'}}),
            'unknown',
        )

    def test_cookie_sync_handles_missing_client_or_cookie_provider(self):
        """Cookie snapshot sync should tolerate absent clients and clients without cookie support."""

        br = self.make_browser(accept_cookies=True)
        br._Browser__client = None
        br._Browser__shared_cookie_header = None

        br._Browser__sync_shared_cookies_from_client()

        self.assertIsNone(br._Browser__shared_cookie_header)

        br._Browser__client = object()
        br._Browser__sync_shared_cookies_from_client()

        self.assertIsNone(br._Browser__shared_cookie_header)

    def test_apply_shared_cookies_handles_empty_unsafe_and_unsupported_clients(self):
        """Cookie replay should skip unsafe values and tolerate clients without header support."""

        br = self.make_browser(accept_cookies=True)
        br._Browser__client = None
        br._Browser__shared_cookie_header = 'sid=1'

        br._Browser__apply_shared_cookies_to_client()

        br._Browser__client = MagicMock()
        br._Browser__shared_cookie_header = ''
        br._Browser__apply_shared_cookies_to_client()
        br._Browser__client.add_header.assert_not_called()

        br._Browser__shared_cookie_header = 'sid=1\r\nInjected: yes'
        br._Browser__apply_shared_cookies_to_client()
        br._Browser__client.add_header.assert_not_called()

        br._Browser__client = object()
        br._Browser__shared_cookie_header = 'sid=1'
        br._Browser__apply_shared_cookies_to_client()

    def test_waf_safe_activation_signal_scans_all_markers_without_match(self):
        """Immediate WAF-safe detection should return False when no signal marker matches."""

        br = self.make_browser()

        self.assertFalse(br._Browser__is_explicit_waf_safe_activation_detection({'signals': ['plain block']}))

    def test_get_header_value_falls_back_to_case_insensitive_items_iteration(self):
        """Header lookup should support mappings where get() misses but items() preserves case."""

        class HeadersWithItemsOnly(object):
            def get(self, name):
                return None

            def items(self):
                return [('Retry-After', '5')]

        response = SimpleNamespace(headers=HeadersWithItemsOnly())

        self.assertEqual(Browser._Browser__get_header_value(response, 'retry-after'), '5')

    def test_dns_wildcard_match_returns_none_for_urls_without_hostname(self):
        """DNS wildcard calibration should ignore malformed URLs that have no hostname."""

        br = self.make_browser(is_auto_calibrate=True, scan='subdomains', SUBDOMAINS_SCAN='subdomains')
        br._Browser__calibration = SimpleNamespace(has_dns_wildcard=True, match_dns_wildcard=MagicMock())

        self.assertIsNone(br._Browser__match_dns_wildcard_response('not-a-url'))
        br._Browser__calibration.match_dns_wildcard.assert_not_called()

    def test_calibration_match_skips_stacktrace_bucket(self):
        """Auto-calibration should never suppress high-value stacktrace findings."""

        br = self.make_browser(is_auto_calibrate=True)
        br._Browser__calibration = SimpleNamespace(match=MagicMock(return_value={'score': 1.0}))

        actual = br._Browser__match_calibrated_response(object(), ('stacktrace', 'http://example.com/error', '1KB', '500'))

        self.assertIsNone(actual)
        br._Browser__calibration.match.assert_not_called()

    def test_header_bypass_skip_logs_blocked_status_when_feature_enabled(self):
        """Header-bypass skip path should record blocked responses when probing is not applicable."""

        br = self.make_browser(is_header_bypass=True)
        br._Browser__header_bypass = SimpleNamespace(should_probe=MagicMock(return_value=False))

        br._Browser__probe_header_bypass('http://example.com/admin', ('blocked', 'http://example.com/admin', '1KB', '403'))

        br._Browser__debug.debug_header_bypass_skipped.assert_called_once_with(403)

    def test_http_request_merges_stacktrace_detection_metadata_into_report_item(self):
        """HTTP request flow should keep stacktrace metadata on accepted stacktrace findings."""

        br = self.make_browser(is_recursive=False)
        response = SimpleNamespace(
            data=b'Traceback (most recent call last):',
            headers={'Content-Type': 'text/plain'},
            opendoor_stacktrace_detection={
                'type': 'stacktrace',
                'runtime': 'python',
                'signal': 'python-traceback',
                'confidence': 95,
            },
        )
        br._Browser__client.request.return_value = response
        br._Browser__response.handle.return_value = ('stacktrace', 'http://example.com/error', '1KB', '500')
        br._Browser__header_bypass = SimpleNamespace(should_probe=MagicMock(return_value=False))
        br._Browser__calibration = None

        br._Browser__http_request('http://example.com/error')

        self.assertEqual(
            br._Browser__result['report_items']['stacktrace'][0]['stacktrace_detection'],
            response.opendoor_stacktrace_detection,
        )


    def test_fingerprint_progress_should_cover_invalid_values_and_terminal_fallback(self):
        """Browser.__fingerprint_progress() should handle invalid values and terminal fallback."""

        browser = object.__new__(Browser)
        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', side_effect=OSError):
                browser._Browser__fingerprint_progress('bad', object(), 'metadata-' + ('x' * 200))

        output = stdout.getvalue()

        self.assertIn(chr(13), output)
        self.assertIn('Fingerprint [', output)
        self.assertIn('0.0%', output)
        self.assertTrue(output.split(chr(13))[-1].endswith('...'))
        self.assertTrue(getattr(browser, '_Browser__fingerprint_progress_active'))
        self.assertGreater(getattr(browser, '_Browser__fingerprint_progress_last_length'), 0)

    def test_fingerprint_progress_done_should_cover_active_zero_length_clear(self):
        """Browser.__fingerprint_progress() done branch should tolerate active zero-length state."""

        browser = object.__new__(Browser)
        setattr(browser, '_Browser__fingerprint_progress_active', True)
        setattr(browser, '_Browser__fingerprint_progress_last_length', 0)

        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('src.lib.browser.browser.tpl.info') as info_mock:
                browser._Browser__fingerprint_progress(1, 0, 'done')

        self.assertFalse(getattr(browser, '_Browser__fingerprint_progress_active'))
        self.assertEqual(getattr(browser, '_Browser__fingerprint_progress_last_length'), 0)

        info_mock.assert_called_once()
        message = info_mock.call_args.kwargs.get('msg')
        self.assertIn('Fingerprint [', message)
        self.assertIn('0.0%', message)
        self.assertIn('done', message)

    def test_clear_filtered_progress_should_ignore_inactive_state(self):
        """Browser.__clear_filtered_progress() should be a no-op without active progress."""

        browser = object.__new__(Browser)
        setattr(browser, '_Browser__filtered_progress_active', False)

        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            browser._Browser__clear_filtered_progress()

        self.assertEqual(stdout.getvalue(), '')

    def test_clear_filtered_progress_should_cover_active_zero_length_state(self):
        """Browser.__clear_filtered_progress() should clear active zero-length progress state."""

        browser = object.__new__(Browser)
        setattr(browser, '_Browser__filtered_progress_active', True)
        setattr(browser, '_Browser__filtered_progress_last_length', 0)

        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            browser._Browser__clear_filtered_progress()

        self.assertEqual(stdout.getvalue(), '')
        self.assertFalse(getattr(browser, '_Browser__filtered_progress_active'))
        self.assertEqual(getattr(browser, '_Browser__filtered_progress_last_length'), 0)

    def test_emit_filtered_progress_should_cover_terminal_fallback_and_no_metadata(self):
        """Browser.__emit_filtered_progress() should cover terminal fallback and missing metadata."""

        browser = object.__new__(Browser)
        setattr(browser, '_Browser__pool', SimpleNamespace(items_size=0, total_items_size=0))

        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', side_effect=ValueError):
                result = browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://example.com/' + ('long/' * 80), '1KB', '200'),
                    None,
                )

        output = stdout.getvalue()

        self.assertTrue(result)
        self.assertIn(chr(13), output)
        self.assertIn('0.0%', output)
        self.assertIn('calibrated - 200 - 1KB', output)
        self.assertNotIn('score=', output)
        self.assertTrue(output.split(chr(13))[-1].endswith('...'))

    def test_emit_filtered_progress_should_cover_string_score(self):
        """Browser.__emit_filtered_progress() should render non-numeric scores."""

        browser = object.__new__(Browser)
        setattr(browser, '_Browser__pool', SimpleNamespace(items_size=7, total_items_size=10))

        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=160)):
                result = browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://example.com/deep', '158KB', '200'),
                    {'calibration_score': 'manual'},
                )

        output = stdout.getvalue()
        rendered = output.split(chr(13))[-1]

        self.assertTrue(result)
        self.assertLessEqual(len(rendered), 159)
        self.assertIn('score=manual', output)
        self.assertFalse(rendered.endswith('...'))


class TestBrowserInitExtra(unittest.TestCase):
    """Extra init-branch coverage for Browser."""

    def make_config(self, **overrides):
        data = {
            'scan': 'directories',
            'DEFAULT_SCAN': 'directories',
            '_method': 'HEAD',
            'method': 'GET',
            'method_override_items': [],
            'proxy_list': '',
            'is_random_list': False,
            'is_extension_filter': False,
            'is_ignore_extension_filter': False,
            'is_external_wordlist': False,
            'wordlist': None,
            'is_standalone_proxy': False,
            'is_external_proxy_list': False,
            'prefix': '',
            'is_external_reports_dir': False,
            'reports_dir': None,
            'extensions': [],
            'ignore_extensions': [],
            'threads': 1,
            'delay': 0,
            'is_session_enabled': False,
            'session_save': None,
            'session_autosave_sec': 20,
            'session_autosave_items': 200,
        }
        data.update(overrides)
        return SimpleNamespace(**data)

    def test_init_head_get_without_override_items_does_not_warn(self):
        """Browser init should not warn when HEAD->GET override has no items to report."""

        reader = MagicMock()
        reader.total_lines = 3

        with patch('src.lib.browser.browser.Config', return_value=self.make_config()), \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader', return_value=reader), \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()), \
                patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            Browser({'host': 'test.local'})

        warning_mock.assert_not_called()

    def test_init_applies_extension_filter_on_default_scan(self):
        """Browser init should build extensionlist when extension-filter mode is enabled."""

        reader = MagicMock()
        reader.total_lines = 3

        with patch('src.lib.browser.browser.Config', return_value=self.make_config(is_extension_filter=True, extensions=['php'])), \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader', return_value=reader), \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()):
            Browser({'host': 'test.local'})

        reader.filter_by_extension.assert_called_once()

    def test_init_creates_session_manager_when_enabled(self):
        """Browser init should create SessionManager when persistent sessions are enabled."""

        reader = MagicMock()
        reader.total_lines = 3
        session_manager = MagicMock()

        with patch('src.lib.browser.browser.Config', return_value=self.make_config(
            is_session_enabled=True,
            session_save='/tmp/session.json',
            session_autosave_sec=20,
            session_autosave_items=200
        )), \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader', return_value=reader), \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()), \
                patch('src.lib.browser.browser.SessionManager', return_value=session_manager) as manager_mock:
            br = Browser({'host': 'test.local'})

        manager_mock.assert_called_once()
        self.assertIs(getattr(br, '_Browser__session'), session_manager)

    def test_init_restores_snapshot_when_present(self):
        """Browser init should restore state from a provided session snapshot."""

        reader = MagicMock()
        reader.total_lines = 3
        snapshot = {'pending': [], 'seen': [], 'stats': {'processed': 0, 'total_items': 1}}

        with patch('src.lib.browser.browser.Config', return_value=self.make_config()), \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader', return_value=reader), \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()), \
                patch.object(Browser, '_Browser__restore_session_state') as restore_mock:
            Browser({'host': 'test.local', 'session_snapshot': snapshot})

        restore_mock.assert_called_once_with(snapshot)
