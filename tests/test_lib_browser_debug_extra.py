# -*- coding: utf-8 -*-

import unittest
from io import StringIO
from unittest.mock import patch

from src.core.logger.logger import Logger
from src.lib.browser.config import Config
from src.lib.browser.debug import Debug


class TestBrowserDebugExtra(unittest.TestCase):
    """TestBrowserDebugExtra class."""

    def tearDown(self):
        logger = Logger.log()
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    def make_debug(self, params):
        """Create Debug with isolated stdout."""

        with patch('sys.stdout', new=StringIO()):
            return Debug(Config(params))

    def test_init_with_zero_debug_does_not_log(self):
        """Debug.__init__() should not emit startup logs when debug level is zero."""

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg = self.make_debug({'debug': 0, 'reports': 'std'})

        self.assertEqual(dbg.level, 0)
        debug_mock.assert_not_called()

    def test_debug_list_handles_ignore_extensions_and_subdomains(self):
        """Debug.debug_list() should log ignore-extension, subdomain and default directory modes."""

        dbg = self.make_debug({'debug': 1, 'ignore_extensions': 'jpg,png', 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_list(5)
        keys = [call.kwargs.get('key') for call in debug_mock.call_args_list]
        self.assertIn('ext_ignore_filter', keys)

        dbg = self.make_debug({'debug': 1, 'scan': 'subdomains', 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_list(3)
        keys = [call.kwargs.get('key') for call in debug_mock.call_args_list]
        self.assertIn('subdomains', keys)

        dbg = self.make_debug({'debug': 1, 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_list(7)
        keys = [call.kwargs.get('key') for call in debug_mock.call_args_list]
        self.assertIn('directories', keys)

    def test_debug_connection_pool_without_pool_logs_once(self):
        """Debug.debug_connection_pool() should log only the header line when pool is missing."""

        dbg = self.make_debug({'debug': 2, 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_connection_pool('http_pool_start', None, 'HTTP')

        self.assertEqual(debug_mock.call_count, 1)

    def test_debug_proxy_pool_internal_and_none_modes(self):
        """Debug.debug_proxy_pool() should handle built-in proxy pool and no-proxy mode."""

        dbg = self.make_debug({'debug': 1, 'proxy_pool': True, 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_proxy_pool()
        debug_mock.assert_called_once_with(key='proxy_pool_internal_start')

        dbg = self.make_debug({'debug': 1, 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_proxy_pool()
        debug_mock.assert_not_called()

    def test_debug_request_uri_handles_forbidden_redirect_and_hidden_last_item(self):
        """Debug.debug_request_uri() should cover forbidden, redirect and hidden terminal cases."""

        dbg = self.make_debug({'debug': 1, 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.info') as info_mock, \
                patch('src.lib.browser.debug.tpl.line', side_effect=lambda *args, **kwargs: kwargs.get('url') or kwargs.get('msg') or 'line'), \
                patch('src.lib.browser.debug.sys.writels') as writels_mock:
            dbg.debug_request_uri('forbidden', 'http://test.local/path', items_size=1, total_size=2, content_size='0B', response_code='403')
            dbg.debug_request_uri('redirect', 'http://test.local/path', redirect_uri='http://test.local/next', items_size=1, total_size=2, content_size='0B', response_code='301')

        self.assertEqual(info_mock.call_count, 2)
        self.assertTrue(writels_mock.called)

        hidden = self.make_debug({'debug': -1, 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.line_log') as line_log_mock, \
                patch('src.lib.browser.debug.tpl.line', side_effect=lambda *args, **kwargs: kwargs.get('msg') or 'line'), \
                patch('src.lib.browser.debug.sys.writels') as writels_mock:
            hidden.debug_request_uri('ignored', 'http://test.local/path', items_size=2, total_size=2, content_size='0B', response_code='-')

        line_log_mock.assert_not_called()
        writels_mock.assert_called_once_with('', flush=True)

    def test_debug_request_uri_handles_blocked_status(self):
        """Debug.debug_request_uri() should render blocked responses as visible scan items."""

        dbg = self.make_debug({'debug': 1, 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.info') as info_mock, \
                patch('src.lib.browser.debug.tpl.line', side_effect=lambda *args, **kwargs: kwargs.get('url') or kwargs.get('msg') or 'line'), \
                patch('src.lib.browser.debug.sys.writels') as writels_mock:
            dbg.debug_request_uri(
                'blocked',
                'http://test.local/path',
                items_size=1,
                total_size=1,
                content_size='5KB',
                response_code='200'
            )

        info_mock.assert_called_once()
        writels_mock.assert_called_once_with('', flush=True)

    def test_debug_request_uri_renders_named_blocked_waf(self):
        """Debug.debug_request_uri() should show WAF vendor name and confidence for blocked responses."""

        dbg = self.make_debug({'debug': 1, 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.info') as info_mock, \
                patch('src.lib.browser.debug.tpl.line', side_effect=lambda *args, **kwargs: kwargs.get('msg') or kwargs.get('url') or 'line'), \
                patch('src.lib.browser.debug.sys.writels'):
            dbg.debug_request_uri(
                'blocked',
                'http://test.local/path',
                items_size=1,
                total_size=1,
                content_size='5KB',
                response_code='200',
                waf_name='Anubis',
                waf_confidence=95,
            )

        rendered_item = info_mock.call_args.kwargs.get('item')
        self.assertIn('WAF: Anubis (95%)', rendered_item)

class TestBrowserDebugSecurityHardening(unittest.TestCase):
    """Security-focused debug output hardening tests."""

    def tearDown(self):
        logger = Logger.log()
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    def make_debug(self):
        """Create Debug with isolated stdout."""

        with patch('sys.stdout', new=StringIO()):
            return Debug(Config({'debug': 2, 'reports': 'std'}))

    def test_debug_request_sensitive_headers_without_mutating_input(self):
        """Debug request output should not expose secrets from request headers."""

        dbg = self.make_debug()
        headers = {
            'Authorization': 'Bearer secret-token',
            'Cookie': 'sid=secret-cookie',
            'X-Api-Key': 'secret-api-key',
            'X-Test': 'visible',
        }

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(dbg.debug_request(headers, 'http://test.local/', 'GET'))

        payload = debug_mock.call_args.kwargs.get('dbg', '')

        self.assertIn('secret-token', payload)
        self.assertIn('secret-cookie', payload)
        self.assertIn('secret-api-key', payload)
        self.assertIn('visible', payload)
        self.assertEqual(headers['Authorization'], 'Bearer secret-token')

class TestBrowserDebugCoverageOnly(unittest.TestCase):
    """Coverage-only tests for debug level helper branches."""

    def tearDown(self):
        logger = Logger.log()
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    def make_debug(self, params):
        """Create Debug with isolated stdout."""

        with patch('sys.stdout', new=StringIO()):
            return Debug(Config(params))

    def test_normalize_debug_headers_accepts_iterables_and_plain_objects(self):
        """Debug response normalization should accept iterable and object-like headers."""

        dbg = self.make_debug({'debug': 3, 'reports': 'std'})

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_response([('Server', 'nginx')])
        self.assertIn('nginx', debug_mock.call_args.kwargs.get('dbg', ''))

        class HeaderObject(object):
            def __init__(self):
                self.Server = 'Apache'

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_response(HeaderObject())
        self.assertIn('Apache', debug_mock.call_args.kwargs.get('dbg', ''))

    def test_level_gates_skip_lower_level_debug_messages(self):
        """Level gates should suppress request/response/scan debug below their thresholds."""

        dbg = self.make_debug({'debug': 0, 'reports': 'std'})

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(dbg.debug_connection_pool('http_pool_start', object(), 'HTTP'))
            self.assertTrue(dbg.debug_proxy_pool())
            self.assertTrue(dbg.debug_request({'A': 'B'}, 'http://test.local/', 'GET'))
            self.assertTrue(dbg.debug_response({'Status': '200'}))
            self.assertTrue(dbg.debug_load_sniffer_plugin('plugin'))
            self.assertTrue(dbg.debug_cookie_accept_enabled())
            self.assertTrue(dbg.debug_cookie_accepted('sid=1'))
            self.assertTrue(dbg.debug_cookie_attached({'Cookie': 'sid=1'}))
            self.assertTrue(dbg.debug_auto_calibration_enabled())
            self.assertTrue(dbg.debug_header_bypass_skipped(403))
            self.assertTrue(dbg.debug_header_bypass_probing(403, 2))
            self.assertTrue(dbg.debug_header_bypass_candidate({'bypass_header': 'X-Test'}))
            self.assertTrue(dbg.debug_header_bypass_finished())
            self.assertTrue(dbg.debug_recursive_expansion('/admin', 2, 1))
            self.assertTrue(dbg.debug_classification('success', code=200, size='1KB'))

        debug_mock.assert_not_called()

    def test_level_one_runtime_helpers_emit_scan_decisions(self):
        """Level 1 should emit scanner decision helper messages."""

        dbg = self.make_debug({'debug': 1, 'reports': 'std', 'auto_calibrate': True, 'header_bypass': True})

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_load_sniffer_plugin('Test sniffer')
            dbg.debug_auto_calibration_enabled()
            dbg.debug_header_bypass_skipped(None)
            dbg.debug_header_bypass_probing(403, 3)
            dbg.debug_header_bypass_candidate({'bypass_variant': 'X-Original-URL: /admin'})
            dbg.debug_header_bypass_finished()
            dbg.debug_recursive_expansion('/admin', 4, 2)

        keys = [call.kwargs.get('key') for call in debug_mock.call_args_list]
        messages = [call.kwargs.get('msg', '') for call in debug_mock.call_args_list]

        self.assertIn('load_sniffer_plugin', keys)
        self.assertIn('header_bypass_skipped', keys)
        self.assertIn('header_bypass_probing', keys)
        self.assertIn('header_bypass_candidate', keys)
        self.assertIn('header_bypass_finished', keys)
        self.assertTrue(any('Auto-calibration enabled' in message for message in messages))
        self.assertTrue(any('Recursive expansion' in message for message in messages))

    def test_level_two_cookie_helpers_emit_request_diagnostics(self):
        """Level 2 should emit cookie lifecycle diagnostics."""

        dbg = self.make_debug({'debug': 2, 'reports': 'std'})

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_cookie_accept_enabled()
            dbg.debug_cookie_accepted('sid=1')
            dbg.debug_cookie_attached({'Cookie': 'sid=1'})
            dbg.debug_cookie_attached({'X-Test': '1'})
            dbg.debug_cookie_attached(object())

        keys = [call.kwargs.get('key') for call in debug_mock.call_args_list]
        self.assertEqual(keys.count('accept_cookies_enabled'), 1)
        self.assertEqual(keys.count('response_cookies_accepted'), 1)
        self.assertEqual(keys.count('cookie_header_attached'), 1)

    def test_level_three_classification_emits_response_diagnostics(self):
        """Level 3 should emit classification and WAF signal diagnostics."""

        dbg = self.make_debug({'debug': 3, 'reports': 'std'})

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_classification(
                'blocked',
                code=403,
                size='2KB',
                waf_name='Cloudflare',
                waf_confidence=92,
                signals=['header:cf-ray'],
                redirect_uri='https://test.local/login',
            )

        messages = [call.kwargs.get('msg', '') for call in debug_mock.call_args_list]
        self.assertTrue(any('Classification: blocked' in message for message in messages))
        self.assertTrue(any('redirect=https://test.local/login' in message for message in messages))
        self.assertTrue(any('WAF signals: header:cf-ray' in message for message in messages))


    def test_debug_classification_should_log_stacktrace_detection_metadata(self):
        """Debug classification should accept and log stacktrace metadata."""

        debug = self.make_debug({'debug': 3, 'reports': 'std'})
        detection = {
            'type': 'stacktrace',
            'runtime': 'PHP',
            'signal': 'Fatal error',
            'confidence': 95,
        }

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            result = debug.debug_classification(
                'stacktrace',
                code=200,
                size='796B',
                stacktrace_detection=detection,
            )

        self.assertTrue(result)
        messages = [
            call.kwargs.get('msg')
            for call in debug_mock.call_args_list
            if call.kwargs.get('msg')
        ]

        self.assertIn('Classification: stacktrace; code=200; size=796B', messages)
        self.assertIn('StackTrace detection: runtime=PHP; signal=Fatal error; confidence=95', messages)


if __name__ == '__main__':
    unittest.main()
