# -*- coding: utf-8 -*-

import unittest
from io import StringIO
from unittest.mock import patch

from src.core.logger.logger import Logger
from src.lib.browser.config import Config
from src.lib.browser.debug import Debug


class HeaderObject(object):
    def __init__(self):
        self.Accept = '*/*'


class TestBrowserDebug(unittest.TestCase):
    """TestBrowserDebug class."""

    def setUp(self):
        self.config = Config({
            'debug': 1,
            'method': 'HEAD',
            'random_agent': False,
            'random_list': True,
            'threads': 1,
            'reports': 'std',
        })
        with patch('sys.stdout', new=StringIO()):
            self.debug = Debug(self.config)

    def tearDown(self):
        logger = Logger.log()
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    def test_level(self):
        """Debug.level should expose the configured level."""

        self.assertEqual(self.debug.level, 1)

    def test_debug_user_agents_logs_browser_or_random_mode(self):
        """Debug.debug_user_agents() should log either browser or random browser mode."""

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(self.debug.debug_user_agents())

        debug_mock.assert_called_with(key='browser', browser=self.config.user_agent)

        random_config = Config({'debug': 1, 'method': 'HEAD', 'random_agent': True, 'reports': 'std'})
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(random_config)
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_user_agents())
        debug_mock.assert_called_with(key='random_browser')

    def test_debug_list_logs_random_and_extension_modes(self):
        """Debug.debug_list() should log scan-list mode details."""

        ext_config = Config({
            'debug': 1,
            'method': 'HEAD',
            'random_list': True,
            'extensions': 'php,html',
            'threads': 2,
            'reports': 'std',
        })
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(ext_config)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_list(10))

        called_keys = [call.kwargs.get('key') for call in debug_mock.call_args_list]
        self.assertIn('randomizing', called_keys)
        self.assertIn('ext_filter', called_keys)
        self.assertIn('create_queue', called_keys)

    def test_debug_connection_pool_logs_pool_string_when_present(self):
        """Debug.debug_connection_pool() should log pool details at request-debug level."""

        cfg = Config({'debug': 2, 'method': 'HEAD', 'reports': 'std'})
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_connection_pool('http_pool_start', 'POOL', 'HTTP'))

        self.assertEqual(debug_mock.call_count, 2)

    def test_debug_header_bypass_logs_configuration_when_enabled(self):
        """Debug.debug_header_bypass() should expose active header-bypass settings."""

        cfg = Config({
            'debug': 1,
            'method': 'HEAD',
            'header_bypass': True,
            'header_bypass_status': ['401', '403'],
            'header_bypass_limit': 12,
            'header_bypass_headers': ['X-Original-URL', 'X-Forwarded-For'],
            'reports': 'std',
        })
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_header_bypass())

        debug_mock.assert_called_once_with(
            key='header_bypass_enabled',
            statuses='401,403',
            limit=12,
            headers=2
        )

    def test_debug_header_bypass_noops_when_disabled(self):
        """Debug.debug_header_bypass() should not log when header-bypass is disabled."""

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(self.debug.debug_header_bypass())

        debug_mock.assert_not_called()

    def test_debug_proxy_pool_logs_matching_mode(self):
        """Debug.debug_proxy_pool() should log the selected proxy mode."""

        ext_cfg = Config({'debug': 1, 'method': 'HEAD', 'proxy_list': 'proxy.txt', 'reports': 'std'})
        with patch('sys.stdout', new=StringIO()):
            ext_debug = Debug(ext_cfg)
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(ext_debug.debug_proxy_pool())
        debug_mock.assert_called_with(key='proxy_pool_external_start')

        standalone_cfg = Config({'debug': 1, 'method': 'HEAD', 'proxy': 'http://127.0.0.1:8080', 'reports': 'std'})
        with patch('sys.stdout', new=StringIO()):
            standalone_debug = Debug(standalone_cfg)
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(standalone_debug.debug_proxy_pool())
        debug_mock.assert_called_with(key='proxy_pool_standalone', server=standalone_cfg.proxy)

        auth_cfg = Config({
            'debug': 1,
            'method': 'HEAD',
            'proxy': 'http://user:pass@127.0.0.1:8080',
            'reports': 'std',
        })
        with patch('sys.stdout', new=StringIO()):
            auth_debug = Debug(auth_cfg)
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(auth_debug.debug_proxy_pool())
        debug_mock.assert_called_with(key='proxy_pool_standalone', server='http://user:*****@127.0.0.1:8080')

    def test_debug_proxy_selected_logs_masked_rotating_proxy(self):
        """Debug.debug_proxy_selected() should mask selected rotating proxy credentials."""

        cfg = Config({'debug': 1, 'method': 'HEAD', 'proxy_list': 'proxy.txt', 'reports': 'std'})
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_proxy_selected('http://user:pass@127.0.0.1:8080'))

        debug_mock.assert_called_once_with(
            key='proxy_pool_selected',
            server='http://user:*****@127.0.0.1:8080',
        )

    def test_debug_proxy_selected_includes_rotation_when_provided(self):
        """Debug.debug_proxy_selected() should append the selected rotation policy."""

        cfg = Config({'debug': 1, 'method': 'HEAD', 'proxy_list': 'proxy.txt', 'reports': 'std'})
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_proxy_selected('http://user:pass@127.0.0.1:8080', 'sequential'))

        debug_mock.assert_called_once_with(
            key='proxy_pool_selected',
            server='http://user:*****@127.0.0.1:8080 (sequential)',
        )

    def test_debug_request_does_not_mutate_input_dict(self):
        """Debug.debug_request() should not mutate the original request header mapping."""

        cfg = Config({'debug': 2, 'method': 'HEAD', 'reports': 'std'})
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(cfg)

        headers = {'Accept': '*/*'}
        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_request(headers, 'http://test.local/data/', 'HEAD'))

        self.assertEqual(headers, {'Accept': '*/*'})
        debug_mock.assert_called_once()

    def test_debug_request_accepts_object_headers(self):
        """Debug.debug_request() should accept header objects exposing __dict__."""

        cfg = Config({'debug': 2, 'method': 'HEAD', 'reports': 'std'})
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_request(HeaderObject(), 'http://test.local/data/', 'HEAD'))

        debug_mock.assert_called_once()

    def test_debug_response_logs_serialized_headers(self):
        """Debug.debug_response() should log serialized response headers."""

        cfg = Config({'debug': 3, 'method': 'HEAD', 'reports': 'std'})
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_response({'Server': 'test'}))

        debug_mock.assert_called_once()

    def test_debug_request_uri_logs_supported_statuses(self):
        """Debug.debug_request_uri() should log informational output for handled statuses."""

        with patch('src.lib.browser.debug.tpl.info') as info_mock, \
                patch('src.lib.browser.debug.tpl.line', side_effect=lambda *args, **kwargs: kwargs.get('msg') or kwargs.get('url') or 'line'), \
                patch('src.lib.browser.debug.sys.writels') as writels_mock:
            self.assertTrue(self.debug.debug_request_uri('success', 'http://test.local/data/', items_size=1, total_size=1, content_size='2B', response_code='200'))

        info_mock.assert_called_once()
        writels_mock.assert_called()

    def test_debug_request_uri_logs_unhandled_statuses_as_scan_items(self):
        """Debug.debug_request_uri() should keep dictionary scan URI visible for unhandled statuses."""

        with patch('src.lib.browser.debug.tpl.line_log') as line_log_mock, \
                patch('src.lib.browser.debug.tpl.line', side_effect=lambda *args, **kwargs: kwargs.get('msg') or kwargs.get('url') or 'line'), \
                patch('src.lib.browser.debug.sys.writels') as writels_mock:
            self.assertTrue(
                self.debug.debug_request_uri(
                    'ignored',
                    'http://test.local/data/',
                    items_size=1,
                    total_size=1,
                    content_size='28KB',
                    response_code='404',
                )
            )

        line_log_mock.assert_called_once_with(
            key='get_item',
            percent='100.0%',
            current='1',
            total=1,
            item='/data/',
            size='28KB',
            code='404',
        )
        writels_mock.assert_called_once_with('', flush=True)

    def test_debug_user_agents_noops_when_debug_disabled(self):
        """Debug.debug_user_agents() should not log when debug output is disabled."""

        cfg = Config({
            'debug': 0,
            'method': 'HEAD',
            'random_agent': True,
            'reports': 'std',
        })
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_user_agents())

        debug_mock.assert_not_called()

    def test_debug_list_noops_when_debug_disabled(self):
        """Debug.debug_list() should not log scan-list details when debug output is disabled."""

        cfg = Config({
            'debug': 0,
            'method': 'HEAD',
            'random_list': True,
            'extensions': 'php,html',
            'threads': 2,
            'reports': 'std',
        })
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(debug.debug_list(10))

        debug_mock.assert_not_called()

    def test_debug_request_uri_uses_raw_uri_for_subdomain_scan(self):
        """Debug.debug_request_uri() should not parse URL paths in subdomain scan mode."""

        cfg = Config({
            'debug': 1,
            'method': 'HEAD',
            'scan': 'subdomains',
            'reports': 'std',
        })
        with patch('sys.stdout', new=StringIO()):
            debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.info') as info_mock, \
                patch('src.lib.browser.debug.tpl.line', side_effect=lambda *args, **kwargs: kwargs.get('msg') or kwargs.get('url') or 'line'), \
                patch('src.lib.browser.debug.sys.writels'):
            self.assertTrue(
                debug.debug_request_uri(
                    'success',
                    'api.example.com',
                    items_size=1,
                    total_size=1,
                    content_size='0B',
                    response_code='200',
                )
            )

        self.assertEqual(info_mock.call_args.kwargs['item'], 'api.example.com')

    def test_debug_request_uri_does_not_flush_for_non_final_unhandled_status(self):
        """Debug.debug_request_uri() should flush only after the last unhandled scan item."""

        with patch('src.lib.browser.debug.tpl.line_log') as line_log_mock, \
                patch('src.lib.browser.debug.tpl.line', side_effect=lambda *args, **kwargs: kwargs.get('msg') or kwargs.get('url') or 'line'), \
                patch('src.lib.browser.debug.sys.writels') as writels_mock:
            self.assertTrue(
                self.debug.debug_request_uri(
                    'ignored',
                    'http://test.local/data/',
                    items_size=1,
                    total_size=2,
                    content_size='28KB',
                    response_code='404',
                )
            )

        line_log_mock.assert_called_once()
        writels_mock.assert_not_called()

    def test_debug_load_sniffer_plugin_logs_description(self):
        """Debug.debug_load_sniffer_plugin() should log the plugin description."""

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            self.assertTrue(self.debug.debug_load_sniffer_plugin('test sniffer'))

        debug_mock.assert_called_once_with(key='load_sniffer_plugin', description='test sniffer')


if __name__ == '__main__':
    unittest.main()
