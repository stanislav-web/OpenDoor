# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib3.exceptions import MaxRetryError, ProxySchemeUnknown, ReadTimeoutError
from urllib3.response import HTTPResponse

from src.core.http.exceptions import ProxyRequestError
from src.core.http.proxy import Proxy


class TestProxyExtra(unittest.TestCase):
    """TestProxyExtra class."""

    @staticmethod
    def make_cfg(**overrides):
        """Create a minimal config namespace for Proxy tests."""

        base = {
            'keep_alive': False,
            'is_standalone_proxy': True,
            'proxy': 'http://127.0.0.1:8080',
            'threads': 2,
            'timeout': 1,
            'retries': False,
            'accept_cookies': False,
            'method': 'HEAD',
            'DEFAULT_SCAN': 'directories',
            'scan': 'directories',
            'is_random_user_agent': False,
            'user_agent': 'UA',
            'scheme': 'http://',
            'host': 'example.com',
            'port': 80,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @staticmethod
    def make_debug(level=0):
        """Create a simple debug stub."""

        return SimpleNamespace(
            level=level,
            debug_proxy_pool=MagicMock(),
            debug_request=MagicMock(),
        )

    def test_init_rejects_empty_proxy_list_for_non_standalone_mode(self):
        """Proxy should reject empty proxy lists when standalone proxy is disabled."""

        cfg = self.make_cfg(is_standalone_proxy=False)

        with self.assertRaises(ProxyRequestError):
            Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=[], agent_list=['UA'])

    def test_get_random_proxy_returns_stripped_value(self):
        """Proxy.__get_random_proxy() should return a stripped proxy server string."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        proxy = Proxy(
            cfg,
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=[' http://one:8080 ', ' https://two:8443 '],
            agent_list=['UA'],
        )

        with patch('src.core.http.proxy.random.randrange', return_value=1):
            actual = getattr(proxy, '_Proxy__get_random_proxy')()

        self.assertEqual(actual, 'https://two:8443')

    def test_get_proxy_type_detects_socks_https_and_http(self):
        """Proxy.__get_proxy_type() should classify supported proxy schemes."""

        proxy_type = getattr(Proxy, '_Proxy__get_proxy_type')

        self.assertEqual(proxy_type('socks5://127.0.0.1:9050'), 'socks')
        self.assertEqual(proxy_type('https://proxy.example.com'), 'https')
        self.assertEqual(proxy_type('http://proxy.example.com'), 'http')

    def test_proxy_pool_uses_proxy_manager_for_http_proxy(self):
        """Proxy.__proxy_pool() should use ProxyManager for non-socks proxies."""

        cfg = self.make_cfg(is_standalone_proxy=True, proxy='http://127.0.0.1:8080')
        pool = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch('src.core.http.proxy.ProxyManager', return_value=pool) as proxy_manager_mock:
            actual = getattr(proxy, '_Proxy__proxy_pool')()

        self.assertIs(actual, pool)
        proxy_manager_mock.assert_called_once()

    def test_proxy_pool_uses_socks_manager_and_disables_warnings(self):
        """Proxy.__proxy_pool() should use the SOCKS manager and disable warnings for socks proxies."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        pool = MagicMock()
        socks_manager = MagicMock(return_value=pool)
        package_module = SimpleNamespace(SOCKSProxyManager=socks_manager)

        proxy = Proxy(
            cfg,
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=['socks5://127.0.0.1:9050'],
            agent_list=['UA'],
        )

        with patch('src.core.http.proxy.random.randrange', return_value=0), \
                patch('src.core.http.proxy.disable_warnings') as disable_mock, \
                patch('src.core.http.proxy.importlib.import_module', return_value=package_module):
            actual = getattr(proxy, '_Proxy__proxy_pool')()

        self.assertIs(actual, pool)
        disable_mock.assert_called_once()
        socks_manager.assert_called_once()

    def test_proxy_pool_wraps_proxy_scheme_errors(self):
        """Proxy.__proxy_pool() should wrap proxy scheme errors as ProxyRequestError."""

        cfg = self.make_cfg(is_standalone_proxy=True, proxy='http://127.0.0.1:8080')
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch('src.core.http.proxy.ProxyManager', side_effect=ProxySchemeUnknown('bad-scheme')):
            with self.assertRaises(ProxyRequestError):
                getattr(proxy, '_Proxy__proxy_pool')()

    def test_pool_request_uses_proxy_pool_and_routes_cookies(self):
        """Proxy.__pool_request() should delegate to the selected pool and route cookies."""

        cfg = self.make_cfg(is_standalone_proxy=True)
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        response = HTTPResponse(status=200, body=b'ok', headers={})
        pool = MagicMock()
        pool.request.return_value = response

        with patch.object(proxy, '_Proxy__proxy_pool', return_value=pool), \
                patch.object(proxy, 'cookies_middleware') as cookies_mock:
            actual = getattr(proxy, '_Proxy__pool_request')('http://example.com/path')

        self.assertEqual(actual.status, 200)
        pool.request.assert_called_once()
        cookies_mock.assert_called_once_with(is_accept=False, response=response)

    def test_request_sets_headers_and_uses_debug_path(self):
        """Proxy.request() should populate headers and call debug_request when debug level is high."""

        cfg = self.make_cfg(keep_alive=True)
        debug = self.make_debug(level=99)
        proxy = Proxy(cfg, debug, tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        response = HTTPResponse(status=200, body=b'ok', headers={})

        with patch.object(proxy, '_Proxy__pool_request', return_value=response) as pool_request_mock:
            actual = proxy.request('http://example.com/path')

        self.assertEqual(actual.status, 200)
        pool_request_mock.assert_called_once_with('http://example.com/path')
        debug.debug_request.assert_called_once()

        headers = debug.debug_request.call_args.args[0]
        self.assertEqual(headers['User-Agent'], 'UA')
        self.assertEqual(headers['Connection'], 'keep-alive')

    def test_request_retries_once_on_max_retry_for_default_scan(self):
        """Proxy.request() should warn and retry once on MaxRetryError for default scan mode."""

        cfg = self.make_cfg(scan='directories')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])
        proxy._Proxy__server = 'http://127.0.0.1:8080'

        response = HTTPResponse(status=200, body=b'ok', headers={})

        with patch.object(proxy, '_Proxy__pool_request', side_effect=[MaxRetryError(None, '/', None), response]):
            actual = proxy.request('http://example.com/path')

        self.assertEqual(actual.status, 200)
        tpl.warning.assert_called_once()

    def test_request_suppresses_retry_warning_for_non_default_scan(self):
        """Proxy.request() should not warn or retry on MaxRetryError for non-default scan mode."""

        cfg = self.make_cfg(scan='subdomains')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__pool_request', side_effect=MaxRetryError(None, '/', None)):
            self.assertIsNone(proxy.request('http://api.example.com'))

        tpl.warning.assert_not_called()

    def test_request_warns_on_read_timeout_for_default_scan(self):
        """Proxy.request() should warn on ReadTimeoutError for default scan mode."""

        cfg = self.make_cfg(scan='directories')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__pool_request', side_effect=ReadTimeoutError(None, '/', 'x')):
            self.assertIsNone(proxy.request('http://example.com/path'))

        tpl.warning.assert_called_once()

    def test_request_suppresses_read_timeout_warning_for_non_default_scan(self):
        """Proxy.request() should not warn on ReadTimeoutError for non-default scan mode."""

        cfg = self.make_cfg(scan='subdomains')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__pool_request', side_effect=ReadTimeoutError(None, '/', 'x')):
            self.assertIsNone(proxy.request('http://api.example.com'))

        tpl.warning.assert_not_called()


if __name__ == '__main__':
    unittest.main()