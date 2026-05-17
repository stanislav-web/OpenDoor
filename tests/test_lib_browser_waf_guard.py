# -*- coding: utf-8 -*-

import threading
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core import helper
from src.lib.browser.browser import Browser, _WafGuardStop
from src.lib.browser.config import Config


class TestBrowserWafGuard(unittest.TestCase):
    """Regression tests for WAF guard early stop behavior."""

    def make_browser(self, *, enabled=True, after=2, threshold=1.0):
        """Create a Browser shell with only WAF guard state hydrated."""

        browser = Browser.__new__(Browser)
        config = SimpleNamespace(
            is_waf_guard=enabled,
            waf_guard_after=after,
            waf_guard_threshold=threshold,
            is_session_enabled=False,
        )

        setattr(browser, '_Browser__config', config)
        setattr(browser, '_Browser__waf_guard_lock', threading.RLock())
        setattr(browser, '_Browser__waf_guard_classified', 0)
        setattr(browser, '_Browser__waf_guard_blocked', 0)
        setattr(browser, '_Browser__waf_guard_stopped', False)
        setattr(browser, '_Browser__progress_output_lock', threading.RLock())
        setattr(browser, '_Browser__filtered_progress_active', False)
        setattr(browser, '_Browser__filtered_progress_last_length', 0)
        setattr(browser, '_Browser__session_lock', threading.RLock())
        setattr(browser, '_Browser__session', None)
        setattr(browser, '_Browser__session_dirty', False)
        setattr(browser, '_Browser__completed_requests', set())
        setattr(browser, '_Browser__pending_requests', {})
        setattr(browser, '_Browser__seen_scan_urls', set())
        setattr(browser, '_Browser__processed_offset', 0)
        setattr(browser, '_Browser__session_snapshot', None)
        setattr(browser, '_Browser__result', {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
        })

        return browser

    def test_should_expose_waf_guard_config_defaults(self):
        """Config should expose WAF guard defaults and auto-enable WAF detection."""

        cfg = Config({'reports': 'std', 'waf_guard': True})

        self.assertTrue(cfg.is_waf_guard)
        self.assertTrue(cfg.is_waf_detect)
        self.assertEqual(cfg.waf_guard_after, 50)
        self.assertEqual(cfg.waf_guard_threshold, 0.95)

    def test_should_trigger_waf_guard_after_block_threshold(self):
        """Browser should trigger WAF guard after enough WAF-blocked responses."""

        browser = self.make_browser(enabled=True, after=2, threshold=1.0)
        record = getattr(browser, '_Browser__record_waf_guard_response')

        response_data = ('blocked', 'https://example.test/admin', '6KB', '403')
        waf_detection = {'name': 'Cloudflare', 'confidence': 92}

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            self.assertFalse(record(response_data, waf_detection))
            self.assertTrue(record(response_data, waf_detection))

        warning_mock.assert_called_once()
        self.assertTrue(getattr(browser, '_Browser__waf_guard_stopped'))
        self.assertEqual(getattr(browser, '_Browser__waf_guard_classified'), 2)
        self.assertEqual(getattr(browser, '_Browser__waf_guard_blocked'), 2)

    def test_should_not_trigger_waf_guard_for_origin_forbidden(self):
        """Browser should not treat plain origin 403 responses as WAF-blocked."""

        browser = self.make_browser(enabled=True, after=1, threshold=1.0)
        record = getattr(browser, '_Browser__record_waf_guard_response')

        response_data = ('forbidden', 'https://example.test/admin', '0B', '403')

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            self.assertFalse(record(response_data, None))

        warning_mock.assert_not_called()
        self.assertFalse(getattr(browser, '_Browser__waf_guard_stopped'))
        self.assertEqual(getattr(browser, '_Browser__waf_guard_classified'), 1)
        self.assertEqual(getattr(browser, '_Browser__waf_guard_blocked'), 0)

    def test_should_keep_normal_batch_submission_without_waf_guard(self):
        """Browser._add_urls() should keep the original one-join batch flow without WAF guard."""

        browser = self.make_browser(enabled=False, after=2, threshold=1.0)
        pool = SimpleNamespace(add=MagicMock(), join=MagicMock())
        setattr(browser, '_Browser__pool', pool)
        setattr(browser, '_Browser__deduplicate_scan_url', lambda url: True)
        setattr(browser, '_Browser__is_ignored', lambda url: False)
        setattr(browser, '_Browser__register_pending_request', lambda url, depth: True)

        browser._add_urls(['u1', 'u2', 'u3'])

        self.assertEqual(pool.add.call_count, 3)
        self.assertEqual(pool.join.call_count, 1)

    def test_should_use_guard_windows_only_when_waf_guard_is_enabled(self):
        """Browser._add_urls() should split submissions into guard windows only under WAF guard."""

        browser = self.make_browser(enabled=True, after=2, threshold=1.0)
        pool = SimpleNamespace(add=MagicMock(), join=MagicMock())
        setattr(browser, '_Browser__pool', pool)
        setattr(browser, '_Browser__deduplicate_scan_url', lambda url: True)
        setattr(browser, '_Browser__is_ignored', lambda url: False)
        setattr(browser, '_Browser__register_pending_request', lambda url, depth: True)

        browser._add_urls(['u1', 'u2', 'u3', 'u4', 'u5'])

        self.assertEqual(pool.add.call_count, 5)
        self.assertEqual(pool.join.call_count, 3)

    def test_should_ignore_waf_guard_recording_when_disabled_or_response_missing(self):
        """Browser should not record WAF guard samples when disabled or missing response data."""

        disabled = self.make_browser(enabled=False, after=1, threshold=1.0)
        record_disabled = getattr(disabled, '_Browser__record_waf_guard_response')
        self.assertFalse(record_disabled(('blocked', 'u', '1KB', '403'), {'name': 'Cloudflare'}))
        self.assertEqual(getattr(disabled, '_Browser__waf_guard_classified'), 0)

        enabled = self.make_browser(enabled=True, after=1, threshold=1.0)
        record_enabled = getattr(enabled, '_Browser__record_waf_guard_response')
        self.assertFalse(record_enabled(None, {'name': 'Cloudflare'}))
        self.assertEqual(getattr(enabled, '_Browser__waf_guard_classified'), 0)

    def test_should_return_true_when_waf_guard_is_already_triggered(self):
        """Browser should keep a triggered WAF guard state stable."""

        browser = self.make_browser(enabled=True, after=1, threshold=1.0)
        setattr(browser, '_Browser__waf_guard_stopped', True)

        record = getattr(browser, '_Browser__record_waf_guard_response')

        self.assertTrue(record(('blocked', 'u', '1KB', '403'), {'name': 'Cloudflare'}))
        self.assertEqual(getattr(browser, '_Browser__waf_guard_classified'), 0)

    def test_should_not_trigger_waf_guard_below_block_threshold(self):
        """Browser should wait when WAF-blocked ratio is below the configured threshold."""

        browser = self.make_browser(enabled=True, after=2, threshold=0.75)
        record = getattr(browser, '_Browser__record_waf_guard_response')

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            self.assertFalse(record(('blocked', 'u1', '1KB', '403'), {'name': 'Cloudflare'}))
            self.assertFalse(record(('success', 'u2', '1KB', '200'), None))

        warning_mock.assert_not_called()
        self.assertFalse(getattr(browser, '_Browser__waf_guard_stopped'))
        self.assertEqual(getattr(browser, '_Browser__waf_guard_classified'), 2)
        self.assertEqual(getattr(browser, '_Browser__waf_guard_blocked'), 1)

    def test_should_default_waf_guard_window_size_when_config_is_invalid(self):
        """Browser should fall back to the default WAF guard window for invalid config values."""

        browser = self.make_browser(enabled=True, after=2, threshold=1.0)
        getattr(browser, '_Browser__config').waf_guard_after = 'bad'

        self.assertEqual(getattr(browser, '_Browser__waf_guard_window_size')(), 50)

    def test_should_skip_duplicate_urls_inside_waf_guard_windows(self):
        """Browser._add_urls() should skip duplicate URLs while WAF guard windowing is enabled."""

        browser = self.make_browser(enabled=True, after=2, threshold=1.0)
        pool = SimpleNamespace(add=MagicMock(), join=MagicMock())
        setattr(browser, '_Browser__pool', pool)
        setattr(browser, '_Browser__deduplicate_scan_url', lambda url: url != 'u2')
        setattr(browser, '_Browser__is_ignored', lambda url: False)
        setattr(browser, '_Browser__register_pending_request', lambda url, depth: True)

        browser._add_urls(['u1', 'u2', 'u3'])

        self.assertEqual([call.args[1] for call in pool.add.call_args_list], ['u1', 'u3'])
        self.assertEqual(pool.join.call_count, 1)

    def test_should_report_ignored_urls_inside_waf_guard_windows(self):
        """Browser._add_urls() should preserve ignored URL reporting under WAF guard."""

        browser = self.make_browser(enabled=True, after=2, threshold=1.0)
        pool = SimpleNamespace(add=MagicMock(), join=MagicMock())
        setattr(browser, '_Browser__pool', pool)
        setattr(browser, '_Browser__deduplicate_scan_url', lambda url: True)
        setattr(browser, '_Browser__is_ignored', lambda url: url == 'u2')
        setattr(browser, '_Browser__register_pending_request', lambda url, depth: True)
        setattr(browser, '_Browser__catch_report_data', MagicMock())
        setattr(browser, '_Browser__emit_ignored_item_warning', MagicMock())

        browser._add_urls(['u1', 'u2'])

        getattr(browser, '_Browser__catch_report_data').assert_called_once_with('ignored', 'u2')
        getattr(browser, '_Browser__emit_ignored_item_warning').assert_called_once_with('u2')
        self.assertEqual(pool.add.call_count, 1)
        self.assertEqual(pool.join.call_count, 1)

    def test_should_stop_before_submitting_when_waf_guard_already_triggered(self):
        """Browser._add_urls() should stop immediately when WAF guard is already triggered."""

        browser = self.make_browser(enabled=True, after=2, threshold=1.0)
        setattr(browser, '_Browser__waf_guard_stopped', True)
        setattr(browser, '_Browser__pool', SimpleNamespace(add=MagicMock(), join=MagicMock()))

        with self.assertRaises(_WafGuardStop):
            browser._add_urls(['u1'])

    def test_should_stop_after_full_waf_guard_window_join(self):
        """Browser._add_urls() should stop after a full guard window triggers WAF guard."""

        browser = self.make_browser(enabled=True, after=2, threshold=1.0)
        pool = SimpleNamespace(add=MagicMock(), join=MagicMock())
        pool.join.side_effect = lambda: setattr(browser, '_Browser__waf_guard_stopped', True)
        setattr(browser, '_Browser__pool', pool)
        setattr(browser, '_Browser__deduplicate_scan_url', lambda url: True)
        setattr(browser, '_Browser__is_ignored', lambda url: False)
        setattr(browser, '_Browser__register_pending_request', lambda url, depth: True)

        with self.assertRaises(_WafGuardStop):
            browser._add_urls(['u1', 'u2', 'u3'])

        self.assertEqual(pool.add.call_count, 2)
        self.assertEqual(pool.join.call_count, 1)

    def test_should_stop_after_final_partial_waf_guard_window_join(self):
        """Browser._add_urls() should stop after the final partial guard window triggers WAF guard."""

        browser = self.make_browser(enabled=True, after=3, threshold=1.0)
        pool = SimpleNamespace(add=MagicMock(), join=MagicMock())
        pool.join.side_effect = lambda: setattr(browser, '_Browser__waf_guard_stopped', True)
        setattr(browser, '_Browser__pool', pool)
        setattr(browser, '_Browser__deduplicate_scan_url', lambda url: True)
        setattr(browser, '_Browser__is_ignored', lambda url: False)
        setattr(browser, '_Browser__register_pending_request', lambda url, depth: True)

        with self.assertRaises(_WafGuardStop):
            browser._add_urls(['u1', 'u2'])

        self.assertEqual(pool.add.call_count, 2)
        self.assertEqual(pool.join.call_count, 1)

    def test_should_translate_keyboard_interrupt_during_waf_guard_join(self):
        """Browser._add_urls() should keep KeyboardInterrupt semantics under WAF guard."""

        browser = self.make_browser(enabled=True, after=1, threshold=1.0)
        pool = SimpleNamespace(add=MagicMock(), join=MagicMock(side_effect=KeyboardInterrupt))
        setattr(browser, '_Browser__pool', pool)
        setattr(browser, '_Browser__deduplicate_scan_url', lambda url: True)
        setattr(browser, '_Browser__is_ignored', lambda url: False)
        setattr(browser, '_Browser__register_pending_request', lambda url, depth: True)

        with self.assertRaises(KeyboardInterrupt):
            browser._add_urls(['u1'])


    def test_should_not_warn_about_early_finish_when_waf_guard_stopped_scan(self):
        """Browser should not emit generic early-finish warning after WAF guard stops the scan."""

        browser = self.make_browser(enabled=True, after=2, threshold=1.0)
        setattr(browser, '_Browser__pool', SimpleNamespace(submitted_size=1, total_items_size=10))
        setattr(browser, '_Browser__waf_guard_stopped', True)

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            getattr(browser, '_Browser__warn_if_scan_finished_early')()

        warning_mock.assert_not_called()

    def test_should_clear_previous_fingerprint_progress_on_done_message(self):
        """Browser fingerprint progress should clear transient progress before final done output."""

        from io import StringIO

        browser = self.make_browser(enabled=True, after=2, threshold=1.0)
        setattr(browser, '_Browser__fingerprint_progress_active', True)
        setattr(browser, '_Browser__fingerprint_progress_last_length', 5)
        output = StringIO()

        with patch('sys.stdout', new=output), \
                patch('src.lib.browser.browser.tpl.info') as info_mock:
            getattr(browser, '_Browser__fingerprint_progress')(1, 1, 'done')

        self.assertEqual(output.getvalue(), '\r     \r')
        info_mock.assert_called_once()
        self.assertFalse(getattr(browser, '_Browser__fingerprint_progress_active'))
        self.assertEqual(getattr(browser, '_Browser__fingerprint_progress_last_length'), 0)

    def test_should_warn_about_non_empty_supercookie_risks_only(self):
        """Browser should render only non-empty supercookie fingerprint warnings."""

        self.make_browser(enabled=True, after=2, threshold=1.0)

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            getattr(Browser, '_Browser__print_privacy_risk_warnings')({
                'privacy_risks': {
                    'supercookie': {
                        'risk': 'high',
                        'warnings': ['', 'HSTS preload may persist visitor state'],
                    },
                },
            })

        warning_mock.assert_called_once_with(msg='Possible supercookie tracking surface: HSTS preload may persist visitor state')

    def test_should_capture_shared_cookie_header_from_client(self):
        """Browser should keep accepted cookies for recreated request providers."""

        browser = self.make_browser(enabled=True, after=2, threshold=1.0)
        getattr(browser, '_Browser__config').accept_cookies = True
        setattr(browser, '_Browser__client', SimpleNamespace(_push_cookies=lambda: 'sid=1'))
        setattr(browser, '_Browser__shared_cookie_header', None)

        getattr(browser, '_Browser__sync_shared_cookies_from_client')()

        self.assertEqual(getattr(browser, '_Browser__shared_cookie_header'), 'sid=1')



if __name__ == '__main__':
    unittest.main()
