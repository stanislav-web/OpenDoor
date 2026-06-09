# -*- coding: utf-8 -*-

import contextlib
import io
import socket as py_socket
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from src.core import helper
from src.core.http.exceptions import ProxyRequestError, SocketError
from src.core.http.socks import Socket
from src.lib.browser.browser import Browser
from src.lib.browser.config import Config
from src.lib.browser.sniffers import SnifferContext, SnifferDecision, SnifferEngine, SnifferResult


class _TupleDetector(object):
    """Fake detector returning a tuple of findings."""

    NAME = 'tuple-detector'
    KIND = 'detector'

    def match(self, context):
        """Return one finding as a tuple to exercise engine normalization."""

        return (SnifferResult(bucket='tuple', url=context.request_url),)


class TestReleaseCoverageGaps(unittest.TestCase):
    """Release hardening tests for remaining coverage gaps."""

    def test_config_validation_covers_blank_and_malformed_filter_tokens(self):
        """Config should ignore blank filter tokens and reject malformed filter values."""

        cfg = Config({
            'reports': 'std',
            'include_status': [' ', '200'],
            'exclude_size': [' ', '0'],
            'exclude_size_range': [' ', '0-1'],
        })

        self.assertEqual(cfg.include_status, ['200'])
        self.assertEqual(cfg.exclude_size, [0])
        self.assertEqual(cfg.exclude_size_range, [(0, 1)])
        self.assertIsNone(Config._normalize_text_filter_values('   '))

        invalid_cases = [
            {'min_response_length': 'abc'},
            {'include_status': '300-200'},
            {'include_status': '99-200'},
            {'include_status': '200-600'},
            {'exclude_size_range': '100'},
            {'exclude_size_range': 'a-b'},
        ]

        for params in invalid_cases:
            with self.subTest(params=params):
                payload = {'reports': 'std'}
                payload.update(params)
                with self.assertRaises(ValueError):
                    Config(payload)

    def test_config_method_override_deduplicates_existing_items_and_fractional_delay(self):
        """Config should avoid duplicate override labels and preserve fractional delays below one second."""

        original = Config.BODY_REQUIRED_SNIFFERS
        Config.BODY_REQUIRED_SNIFFERS = original + ('--match-text',)
        try:
            cfg = Config({
                'reports': 'std',
                'method': 'HEAD',
                'sniff': '--match-text',
                'match_text': ['login'],
                'delay': 0.25,
            })
            self.assertEqual(cfg.method_override_items, ['--match-text'])
            self.assertEqual(cfg.delay, 0.25)
        finally:
            Config.BODY_REQUIRED_SNIFFERS = original

    def test_socket_connect_address_helpers_cover_error_and_dedupe_paths(self):
        """Socket diagnostics should handle DNS errors, malformed records and duplicate addresses."""

        with patch('src.core.http.socks.socket.getaddrinfo', side_effect=py_socket.gaierror(-2, 'fail')):
            self.assertEqual(Socket._resolve_connect_addresses('bad.local', 80), [])

        with patch('src.core.http.socks.socket.getaddrinfo', return_value=[
            (py_socket.AF_INET, py_socket.SOCK_STREAM, 6, ''),
            (py_socket.AF_INET, py_socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80)),
            (py_socket.AF_INET, py_socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80)),
        ]):
            self.assertEqual(Socket._resolve_connect_addresses('example.com', 80), ['127.0.0.1'])

        self.assertEqual(Socket._format_connect_addresses([]), 'unresolved')

    def test_socket_ping_does_not_close_missing_socket_on_connect_failure(self):
        """Socket.ping() should not try to close a socket when connection creation fails early."""

        with patch('src.core.http.socks.socket.create_connection', side_effect=ValueError('bad port')):
            with self.assertRaises(SocketError):
                Socket.ping('example.com', 'bad', timeout=1)


    def test_release_e2e_command_keeps_crawl_smoke_enabled(self):
        """Local release.sh is intentionally gitignored and not available in CI."""

        self.skipTest('release.sh is a local ignored release helper')

    def test_sniffer_engine_normalizes_tuple_results(self):
        """SnifferEngine should normalize tuple results into a list of findings."""

        context = SnifferContext(request_url='https://example.com/admin')
        engine = SnifferEngine(enabled=['tuple-detector'], sniffers=[_TupleDetector()])

        decision = engine.run_passive(context)

        self.assertEqual([result.bucket for result in decision.findings], ['tuple'])

    def test_sniffer_result_uses_explicit_evidence_key_and_extend_ignores_none(self):
        """SnifferResult should prefer explicit evidence keys and decisions should accept empty extensions."""

        result = SnifferResult(
            bucket='secret',
            url='https://example.com/config.php',
            metadata={'evidence': 'metadata-value'},
            evidence_key='explicit-value',
        )
        decision = SnifferDecision()

        self.assertEqual(result.dedupe_key(), ('secret', 'https://example.com/config.php', 'explicit-value'))
        self.assertIs(decision.extend(None), decision)
        self.assertEqual(decision.findings, [])


class TestBrowserReleaseCoverageGaps(unittest.TestCase):
    """Browser-focused release coverage for defensive branches."""

    @staticmethod
    def make_browser():
        """Create a minimal Browser instance without network/runtime initialization."""

        browser = Browser.__new__(Browser)
        browser._Browser__config = SimpleNamespace(
            requested_method='GET',
            waf_guard=True,
            is_waf_guard=True,
            waf_guard_after=2,
            waf_guard_threshold=0.75,
            is_session_enabled=False,
            is_auto_calibrate=False,
            calibration_threshold=0.95,
            is_standalone_proxy=False,
        )
        browser._Browser__result = {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
            'filtered_items': [],
        }
        browser._Browser__report_item_keys = {}
        browser._Browser__report_item_keys_result_id = id(browser._Browser__result)
        browser._Browser__pool = SimpleNamespace(items_size=1, total_items_size=2)
        browser._Browser__filtered_progress_active = False
        browser._Browser__filtered_progress_last_length = 0
        browser._Browser__fingerprint_progress_active = False
        browser._Browser__fingerprint_progress_last_length = 0
        browser._Browser__transport_failure_lock = threading.RLock()
        browser._Browser__transport_failures_skipped = 0
        browser._Browser__waf_guard_lock = threading.RLock()
        browser._Browser__waf_guard_classified = 0
        browser._Browser__waf_guard_blocked = 0
        browser._Browser__waf_guard_stopped = False
        browser._Browser__request_state_lock = threading.RLock()
        browser._Browser__visited_recursive = set()
        browser._Browser__queued_recursive = set()
        browser._Browser__completed_requests = set()
        browser._Browser__pending_requests = {}
        browser._Browser__transient_request_keys = set()
        browser._Browser__seen_scan_urls = set()
        return browser

    def test_browser_should_mask_plain_credentials_without_url_scheme(self):
        """Proxy credential masking should cover defensive no-scheme credential strings."""

        mask = Browser._Browser__mask_proxy_url_fallback

        self.assertEqual(mask('user:pass@proxy.local:8080'), 'user:*****@proxy.local:8080')

    def test_browser_should_clear_active_fingerprint_progress_on_done(self):
        """Fingerprint progress should clear the previous rotating line before final output."""

        browser = self.make_browser()
        browser._Browser__fingerprint_progress_active = True
        browser._Browser__fingerprint_progress_last_length = 7

        with contextlib.redirect_stdout(io.StringIO()) as stream, \
                patch('src.lib.browser.browser.output.clear_dynamic_line') as clear_line, \
                patch('src.lib.browser.browser.tpl.info') as info:
            browser._Browser__fingerprint_progress(1, 1, 'done')

        self.assertIn('\r       \r', stream.getvalue())
        self.assertFalse(browser._Browser__fingerprint_progress_active)
        self.assertEqual(browser._Browser__fingerprint_progress_last_length, 0)
        clear_line.assert_called_once_with()
        info.assert_called_once()

    def test_browser_should_keep_invalid_weak_calibration_inputs_disabled(self):
        """Weak calibration baseline guard should ignore malformed numeric inputs."""

        browser = self.make_browser()

        self.assertFalse(browser._Browser__is_weak_calibration_baseline('bad', 10))
        self.assertFalse(browser._Browser__is_weak_calibration_baseline(1, 'bad'))


    def test_browser_should_keep_calibrating_after_non_standalone_proxy_probe_failure(self):
        """Auto-calibration should count proxy probe failures without aborting non-proxy scans."""

        browser = self.make_browser()
        browser._Browser__config.is_auto_calibrate = True
        browser._Browser__calibration = None
        browser._Browser__client = object()
        browser._Browser__debug = SimpleNamespace(debug_auto_calibration_enabled=MagicMock(return_value=True))
        browser._Browser__build_dns_wildcard_addresses = MagicMock(return_value=['127.0.0.2'])
        browser._Browser__build_calibration_urls = MagicMock(return_value=['https://example.com/missing'])
        browser._Browser__request_with_waf_safe_mode = MagicMock(side_effect=ProxyRequestError('proxy down'))
        browser._Browser__response = MagicMock()

        with patch('src.lib.browser.browser.tpl.warning') as warning, \
                patch('src.lib.browser.browser.tpl.info') as info:
            result = browser.calibrate()

        self.assertIsNotNone(result)
        warning.assert_any_call(msg='Auto-calibration probe failed: proxy down')
        info.assert_any_call(msg='DNS wildcard calibration ready: addresses=127.0.0.2')

    def test_browser_should_capture_shared_cookie_header_when_client_exports_cookies(self):
        """Cookie propagation should store a non-empty provider cookie header."""

        browser = self.make_browser()
        browser._Browser__config.accept_cookies = True
        browser._Browser__shared_cookie_header = None
        browser._Browser__client = SimpleNamespace(_push_cookies=MagicMock(return_value='sid=abc'))

        browser._Browser__sync_shared_cookies_from_client()

        self.assertEqual(browser._Browser__shared_cookie_header, 'sid=abc')

    def test_browser_should_lookup_header_from_items_when_direct_get_misses(self):
        """Case-insensitive header lookup should fall back to iterating header items."""

        class Headers(object):
            """Mapping-like headers with case-sensitive get and iterable items."""

            def get(self, key):
                """Return nothing to force item iteration."""

                return None

            def items(self):
                """Return mixed-case headers."""

                return [('X-Other', '1'), ('Content-Type', 'text/html')]

        self.assertEqual(Browser._Browser__get_header_value(SimpleNamespace(headers=Headers()), 'content-type'), 'text/html')
        self.assertIsNone(self.make_browser()._Browser__response_header(SimpleNamespace(headers=[('X-Test', '1')]), 'missing'))

    def test_browser_should_include_openredirect_passive_metadata_when_recording_finding(self):
        """Open redirect report helper should preserve passive finding metadata."""

        browser = self.make_browser()
        browser._Browser__response = SimpleNamespace(_get_content_size=MagicMock(return_value='0B'))
        browser._Browser__emit_sniffer_finding = MagicMock()
        response = SimpleNamespace(status=302)

        browser._Browser__handle_open_redirect_match(
            'https://example.com/login?next=https://evil.test',
            response,
            {'openredirect_detection': {'type': 'open_redirect', 'confidence': 80, 'parameter': 'next'}},
        )

        finding = browser._Browser__emit_sniffer_finding.call_args[0][0]
        self.assertEqual(finding.bucket, 'openredirect')
        self.assertEqual(finding.metadata['openredirect_detection']['parameter'], 'next')
        self.assertEqual(finding.metadata['passive_finding']['confidence'], 'medium')

    def test_browser_should_calculate_waf_guard_ratio_before_threshold_decision(self):
        """WAF guard should stop only after its classified/block ratio reaches threshold."""

        browser = self.make_browser()
        browser._Browser__finish_filtered_progress_line = MagicMock()

        with patch('src.lib.browser.browser.tpl.warning') as warning:
            first = browser._Browser__record_waf_guard_response(('blocked', 'u1', '1B', '403'), {'name': 'WAF'})
            second = browser._Browser__record_waf_guard_response(('success', 'u2', '1B', '200'), None)

        self.assertFalse(first)
        self.assertFalse(second)
        self.assertFalse(browser._Browser__waf_guard_stopped)
        warning.assert_not_called()

    def test_browser_should_handle_transport_pause_invalid_threshold_and_unavailable_pool(self):
        """Transport outage pause helpers should keep malformed thresholds and missing pools safe."""

        browser = self.make_browser()
        browser.DEFAULT_RETRIES_FAIL_STREAK = 100

        self.assertEqual(browser._Browser__transport_outage_pause_threshold('bad'), 10)

        browser._Browser__pool = SimpleNamespace()
        browser._Browser__request_transport_outage_pause(5, 10, '/admin')

        request_pause = MagicMock(return_value=False)
        browser._Browser__pool = SimpleNamespace(request_pause=request_pause)
        browser._Browser__request_transport_outage_pause(5, 10, '/admin')
        request_pause.assert_called_once_with()

    def test_browser_should_filter_js_cookie_reload_edge_cases_without_false_positives(self):
        """JS cookie gate detection should reject large, non-HTML, visible and non-script pages."""

        def response(body, content_type='text/html'):
            return SimpleNamespace(status=200, headers={'Content-Type': content_type}, data=body.encode('utf-8'))

        cases = [
            response('x' * 2049),
            response("<script>document.cookie='x';location.reload();</script>", 'application/json'),
            response("<script>document.cookie='x';</script>"),
            response("<html><script>document.cookie='x';location.reload();</script><body>visible</body></html>"),
            response("<html><head>document.cookie='x';location.reload();</head></html>"),
            response("<html><head></head><body><script>document.cookie='x';location.reload();</script><p>visible</p></body></html>"),
        ]

        for item in cases:
            with self.subTest(body=item.data[:20]):
                self.assertIsNone(Browser._Browser__match_js_cookie_reload_challenge(
                    item,
                    ('success', 'https://example.com/admin', '1B', '200'),
                ))

    def test_browser_should_fallback_visible_text_extraction_when_html_parser_fails(self):
        """Visible text extraction should degrade to tag stripping on parser errors."""

        with patch('src.lib.browser.browser._VisibleTextExtractor.feed', side_effect=ValueError('bad html')):
            self.assertEqual(Browser._Browser__visible_text_without_scripts('<b>Visible</b>'), 'Visible')

    def test_browser_should_debug_additive_plugin_errors_when_scan_debug_is_enabled(self):
        """Additive sniffer plugin exceptions should remain debug-only diagnostics."""

        class BrokenPlugin(object):
            """Plugin that raises during passive collection."""

            RESPONSE_INDEX = 'secret'

            def process(self, _response):
                """Raise a deterministic plugin failure."""

                raise RuntimeError('boom')

        browser = self.make_browser()
        browser._Browser__response = SimpleNamespace(_response_plugins=[BrokenPlugin()])
        browser._Browser__debug = SimpleNamespace(is_scan_debug=MagicMock(return_value=True))

        with patch('src.lib.browser.browser.tpl.debug') as debug:
            findings = browser._Browser__collect_passive_sniffer_findings(
                SimpleNamespace(),
                ('success', 'https://example.com/admin', '1B', '200'),
            )

        self.assertEqual(findings, [])
        debug.assert_called_once()

    def test_browser_should_sort_passive_additive_plugins_by_bucket_order(self):
        """Passive additive plugin selection should include only configured additive buckets in stable order."""

        secret = SimpleNamespace(RESPONSE_INDEX='secret')
        file_plugin = SimpleNamespace(RESPONSE_INDEX='file')
        ignored = SimpleNamespace(RESPONSE_INDEX='success')
        browser = self.make_browser()
        browser._Browser__response = SimpleNamespace(_response_plugins=[secret, ignored, file_plugin])

        self.assertEqual(browser._Browser__passive_additive_plugins(), [file_plugin, secret])

    def test_browser_should_build_malware_and_endpoint_sniffer_metadata(self):
        """Sniffer metadata helper should preserve malware and endpoint passive finding wrappers."""

        malware_response = SimpleNamespace(opendoor_malware_detection={
            'type': 'malware',
            'subtype': 'webshell',
            'confidence': 90,
        })
        endpoint_response = SimpleNamespace(opendoor_endpoint_detection={
            'type': 'websocket',
            'confidence': 65,
        })

        malware = Browser._Browser__metadata_for_sniffer_bucket(
            'malware', malware_response, url='https://example.com/shell.php', code='200', method='GET')
        endpoint = Browser._Browser__metadata_for_sniffer_bucket(
            'endpoint', endpoint_response, url='https://example.com/app.js', code='200', method='GET')

        self.assertEqual(malware['passive_finding']['severity'], 'critical')
        self.assertEqual(endpoint['passive_finding']['confidence'], 'low')

    def test_browser_should_build_endpoint_and_openredirect_confidence_edges(self):
        """Passive metadata builders should cover invalid, medium and low confidence branches."""

        self.assertEqual(Browser._Browser__passive_endpoint_metadata('', '200', 'GET', {'confidence': 90}), {})
        medium_endpoint = Browser._Browser__passive_endpoint_metadata(
            'https://example.com/app.js', '200', 'GET', {'type': 'ajax', 'confidence': 75})
        low_redirect = Browser._Browser__passive_openredirect_metadata(
            'https://example.com/redirect', '302', 'GET', {'type': 'open_redirect', 'confidence': 10})

        self.assertEqual(medium_endpoint['passive_finding']['confidence'], 'medium')
        self.assertEqual(low_redirect['passive_finding']['confidence'], 'low')

    def test_browser_should_normalize_report_urls_and_stable_set_values(self):
        """Report dedup helpers should normalize defensive URL and set variants."""

        normalize = Browser._Browser__normalized_report_url

        self.assertEqual(normalize('http://[::1'), 'http://[::1')
        self.assertEqual(normalize('/admin#fragment'), '/admin')
        self.assertEqual(normalize('HTTP://Example.COM:8080/a?b=1#x'), 'http://example.com:8080/a?b=1')
        self.assertEqual(Browser._Browser__stable_report_value({'z', 'a'}), ('a', 'z'))

    def test_browser_should_rebuild_report_dedup_keys_from_legacy_and_structured_items(self):
        """Report dedup rebuild should cover structured, scalar legacy and non-dict states."""

        browser = self.make_browser()
        browser._Browser__result = {
            'report_items': {'success': [{'url': 'https://example.com/a', 'code': '200'}, 'https://example.com/b']},
            'items': {'success': ['https://example.com/c']},
        }
        browser._Browser__report_item_keys = {}

        browser._Browser__rebuild_report_dedup_keys()

        self.assertEqual(len(browser._Browser__report_item_keys['success']), 3)

        browser._Browser__result = []
        browser._Browser__report_item_keys = {'success': set()}
        browser._Browser__rebuild_report_dedup_keys()
        self.assertEqual(browser._Browser__report_item_keys, {'success': set()})

    def test_browser_should_store_endpoint_and_redirect_report_metadata_once(self):
        """Report writer should preserve endpoint and redirect metadata and dedupe repeated items."""

        browser = self.make_browser()
        metadata = {
            'endpoint_detection': {'type': 'ajax'},
            'redirect_classification': {'risk': 'external'},
        }

        browser._Browser__catch_report_data('success', 'https://example.com/app.js', '1B', '200', metadata=metadata)
        browser._Browser__catch_report_data('success', 'https://example.com/app.js', '1B', '200', metadata=metadata)

        items = browser._Browser__result['report_items']['success']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['endpoint_detection']['type'], 'ajax')
        self.assertEqual(items[0]['redirect_classification']['risk'], 'external')

    def test_browser_should_restore_pending_request_source_metadata_from_session(self):
        """Session restore should preserve crawl-discovered request source metadata."""

        browser = self.make_browser()
        snapshot = {
            'result': {'total': helper.counter(), 'items': helper.list()},
            'pending': [{
                'url': 'https://example.com/from-crawl',
                'depth': 1,
                'source': 'crawl',
                'source_url': 'https://example.com/',
            }],
            'seen': [],
            'visitedRecursive': [],
            'queuedRecursive': [],
            'stats': {},
        }

        browser._Browser__restore_session_state(snapshot)

        pending = list(browser._Browser__pending_requests.values())[0]
        self.assertEqual(pending['source'], 'crawl')
        self.assertEqual(pending['source_url'], 'https://example.com/')



if __name__ == '__main__':
    unittest.main()
