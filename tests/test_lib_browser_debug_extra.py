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

        dbg = self.make_debug({'debug': 1, 'reports': 'std'})
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            dbg.debug_connection_pool('http_pool_start', None, 'HTTP')

        self.assertEqual(debug_mock.call_count, 1)

    def test_debug_proxy_pool_internal_and_none_modes(self):
        """Debug.debug_proxy_pool() should handle internal tor mode and no-proxy mode."""

        dbg = self.make_debug({'debug': 1, 'tor': True, 'reports': 'std'})
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

if __name__ == '__main__':
    unittest.main()