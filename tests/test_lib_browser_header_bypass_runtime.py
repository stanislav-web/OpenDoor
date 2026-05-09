# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.core import helper
from src.lib.browser.browser import Browser
from src.lib.browser.header_bypass import HeaderBypassProbe


class TestBrowserHeaderBypassRuntime(unittest.TestCase):
    """Browser runtime tests for header injection bypass probes."""

    @staticmethod
    def make_browser(**config_overrides):
        """
        Create a minimal Browser instance for private runtime tests.

        :param dict config_overrides: config overrides
        :return: Browser
        """

        config = {
            'is_header_bypass': True,
            'header_bypass_headers': ['X-Original-URL', 'X-Forwarded-For'],
            'header_bypass_ips': ['127.0.0.1'],
            'header_bypass_status': [401, 403],
            'header_bypass_limit': 4,
            'is_waf_safe_mode': False,
            'is_waf_detect': False,
            'is_session_enabled': False,
            'is_auto_calibrate': False,
            'is_response_filtering': False,
            'is_recursive': False,
            'recursive_depth': 0,
            'recursive_status': [],
            'recursive_exclude': [],
            'DEFAULT_SCAN': 'directories',
            'scan': 'directories',
            'host': 'example.com',
            'scheme': 'https://',
            'port': 443,
            'prefix': '',
        }
        config.update(config_overrides)

        br = Browser.__new__(Browser)
        setattr(br, '_Browser__config', SimpleNamespace(**config))
        setattr(br, '_Browser__client', MagicMock())
        setattr(br, '_Browser__reader', SimpleNamespace(get_ignored_list=MagicMock(return_value=[])))
        setattr(br, '_Browser__pool', SimpleNamespace(
            items_size=1,
            total_items_size=1,
            size=0,
            workers_size=1
        ))
        setattr(br, '_Browser__response', SimpleNamespace(
            handle=MagicMock(),
            waf_detection=None,
        ))
        setattr(br, '_Browser__result', {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
        })
        setattr(br, '_Browser__visited_recursive', set())
        setattr(br, '_Browser__queued_recursive', set())
        setattr(br, '_Browser__calibration', None)
        setattr(br, '_Browser__header_bypass', HeaderBypassProbe(getattr(br, '_Browser__config')))

        return br

    def test_http_request_records_successful_header_bypass_candidate(self):
        """Browser should probe configured headers and record a bypass bucket."""

        br = self.make_browser()
        br._Browser__client.request.side_effect = [SimpleNamespace(), SimpleNamespace()]
        br._Browser__response.handle.side_effect = [
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            ('success', 'https://example.com/admin', '90B', '200'),
        ]

        br._Browser__http_request('https://example.com/admin', depth=0)

        self.assertEqual(br._Browser__client.request.call_count, 2)
        br._Browser__client.request.assert_any_call('https://example.com/admin')
        br._Browser__client.request.assert_any_call(
            'https://example.com/admin',
            extra_headers={'X-Original-URL': '/admin'}
        )

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['bypass'], 1)
        self.assertEqual(result['total']['forbidden'], 1)

        bypass_item = result['report_items']['bypass'][0]
        self.assertEqual(bypass_item['bypass'], 'header')
        self.assertEqual(bypass_item['bypass_header'], 'X-Original-URL')
        self.assertEqual(bypass_item['bypass_value'], '/admin')
        self.assertEqual(bypass_item['bypass_from_code'], '403')
        self.assertEqual(bypass_item['bypass_to_code'], '200')

    def test_http_request_does_not_probe_when_header_bypass_disabled(self):
        """Browser should keep the old request flow when header bypass is disabled."""

        br = self.make_browser(is_header_bypass=False)
        br._Browser__client.request.return_value = SimpleNamespace()
        br._Browser__response.handle.return_value = (
            'forbidden',
            'https://example.com/admin',
            '10B',
            '403',
        )

        br._Browser__http_request('https://example.com/admin', depth=0)

        br._Browser__client.request.assert_called_once_with('https://example.com/admin')
        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['bypass'], 0)
        self.assertEqual(result['total']['forbidden'], 1)

    def test_http_request_does_not_probe_non_configured_status(self):
        """Browser should not probe responses outside configured bypass statuses."""

        br = self.make_browser(header_bypass_status=[403])
        br._Browser__client.request.return_value = SimpleNamespace()
        br._Browser__response.handle.return_value = (
            'auth',
            'https://example.com/admin',
            '10B',
            '401',
        )

        br._Browser__http_request('https://example.com/admin', depth=0)

        br._Browser__client.request.assert_called_once_with('https://example.com/admin')
        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['bypass'], 0)
        self.assertEqual(result['total']['auth'], 1)

    def test_http_request_stops_after_first_promising_bypass_candidate(self):
        """Browser should stop probing after the first promising bypass result."""

        br = self.make_browser(
            header_bypass_headers=['X-Original-URL', 'X-Forwarded-For'],
            header_bypass_ips=['127.0.0.1'],
            header_bypass_limit=4,
        )
        br._Browser__client.request.side_effect = [
            SimpleNamespace(),
            SimpleNamespace(),
        ]
        br._Browser__response.handle.side_effect = [
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            ('success', 'https://example.com/admin', '90B', '200'),
        ]

        br._Browser__http_request('https://example.com/admin', depth=0)

        self.assertEqual(br._Browser__client.request.call_count, 2)
        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['bypass'], 1)

    def test_http_request_continues_until_promising_bypass_candidate(self):
        """Browser should continue probing when early variants are not promising."""

        br = self.make_browser(
            header_bypass_headers=['X-Original-URL'],
            header_bypass_limit=2,
        )
        br._Browser__client.request.side_effect = [
            SimpleNamespace(),
            SimpleNamespace(),
            SimpleNamespace(),
        ]
        br._Browser__response.handle.side_effect = [
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            ('forbidden', 'https://example.com/admin', '11B', '403'),
            ('success', 'https://example.com/admin', '90B', '200'),
        ]

        br._Browser__http_request('https://example.com/admin', depth=0)

        self.assertEqual(br._Browser__client.request.call_count, 3)
        br._Browser__client.request.assert_any_call(
            'https://example.com/admin',
            extra_headers={'X-Original-URL': '/admin'}
        )
        br._Browser__client.request.assert_any_call(
            'https://example.com/admin',
            extra_headers={'X-Original-URL': '/'}
        )

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['bypass'], 1)
        self.assertEqual(result['report_items']['bypass'][0]['bypass_value'], '/')

    def test_http_request_records_successful_path_bypass_candidate(self):
        """Browser should probe path variants and record path-bypass metadata."""

        br = self.make_browser(
            header_bypass_headers=['X-Original-URL'],
            header_bypass_limit=0,
        )
        br._Browser__client.request.side_effect = [
            SimpleNamespace(),
            SimpleNamespace(),
            SimpleNamespace(),
            SimpleNamespace(),
        ]
        br._Browser__response.handle.side_effect = [
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            ('forbidden', 'https://example.com/admin', '11B', '403'),
            ('forbidden', 'https://example.com/admin', '12B', '403'),
            ('success', 'https://example.com/admin/', '90B', '200'),
        ]

        br._Browser__http_request('https://example.com/admin', depth=0)

        br._Browser__client.request.assert_any_call('https://example.com/admin/')
        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['bypass'], 1)

        bypass_item = result['report_items']['bypass'][0]
        self.assertEqual(bypass_item['bypass'], 'path')
        self.assertEqual(bypass_item['bypass_variant'], 'trailing-slash')
        self.assertEqual(bypass_item['bypass_value'], '/admin/')
        self.assertEqual(bypass_item['bypass_url'], 'https://example.com/admin/')
        self.assertEqual(bypass_item['bypass_from_code'], '403')
        self.assertEqual(bypass_item['bypass_to_code'], '200')

    def test_http_request_ignores_empty_probe_response(self):
        """Browser should ignore probe responses that cannot be handled."""

        br = self.make_browser(
            header_bypass_headers=['X-Original-URL'],
            header_bypass_limit=1,
        )
        br._Browser__client.request.side_effect = [
            SimpleNamespace(),
            SimpleNamespace(),
        ]
        br._Browser__response.handle.side_effect = [
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            None,
        ]

        br._Browser__http_request('https://example.com/admin', depth=0)

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['bypass'], 0)
        self.assertEqual(result['total']['forbidden'], 1)

    def test_http_request_probes_waf_blocked_redirect_when_waf_safe_mode_enabled(self):
        """WAF-blocked redirects should trigger header-bypass probes in WAF-safe mode."""

        br = self.make_browser(
            is_waf_safe_mode=True,
            is_waf_detect=True,
            header_bypass_headers=['X-Original-URL'],
            header_bypass_status=[401, 403],
            header_bypass_limit=1,
        )
        br._Browser__client.request.side_effect = [
            SimpleNamespace(),
            SimpleNamespace(),
        ]
        br._Browser__response.handle.side_effect = [
            ('blocked', 'https://example.com/admin', '0B', '301'),
            ('success', 'https://example.com/admin', '90B', '200'),
        ]

        br._Browser__http_request('https://example.com/admin', depth=0)

        self.assertEqual(br._Browser__client.request.call_count, 2)
        br._Browser__client.request.assert_any_call(
            'https://example.com/admin',
            extra_headers={'X-Original-URL': '/admin'}
        )
        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['bypass'], 1)
        self.assertEqual(result['report_items']['bypass'][0]['bypass_from_code'], '301')

    def test_http_request_does_not_probe_regular_redirect_outside_configured_status(self):
        """Regular redirects should not trigger header-bypass probes by default."""

        br = self.make_browser(
            is_waf_safe_mode=True,
            is_waf_detect=True,
            header_bypass_status=[401, 403],
        )
        br._Browser__client.request.return_value = SimpleNamespace()
        br._Browser__response.handle.return_value = (
            'redirect',
            'https://example.com/admin',
            '0B',
            '301',
        )

        br._Browser__http_request('https://example.com/admin', depth=0)

        br._Browser__client.request.assert_called_once_with('https://example.com/admin')
        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['bypass'], 0)
        self.assertEqual(result['total']['redirect'], 1)

    def test_request_with_waf_safe_mode_preserves_old_call_shape_without_extra_headers(self):
        """WAF-safe wrapper should not pass extra_headers=None to regular requests."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace()

        br._Browser__request_with_waf_safe_mode('https://example.com/admin')

        br._Browser__client.request.assert_called_once_with('https://example.com/admin')

    def test_request_with_waf_safe_mode_passes_extra_headers_only_when_present(self):
        """WAF-safe wrapper should pass temporary headers only for probe requests."""

        br = self.make_browser()
        br._Browser__client.request.return_value = SimpleNamespace()

        br._Browser__request_with_waf_safe_mode(
            'https://example.com/admin',
            extra_headers={'X-Original-URL': '/admin'}
        )

        br._Browser__client.request.assert_called_once_with(
            'https://example.com/admin',
            extra_headers={'X-Original-URL': '/admin'}
        )

    @staticmethod
    def make_session_export_browser(**config_overrides):
        """
        Create a Browser instance with enough config fields for session export.

        :param dict config_overrides: config overrides
        :return: Browser
        """

        config = {
            'scan': 'directories',
            'scheme': 'https://',
            'is_ssl': True,
            'host': 'example.com',
            'port': 443,
            'proxy': '',
            'headers': [],
            'cookies': [],
            'raw_request': None,
            'request_body': None,
            'accept_cookies': False,
            'keep_alive': False,
            'is_fingerprint': False,
            'is_waf_detect': False,
            'is_waf_safe_mode': False,
            'wordlist': None,
            'reports': ['std'],
            'reports_dir': None,
            'is_random_user_agent': False,
            'is_random_list': False,
            'prefix': '',
            'extensions': None,
            'ignore_extensions': None,
            'is_recursive': False,
            'recursive_depth': 1,
            'recursive_status': [],
            'recursive_exclude': [],
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
            'timeout': 10,
            'retries': False,
            'debug': 0,
            'is_builtin_proxy_pool': False,
            'proxy_list': '',
            'is_external_proxy_list': False,
            'requested_method': 'HEAD',
            'is_auto_calibrate': False,
            'calibration_samples': 5,
            'calibration_threshold': 0.92,
            'is_header_bypass': True,
            'header_bypass_headers': ['X-Original-URL', 'X-Forwarded-For'],
            'header_bypass_ips': ['127.0.0.1', '10.0.0.1'],
            'header_bypass_status': [401, 403],
            'header_bypass_limit': 0,
            'header_bypass_profile': 'offensive',
            'session_save': '/tmp/session.json',
            'session_autosave_sec': 20,
            'session_autosave_items': 200,
        }
        config.update(config_overrides)

        br = Browser.__new__(Browser)
        setattr(br, '_Browser__config', SimpleNamespace(**config))
        return br

    def test_export_session_params_should_include_header_bypass_settings_when_enabled(self):
        """Session export should preserve header-bypass settings for resume."""

        br = self.make_session_export_browser()

        params = br._Browser__export_session_params()

        self.assertTrue(params['header_bypass'])
        self.assertEqual(params['header_bypass_headers'], 'X-Original-URL,X-Forwarded-For')
        self.assertEqual(params['header_bypass_ips'], '127.0.0.1,10.0.0.1')
        self.assertEqual(params['header_bypass_status'], '401,403')
        self.assertEqual(params['header_bypass_limit'], 0)
        self.assertEqual(params['header_bypass_profile'], 'offensive')

    def test_export_session_params_should_not_export_header_bypass_tuning_when_disabled(self):
        """Session export should avoid noisy header-bypass tuning when bypass is disabled."""

        br = self.make_session_export_browser(is_header_bypass=False)

        params = br._Browser__export_session_params()

        self.assertFalse(params['header_bypass'])
        self.assertNotIn('header_bypass_headers', params)
        self.assertNotIn('header_bypass_ips', params)
        self.assertNotIn('header_bypass_status', params)
        self.assertNotIn('header_bypass_limit', params)
        self.assertNotIn('header_bypass_profile', params)

    def test_http_request_ignores_empty_probe_http_response_object(self):
        """Browser should ignore probe requests that return no HTTP response object."""

        br = self.make_browser(
            header_bypass_headers=['X-Original-URL'],
            header_bypass_limit=1,
        )
        br._Browser__client.request.side_effect = [
            SimpleNamespace(),
            None,
        ]
        br._Browser__response.handle.side_effect = [
            ('forbidden', 'https://example.com/admin', '10B', '403'),
        ]

        br._Browser__http_request('https://example.com/admin', depth=0)

        self.assertEqual(br._Browser__client.request.call_count, 2)
        br._Browser__response.handle.assert_called_once()
        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['bypass'], 0)
        self.assertEqual(result['total']['forbidden'], 1)

    def test_probe_header_bypass_noops_for_legacy_object_without_config(self):
        """Header bypass probing should be a no-op for legacy Browser.__new__ objects without config."""

        br = Browser.__new__(Browser)

        br._Browser__probe_header_bypass(
            'https://example.com/admin',
            ('forbidden', 'https://example.com/admin', '10B', '403')
        )

        self.assertIsNone(getattr(br, '_Browser__header_bypass'))

if __name__ == '__main__':
    unittest.main()