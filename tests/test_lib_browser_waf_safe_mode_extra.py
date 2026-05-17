# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core import helper
from src.lib.browser.browser import Browser


class TestBrowserWafSafeModeExtra(unittest.TestCase):
    """Extra browser tests for WAF-aware safe mode."""

    def make_browser(self):
        """Create a minimal Browser stub."""

        br = Browser.__new__(Browser)

        setattr(br, '_Browser__config', SimpleNamespace(
            is_waf_safe_mode=True,
            is_session_enabled=False,
            is_response_filtering=False,
            is_recursive=True,
            recursive_depth=2,
            recursive_status=['200', '403'],
            recursive_exclude=[],
            DEFAULT_SCAN='directories',
            scan='directories',
            host='example.com',
            scheme='http://',
            port=80,
            prefix='',
        ))

        setattr(br, '_Browser__client', MagicMock())
        setattr(br, '_Browser__reader', SimpleNamespace(
            get_ignored_list=MagicMock(return_value=[])
        ))
        setattr(br, '_Browser__response', SimpleNamespace(
            handle=MagicMock(return_value=('blocked', 'http://example.com/login', '10B', '403')),
            waf_detection={'name': 'Cloudflare', 'confidence': 92}
        ))
        setattr(br, '_Browser__pool', SimpleNamespace(
            items_size=1,
            total_items_size=1,
            size=0,
            workers_size=1
        ))
        setattr(br, '_Browser__visited_recursive', set())
        setattr(br, '_Browser__queued_recursive', set())
        setattr(br, '_Browser__result', {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list()
        })

        return br

    def test_http_request_counts_single_waf_block_without_activating_safe_mode(self):
        """Single ordinary WAF 403 should be logged without globally slowing the scan."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace()

        setattr(br, '_Browser__should_expand_recursively', MagicMock(return_value=True))
        setattr(br, '_Browser__enqueue_recursive_children', MagicMock())

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__http_request('http://example.com/login', depth=0)

        self.assertFalse(getattr(br, '_Browser__waf_safe_active'))
        self.assertEqual(len(getattr(br, '_Browser__waf_safe_block_events')), 1)
        br._Browser__enqueue_recursive_children.assert_not_called()
        warning_mock.assert_not_called()

    def test_http_request_activates_safe_mode_after_repeated_waf_blocks(self):
        """Repeated ordinary WAF 403 responses should activate safe mode by threshold."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace()

        setattr(br, '_Browser__should_expand_recursively', MagicMock(return_value=False))

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__http_request('http://example.com/one.env', depth=0)
            br._Browser__http_request('http://example.com/two.env', depth=0)
            br._Browser__http_request('http://example.com/three.env', depth=0)

        self.assertTrue(getattr(br, '_Browser__waf_safe_active'))
        self.assertEqual(getattr(br, '_Browser__waf_safe_vendor'), 'Cloudflare')
        self.assertEqual(getattr(br, '_Browser__waf_safe_confidence'), 92)
        self.assertEqual(len(getattr(br, '_Browser__waf_safe_block_events')), 3)
        warning_mock.assert_called_once()

    def test_http_request_activates_safe_mode_immediately_for_challenge(self):
        """Explicit challenge signals should bypass the WAF block threshold."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace()
        br._Browser__response.waf_detection = {
            'name': 'Cloudflare',
            'confidence': 92,
            'signals': ['header:cf-mitigated: challenge'],
        }

        setattr(br, '_Browser__should_expand_recursively', MagicMock(return_value=False))

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__http_request('http://example.com/challenge', depth=0)

        self.assertTrue(getattr(br, '_Browser__waf_safe_active'))
        self.assertEqual(len(getattr(br, '_Browser__waf_safe_block_events')), 0)
        warning_mock.assert_called_once()

    def test_request_with_waf_safe_mode_waits_between_requests(self):
        """Safe mode should serialize requests with a cooldown."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace()

        setattr(br, '_Browser__waf_safe_active', True)
        setattr(br, '_Browser__waf_safe_next_at', 10.5)
        setattr(br, '_Browser__waf_safe_delay', 0.75)

        with patch('src.lib.browser.browser.time.monotonic', side_effect=[10.0, 10.6]), \
                patch('src.lib.browser.browser.time.sleep') as sleep_mock:
            br._Browser__request_with_waf_safe_mode('http://example.com/login')

        sleep_mock.assert_called_once_with(0.5)
        self.assertEqual(getattr(br, '_Browser__waf_safe_next_at'), 11.35)

    def test_restore_session_state_restores_waf_safe_mode_runtime(self):
        """Session restore should recover active WAF safe mode state."""

        br = self.make_browser()
        snapshot = {
            'result': {
                'total': helper.counter(),
                'items': helper.list(),
                'report_items': helper.list(),
            },
            'visitedRecursive': [],
            'queuedRecursive': [],
            'seen': [],
            'pending': [],
            'stats': {
                'processed': 0,
                'total_items': 1,
            },
            'wafSafeMode': {
                'active': True,
                'vendor': 'Cloudflare',
                'confidence': 92,
                'delay': 0.75,
                'recoveryCount': 3,
                'blockEvents': [1.0, 2.0],
            }
        }

        br._Browser__restore_session_state(snapshot)

        self.assertTrue(getattr(br, '_Browser__waf_safe_active'))
        self.assertEqual(getattr(br, '_Browser__waf_safe_vendor'), 'Cloudflare')
        self.assertEqual(getattr(br, '_Browser__waf_safe_confidence'), 92)
        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 0.75)
        self.assertEqual(getattr(br, '_Browser__waf_safe_next_at'), 0.0)
        self.assertEqual(getattr(br, '_Browser__waf_safe_recovery_count'), 3)
        self.assertEqual(getattr(br, '_Browser__waf_safe_block_events'), [1.0, 2.0])

    def test_adaptive_backoff_increases_delay_after_threshold_activation(self):
        """Blocked responses should increase cooldown after threshold activates safe mode."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace(status=403, headers={})

        setattr(br, '_Browser__should_expand_recursively', MagicMock(return_value=False))

        with patch('src.lib.browser.browser.tpl.warning'):
            br._Browser__http_request('http://example.com/one.env', depth=0)
            br._Browser__http_request('http://example.com/two.env', depth=0)
            br._Browser__http_request('http://example.com/three.env', depth=0)

        self.assertTrue(getattr(br, '_Browser__waf_safe_active'))
        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 1.5)
        self.assertEqual(getattr(br, '_Browser__waf_safe_recovery_count'), 0)

    def test_adaptive_backoff_does_not_penalize_plain_403_forbidden(self):
        """Plain 403 Forbidden should not be treated as rate limiting."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace(status=403, headers={})
        br._Browser__response.handle.return_value = (
            'forbidden',
            'http://example.com/admin',
            '10B',
            '403'
        )

        setattr(br, '_Browser__waf_safe_active', True)
        setattr(br, '_Browser__waf_safe_delay', 2.0)
        setattr(br, '_Browser__waf_safe_recovery_count', 0)
        setattr(br, '_Browser__should_expand_recursively', MagicMock(return_value=False))

        br._Browser__http_request('http://example.com/admin', depth=0)

        self.assertTrue(getattr(br, '_Browser__waf_safe_active'))
        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 2.0)
        self.assertEqual(getattr(br, '_Browser__waf_safe_recovery_count'), 1)

    def test_adaptive_backoff_activates_for_429_rate_limit(self):
        """429 responses should activate safe mode and increase cooldown."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace(status=429, headers={})
        br._Browser__response.handle.return_value = (
            'failed',
            'http://example.com/admin',
            '10B',
            '429'
        )

        setattr(br, '_Browser__should_expand_recursively', MagicMock(return_value=False))

        with patch('src.lib.browser.browser.tpl.warning'):
            br._Browser__http_request('http://example.com/admin', depth=0)

        self.assertTrue(getattr(br, '_Browser__waf_safe_active'))
        self.assertEqual(getattr(br, '_Browser__waf_safe_vendor'), 'Rate limit')
        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 1.5)

    def test_adaptive_backoff_uses_retry_after_for_503(self):
        """503 with Retry-After should activate safe mode and use Retry-After delay."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace(
            status=503,
            headers={'Retry-After': '4'}
        )
        br._Browser__response.handle.return_value = (
            'failed',
            'http://example.com/admin',
            '10B',
            '503'
        )

        setattr(br, '_Browser__should_expand_recursively', MagicMock(return_value=False))

        with patch('src.lib.browser.browser.tpl.warning'):
            br._Browser__http_request('http://example.com/admin', depth=0)

        self.assertTrue(getattr(br, '_Browser__waf_safe_active'))
        self.assertEqual(getattr(br, '_Browser__waf_safe_vendor'), 'Temporary response')
        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 4.0)

    def test_adaptive_backoff_clamps_retry_after_to_max_delay(self):
        """Retry-After should not push safe-mode cooldown above the max delay."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace(
            status=503,
            headers={'Retry-After': '120'}
        )
        br._Browser__response.handle.return_value = (
            'failed',
            'http://example.com/admin',
            '10B',
            '503'
        )

        setattr(br, '_Browser__should_expand_recursively', MagicMock(return_value=False))

        with patch('src.lib.browser.browser.tpl.warning'):
            br._Browser__http_request('http://example.com/admin', depth=0)

        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 8.0)

    def test_adaptive_backoff_recovers_after_clean_responses(self):
        """Clean responses should gradually reduce safe-mode cooldown."""

        br = self.make_browser()
        setattr(br, '_Browser__waf_safe_active', True)
        setattr(br, '_Browser__waf_safe_delay', 4.0)
        setattr(br, '_Browser__waf_safe_recovery_count', 0)

        response = SimpleNamespace(status=200, headers={})
        response_data = ('success', 'http://example.com/admin', '10B', '200')

        for _ in range(5):
            br._Browser__update_waf_safe_backoff(response, response_data)

        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 2.0)
        self.assertEqual(getattr(br, '_Browser__waf_safe_recovery_count'), 0)

    def test_adaptive_backoff_does_not_recover_on_failed_5xx_without_retry_after(self):
        """Failed 5xx responses without Retry-After should not recover safe-mode cooldown."""

        br = self.make_browser()
        setattr(br, '_Browser__waf_safe_active', True)
        setattr(br, '_Browser__waf_safe_delay', 4.0)
        setattr(br, '_Browser__waf_safe_recovery_count', 0)

        response = SimpleNamespace(status=502, headers={})
        response_data = ('failed', 'http://example.com/admin', '10B', '502')

        br._Browser__update_waf_safe_backoff(response, response_data)

        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 4.0)
        self.assertEqual(getattr(br, '_Browser__waf_safe_recovery_count'), 0)

if __name__ == '__main__':
    unittest.main()
