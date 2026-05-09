# -*- coding: utf-8 -*-

import unittest

from src.lib.browser.config import Config
from src.lib.browser.header_bypass import HeaderBypassProbe


class TestBrowserConfigHeaderBypass(unittest.TestCase):
    """Header injection bypass browser config tests."""

    def test_header_bypass_defaults_are_safe_and_disabled(self):
        """Config should expose stable defaults while keeping the feature disabled."""

        cfg = Config({'reports': 'std'})

        self.assertFalse(cfg.is_header_bypass)
        self.assertEqual(cfg.header_bypass_profile, HeaderBypassProbe.SAFE_PROFILE)
        self.assertEqual(cfg.header_bypass_headers, list(HeaderBypassProbe.DEFAULT_HEADERS))
        self.assertEqual(cfg.header_bypass_ips, list(HeaderBypassProbe.DEFAULT_IP_VALUES))
        self.assertEqual(cfg.header_bypass_status, list(HeaderBypassProbe.DEFAULT_STATUS_CODES))
        self.assertEqual(cfg.header_bypass_limit, 32)

    def test_header_bypass_offensive_profile_expands_defaults(self):
        """Offensive profile should expand default headers and trusted IP values."""

        cfg = Config({
            'reports': 'std',
            'header_bypass_profile': 'offensive',
        })

        self.assertEqual(cfg.header_bypass_profile, HeaderBypassProbe.OFFENSIVE_PROFILE)
        self.assertIn('X-ProxyUser-IP', cfg.header_bypass_headers)
        self.assertIn('X-HTTP-Method-Override', cfg.header_bypass_headers)
        self.assertIn('::1', cfg.header_bypass_ips)

    def test_header_bypass_invalid_profile_falls_back_to_safe(self):
        """Runtime config should fall back to safe for invalid profile values."""

        cfg = Config({'reports': 'std', 'header_bypass_profile': 'invalid'})

        self.assertEqual(cfg.header_bypass_profile, HeaderBypassProbe.SAFE_PROFILE)

    def test_header_bypass_custom_values_are_normalized(self):
        """Config should normalize custom header-bypass values."""

        cfg = Config({
            'reports': 'std',
            'header_bypass': True,
            'header_bypass_headers': ' X-Original-URL, X-Forwarded-For ,Forwarded ',
            'header_bypass_ips': ' 127.0.0.1, 10.0.0.1 ',
            'header_bypass_status': '401,403-404',
            'header_bypass_limit': '0',
        })

        self.assertTrue(cfg.is_header_bypass)
        self.assertEqual(cfg.header_bypass_headers, ['X-Original-URL', 'X-Forwarded-For', 'Forwarded'])
        self.assertEqual(cfg.header_bypass_ips, ['127.0.0.1', '10.0.0.1'])
        self.assertEqual(cfg.header_bypass_status, [401, 403, 404])
        self.assertEqual(cfg.header_bypass_limit, 0)

    def test_header_bypass_custom_list_values_are_normalized(self):
        """Config should handle already-normalized list values from option filters."""

        cfg = Config({
            'reports': 'std',
            'header_bypass_headers': [' X-Real-IP ', ' ', 'X-Client-IP'],
            'header_bypass_ips': [' localhost ', ' ', '192.168.1.1'],
            'header_bypass_status': ['401', '403'],
            'header_bypass_limit': 12,
        })

        self.assertEqual(cfg.header_bypass_headers, ['X-Real-IP', 'X-Client-IP'])
        self.assertEqual(cfg.header_bypass_ips, ['localhost', '192.168.1.1'])
        self.assertEqual(cfg.header_bypass_status, [401, 403])
        self.assertEqual(cfg.header_bypass_limit, 12)

    def test_header_bypass_defaults_are_returned_as_fresh_lists(self):
        """Default header-bypass config lists should not expose shared mutable state."""

        cfg = Config({'reports': 'std'})

        headers = cfg.header_bypass_headers
        ips = cfg.header_bypass_ips
        statuses = cfg.header_bypass_status

        headers.append('X-Mutated')
        ips.append('255.255.255.255')
        statuses.append(418)

        self.assertNotIn('X-Mutated', cfg.header_bypass_headers)
        self.assertNotIn('255.255.255.255', cfg.header_bypass_ips)
        self.assertNotIn(418, cfg.header_bypass_status)

    def test_header_bypass_status_ignores_blank_list_items(self):
        """Header bypass status config should ignore blank list values before expansion."""

        cfg = Config({
            'reports': 'std',
            'header_bypass_status': ['401', ' ', '403-404'],
        })

        self.assertEqual(cfg.header_bypass_status, [401, 403, 404])

    def test_header_bypass_limit_accepts_string_integer(self):
        """Header bypass limit should support string integers from CLI/config sources."""

        cfg = Config({
            'reports': 'std',
            'header_bypass_limit': '16',
        })

        self.assertEqual(cfg.header_bypass_limit, 16)

if __name__ == '__main__':
    unittest.main()