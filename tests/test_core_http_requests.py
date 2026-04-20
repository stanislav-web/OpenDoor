# -*- coding: utf-8 -*-

import socket
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib3.exceptions import MaxRetryError, ReadTimeoutError, ConnectTimeoutError, HostChangedError, ProxySchemeUnknown, SSLError
from urllib3.response import HTTPResponse

from src.core.http.http import HttpRequest
from src.core.http.https import HttpsRequest
from src.core.http.proxy import Proxy
from src.core.http.socks import Socket
from src.core.http.exceptions import HttpRequestError, HttpsRequestError, ProxyRequestError, SocketError


class TestHttpRequest(unittest.TestCase):
    """TestHttpRequest class."""

    def make_cfg(self, **kwargs):
        base = dict(
            host='example.com',
            port=80,
            threads=1,
            timeout=1,
            keep_alive=False,
            DEFAULT_SCAN='directories',
            scan='directories',
            retries=False,
            accept_cookies=False,
            method='HEAD',
            scheme='http://',
            is_random_user_agent=False,
            user_agent='UA',
        )
        base.update(kwargs)
        return SimpleNamespace(**base)

    def test_init_and_request_directory(self):
        """HttpRequest.request() should use the connection pool for directory scans."""

        cfg = self.make_cfg()
        debug = SimpleNamespace(level=0)
        req = HttpRequest(cfg, debug, tpl=MagicMock(), agent_list=['UA'])

        response = HTTPResponse(status=200, body=b'ok', headers={})
        pool = MagicMock()
        pool.request.return_value = response
        req._HttpRequest__pool = pool

        out = req.request('http://example.com/path')

        self.assertEqual(out.status, 200)
        pool.request.assert_called_once()

    def test_request_subdomain_uses_poolmanager(self):
        """HttpRequest.request() should use PoolManager for subdomain scans."""

        cfg = self.make_cfg(scan='subdomains')
        debug = SimpleNamespace(level=0)

        with patch('src.core.http.http.PoolManager') as pm_cls:
            pm = pm_cls.return_value
            pm.request.return_value = HTTPResponse(status=200, body=b'ok', headers={})

            req = HttpRequest(cfg, debug, tpl=MagicMock(), agent_list=['UA'])
            out = req.request('http://api.example.com')

        self.assertEqual(out.status, 200)
        pm.request.assert_called_once()

    def test_request_handles_errors(self):
        """HttpRequest.request() should handle retry and timeout related errors."""

        cfg = self.make_cfg()
        tpl = MagicMock()
        req = HttpRequest(cfg, SimpleNamespace(level=0), tpl=tpl, agent_list=['UA'])
        pool = MagicMock()
        req._HttpRequest__pool = pool

        pool.request.side_effect = MaxRetryError(None, '/', None)
        self.assertIsNone(req.request('http://example.com/x'))
        tpl.warning.assert_called()

        for exc in [HostChangedError(None, '/', 0), ReadTimeoutError(None, '/', 'x'), ConnectTimeoutError(None, '/', 'x')]:
            pool.request.reset_mock(side_effect=True)
            tpl.warning.reset_mock()
            pool.request.side_effect = exc
            self.assertIsNone(req.request('http://example.com/x'))
            self.assertTrue(tpl.warning.called)

    def test_init_wraps_errors(self):
        """HttpRequest.__init__() should wrap provider setup failures."""

        cfg = self.make_cfg()
        with patch('src.core.http.http.RequestProvider.__init__', side_effect=TypeError('bad')):
            with self.assertRaises(HttpRequestError):
                HttpRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])


class TestHttpsRequest(unittest.TestCase):
    """TestHttpsRequest class."""

    def make_cfg(self, **kwargs):
        base = dict(
            host='example.com',
            port=443,
            threads=1,
            timeout=1,
            keep_alive=False,
            DEFAULT_SCAN='directories',
            scan='directories',
            retries=False,
            accept_cookies=False,
            method='HEAD',
            scheme='https://',
            is_random_user_agent=False,
            user_agent='UA',
        )
        base.update(kwargs)
        return SimpleNamespace(**base)

    def test_provide_ssl_auth_required(self):
        """HttpsRequest should provide a synthetic SSL-auth-required response."""

        req = HttpsRequest(self.make_cfg(), SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])
        response = req._provide_ssl_auth_required()

        self.assertEqual(response.status, 496)

    def test_request_directory_and_subdomain(self):
        """HttpsRequest.request() should support both directory and subdomain modes."""

        debug = SimpleNamespace(level=0)
        cfg = self.make_cfg()
        req = HttpsRequest(cfg, debug, tpl=MagicMock(), agent_list=['UA'])

        pool = MagicMock()
        pool.request.return_value = HTTPResponse(status=200, body=b'ok', headers={})
        req._HttpsRequest__pool = pool
        self.assertEqual(req.request('https://example.com/x').status, 200)

        cfg2 = self.make_cfg(scan='subdomains')
        with patch('src.core.http.https.PoolManager') as pm_cls:
            pm = pm_cls.return_value
            pm.request.return_value = HTTPResponse(status=200, body=b'ok', headers={})

            req2 = HttpsRequest(cfg2, debug, tpl=MagicMock(), agent_list=['UA'])
            self.assertEqual(req2.request('https://api.example.com').status, 200)
            pm.request.assert_called_once()

    def test_request_handles_ssl_and_timeouts(self):
        """HttpsRequest.request() should handle SSL-specific and timeout failures."""

        cfg = self.make_cfg()
        tpl = MagicMock()
        req = HttpsRequest(cfg, SimpleNamespace(level=0), tpl=tpl, agent_list=['UA'])
        pool = MagicMock()
        req._HttpsRequest__pool = pool

        pool.request.side_effect = SSLError(None)
        self.assertIsNone(req.request('https://example.com/x'))

        cfg_sub = self.make_cfg(scan='subdomains')
        req_sub = HttpsRequest(cfg_sub, SimpleNamespace(level=0), tpl=tpl, agent_list=['UA'])
        with patch('src.core.http.https.PoolManager') as pm_cls:
            pm = pm_cls.return_value
            pm.request.side_effect = SSLError(None)
            response = req_sub.request('https://api.example.com')
        self.assertEqual(response.status, 496)

        for exc in [MaxRetryError(None, '/', None), HostChangedError(None, '/', 0), ReadTimeoutError(None, '/', 'x'), ConnectTimeoutError(None, '/', 'x')]:
            pool.request.reset_mock(side_effect=True)
            tpl.warning.reset_mock()
            pool.request.side_effect = exc
            self.assertIsNone(req.request('https://example.com/x'))
            self.assertTrue(tpl.warning.called)

    def test_init_wraps_errors(self):
        """HttpsRequest.__init__() should wrap provider setup failures."""

        cfg = self.make_cfg()
        with patch('src.core.http.https.RequestProvider.__init__', side_effect=TypeError('bad')):
            with self.assertRaises(HttpsRequestError):
                HttpsRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])


class TestProxy(unittest.TestCase):
    """TestProxy class."""

    def make_cfg(self, **kwargs):
        base = dict(
            host='example.com',
            port=80,
            threads=1,
            timeout=1,
            keep_alive=False,
            DEFAULT_SCAN='directories',
            scan='directories',
            retries=False,
            accept_cookies=False,
            method='HEAD',
            scheme='http://',
            is_random_user_agent=False,
            user_agent='UA',
            is_standalone_proxy=False,
            proxy='',
            is_tor=False,
        )
        base.update(kwargs)
        return SimpleNamespace(**base)

    def test_init_rejects_empty_list(self):
        """Proxy.__init__() should reject an empty proxy list for non-standalone mode."""

        with self.assertRaises(ProxyRequestError):
            Proxy(self.make_cfg(), SimpleNamespace(level=0, debug_proxy_pool=lambda: None), tpl=MagicMock(), proxy_list=[], agent_list=['UA'])

    def test_proxy_pool_http_and_request(self):
        """Proxy.request() should work with regular HTTP proxies."""

        debug = SimpleNamespace(level=0, debug_proxy_pool=lambda: None)
        proxy = Proxy(self.make_cfg(), debug, tpl=MagicMock(), proxy_list=['http://127.0.0.1:8080'], agent_list=['UA'])

        with patch('src.core.http.proxy.ProxyManager') as pm_cls:
            pm = pm_cls.return_value
            pm.request.return_value = HTTPResponse(status=200, body=b'ok', headers={})
            out = proxy.request('http://example.com/x')

        self.assertEqual(out.status, 200)

    def test_proxy_pool_socks(self):
        """Proxy.request() should work with SOCKS proxies."""

        debug = SimpleNamespace(level=0, debug_proxy_pool=lambda: None)
        proxy = Proxy(self.make_cfg(), debug, tpl=MagicMock(), proxy_list=['socks5://127.0.0.1:9050'], agent_list=['UA'])

        fake_pool = MagicMock()
        fake_pool.request.return_value = HTTPResponse(status=200, body=b'ok', headers={})

        with patch('src.core.http.proxy.importlib.import_module') as import_mod:
            import_mod.return_value = SimpleNamespace(SOCKSProxyManager=MagicMock(return_value=fake_pool))
            out = proxy.request('http://example.com/x')

        self.assertEqual(out.status, 200)

    def test_proxy_request_retries_on_max_retry(self):
        """Proxy.request() should retry once on MaxRetryError."""

        debug = SimpleNamespace(level=0, debug_proxy_pool=lambda: None)
        tpl = MagicMock()
        proxy = Proxy(self.make_cfg(), debug, tpl=tpl, proxy_list=['http://127.0.0.1:8080'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__pool_request', side_effect=[MaxRetryError(None, '/', None), HTTPResponse(status=200, body=b'ok', headers={})]):
            out = proxy.request('http://example.com/x')

        self.assertEqual(out.status, 200)
        tpl.warning.assert_called_once()

    def test_proxy_request_timeout_and_import_errors(self):
        """Proxy.request() should handle timeout warnings and proxy pool setup errors."""

        debug = SimpleNamespace(level=0, debug_proxy_pool=lambda: None)
        tpl = MagicMock()
        proxy = Proxy(self.make_cfg(), debug, tpl=tpl, proxy_list=['http://127.0.0.1:8080'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__pool_request', side_effect=ReadTimeoutError(None, '/', 'x')):
            self.assertIsNone(proxy.request('http://example.com/x'))
            tpl.warning.assert_called_once()

        with patch('src.core.http.proxy.ProxyManager', side_effect=ProxySchemeUnknown('bad')):
            with self.assertRaises(ProxyRequestError):
                proxy._Proxy__pool_request('http://example.com/x')

    def test_get_proxy_type_and_random_proxy(self):
        """Proxy helpers should detect proxy type and return a trimmed random proxy."""

        self.assertEqual(Proxy._Proxy__get_proxy_type('socks5://x'), 'socks')
        self.assertEqual(Proxy._Proxy__get_proxy_type('https://x'), 'https')
        self.assertEqual(Proxy._Proxy__get_proxy_type('http://x'), 'http')

        debug = SimpleNamespace(level=0, debug_proxy_pool=lambda: None)
        proxy = Proxy(self.make_cfg(), debug, tpl=MagicMock(), proxy_list=[' http://127.0.0.1:8080 '], agent_list=['UA'])

        with patch('src.core.http.proxy.random.randrange', return_value=0):
            self.assertEqual(proxy._Proxy__get_random_proxy(), 'http://127.0.0.1:8080')


class TestSocket(unittest.TestCase):
    """TestSocket class."""

    def test_ping_and_ip_helpers(self):
        """Socket helpers should ping and resolve IP addresses."""

        fake_socket = MagicMock()
        with patch('src.core.http.socks.socket.socket', return_value=fake_socket):
            Socket.ping('example.com', 80, timeout=1)

        fake_socket.settimeout.assert_called_once_with(1)
        fake_socket.connect.assert_called_once_with(('example.com', 80))
        fake_socket.close.assert_called_once()

        with patch('src.core.http.socks.socket.gethostbyname', return_value='127.0.0.1'):
            self.assertEqual(Socket.get_ip_address('example.com'), '127.0.0.1')

        with patch('src.core.http.socks.socket.gethostbyname_ex', return_value=('example.com', [], ['1.1.1.1', '2.2.2.2'])):
            self.assertEqual(Socket.get_ips_addresses('example.com'), '[1.1.1.1, 2.2.2.2]')

    def test_socket_wraps_errors(self):
        """Socket helpers should wrap low-level socket errors."""

        fake_socket = MagicMock()
        fake_socket.connect.side_effect = OSError('boom')

        with patch('src.core.http.socks.socket.socket', return_value=fake_socket):
            with self.assertRaises(SocketError):
                Socket.ping('example.com', 80)

        with patch('src.core.http.socks.socket.gethostbyname', side_effect=socket.gaierror('boom')):
            with self.assertRaises(SocketError):
                Socket.get_ip_address('example.com')

        with patch('src.core.http.socks.socket.gethostbyname_ex', side_effect=socket.gaierror('boom')):
            self.assertEqual(Socket.get_ips_addresses('example.com'), '')


if __name__ == '__main__':
    unittest.main()