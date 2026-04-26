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

    def test_http_request_activates_safe_mode_and_suspends_recursive_expansion_for_blocked(self):
        """Blocked responses should activate safe mode and stop recursive amplification."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace()

        setattr(br, '_Browser__should_expand_recursively', MagicMock(return_value=True))
        setattr(br, '_Browser__enqueue_recursive_children', MagicMock())

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__http_request('http://example.com/login', depth=0)

        self.assertTrue(getattr(br, '_Browser__waf_safe_active'))
        self.assertEqual(getattr(br, '_Browser__waf_safe_vendor'), 'Cloudflare')
        self.assertEqual(getattr(br, '_Browser__waf_safe_confidence'), 92)
        br._Browser__enqueue_recursive_children.assert_not_called()
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
            }
        }

        br._Browser__restore_session_state(snapshot)

        self.assertTrue(getattr(br, '_Browser__waf_safe_active'))
        self.assertEqual(getattr(br, '_Browser__waf_safe_vendor'), 'Cloudflare')
        self.assertEqual(getattr(br, '_Browser__waf_safe_confidence'), 92)
        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 0.75)
        self.assertEqual(getattr(br, '_Browser__waf_safe_next_at'), 0.0)


if __name__ == '__main__':
    unittest.main()