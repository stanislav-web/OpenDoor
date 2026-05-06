# -*- coding: utf-8 -*-

import unittest

from src.core.http.providers.debug import DebugProvider


class TestDebugProviderCoverage(unittest.TestCase):
    """Coverage tests for the no-op debug provider interface."""

    def test_default_level_helpers_are_disabled(self):
        """Default DebugProvider should expose disabled level helpers."""

        provider = DebugProvider()

        self.assertIsNone(provider.level)
        self.assertFalse(provider.is_scan_debug())
        self.assertFalse(provider.is_request_debug())
        self.assertFalse(provider.is_response_debug())

    def test_noop_debug_methods_return_none(self):
        """Default DebugProvider no-op methods should be callable by request/response layers."""

        provider = DebugProvider()

        self.assertIsNone(provider.debug_user_agents())
        self.assertIsNone(provider.debug_connection_pool('pool', object(), 'HTTP'))
        self.assertIsNone(provider.debug_proxy_pool())
        self.assertIsNone(provider.debug_list(1))
        self.assertIsNone(provider.debug_request({'A': 'B'}, 'http://test.local/', 'GET'))
        self.assertIsNone(provider.debug_response({'Status': '200'}))
        self.assertIsNone(provider.debug_request_uri('success', 'http://test.local/'))
        self.assertIsNone(provider.debug_load_sniffer_plugin('plugin'))
        self.assertIsNone(provider.debug_cookie_accept_enabled())
        self.assertIsNone(provider.debug_cookie_accepted('sid=1'))
        self.assertIsNone(provider.debug_cookie_attached({'Cookie': 'sid=1'}))
        self.assertIsNone(provider.debug_auto_calibration_enabled())
        self.assertIsNone(provider.debug_header_bypass_skipped(403))
        self.assertIsNone(provider.debug_header_bypass_probing(403, 2))
        self.assertIsNone(provider.debug_header_bypass_candidate({'bypass_header': 'X-Test'}))
        self.assertIsNone(provider.debug_header_bypass_finished())
        self.assertIsNone(provider.debug_recursive_expansion('/admin', 2, 1))
        self.assertIsNone(provider.debug_classification('success', code=200))


if __name__ == '__main__':
    unittest.main()
