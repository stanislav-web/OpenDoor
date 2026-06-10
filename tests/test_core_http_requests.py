# -*- coding: utf-8 -*-

import socket
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, patch

from urllib3.exceptions import DecodeError, MaxRetryError, ReadTimeoutError, ConnectTimeoutError, HostChangedError, ProxySchemeUnknown, SSLError
from urllib3.response import HTTPResponse

from src.core.http.http import HttpRequest
from src.core.http.https import HttpsRequest
from src.core.http.proxy import Proxy
from src.core.http.socks import Socket
from src.core.http.exceptions import HttpRequestError, HttpsRequestError, ProxyRequestError, SocketError


class TestHttpRequest(unittest.TestCase):
    """TestHttpRequest class."""

    def make_cfg(self, **kwargs):
        base = {
            'host': 'example.com',
            'port': 80,
            'threads': 1,
            'timeout': 1,
            'keep_alive': False,
            'DEFAULT_SCAN': 'directories',
            'scan': 'directories',
            'retries': False,
            'accept_cookies': False,
            'method': 'HEAD',
            'scheme': 'http://',
            'is_random_user_agent': False,
            'user_agent': 'UA',
            'is_tls_legacy': False,
        }
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

    def test_request_passes_configured_retries_to_directory_pool(self):
        """HttpRequest.request() should pass cfg.retries to urllib3 for directory requests."""

        cfg = self.make_cfg(retries=7)
        req = HttpRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])
        pool = MagicMock()
        pool.request.return_value = HTTPResponse(status=200, body=b'ok', headers={})
        req._HttpRequest__pool = pool

        req.request('http://example.com/path')

        self.assertEqual(pool.request.call_args.kwargs['retries'], 7)

    def test_request_passes_configured_retries_to_poolmanager(self):
        """HttpRequest.request() should pass cfg.retries to urllib3 for non-directory requests."""

        cfg = self.make_cfg(scan='subdomains', retries=4)

        with patch('src.core.http.http.PoolManager') as pm_cls:
            pm = pm_cls.return_value
            pm.request.return_value = HTTPResponse(status=200, body=b'ok', headers={})

            req = HttpRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])
            req.request('http://api.example.com')

        self.assertEqual(pm.request.call_args.kwargs['retries'], 4)

    def test_request_refreshes_random_user_agent_for_each_http_request(self):
        """HttpRequest.request() should refresh managed random User-Agent before every request."""

        cfg = self.make_cfg(is_random_user_agent=True)
        req = HttpRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA-0'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            return HTTPResponse(status=200, body=b'ok', headers={})

        pool = MagicMock()
        pool.request.side_effect = fake_request
        req._HttpRequest__pool = pool

        with patch.object(HttpRequest, '_user_agent', new_callable=PropertyMock, create=True) as user_agent_mock:
            user_agent_mock.side_effect = ['UA-1', 'UA-2']

            req.request('http://example.com/a')
            req.request('http://example.com/b')

        self.assertEqual(captured_headers[0]['User-Agent'], 'UA-1')
        self.assertEqual(captured_headers[1]['User-Agent'], 'UA-2')
        self.assertEqual(pool.request.call_count, 2)

    def test_request_keeps_custom_user_agent_header_even_when_random_agent_enabled(self):
        """HttpRequest.request() should not overwrite a user-provided User-Agent header."""

        cfg = self.make_cfg(
            is_random_user_agent=True,
            headers=['User-Agent: Custom-UA'],
            header=None,
            cookies=None,
            cookie=None,
            request_body=None,
        )
        req = HttpRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA-0'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            return HTTPResponse(status=200, body=b'ok', headers={})

        pool = MagicMock()
        pool.request.side_effect = fake_request
        req._HttpRequest__pool = pool

        with patch.object(HttpRequest, '_user_agent', new_callable=PropertyMock, create=True) as user_agent_mock:
            user_agent_mock.side_effect = ['UA-1', 'UA-2']

            req.request('http://example.com/a')
            req.request('http://example.com/b')

        self.assertEqual(captured_headers[0]['User-Agent'], 'Custom-UA')
        self.assertEqual(captured_headers[1]['User-Agent'], 'Custom-UA')
        self.assertEqual(pool.request.call_count, 2)

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
        tpl.warning.assert_not_called()

        for exc in [HostChangedError(None, '/', 0), ReadTimeoutError(None, '/', 'x'), DecodeError('bad gzip'), ConnectTimeoutError(None, '/', 'x')]:
            pool.request.reset_mock(side_effect=True)
            tpl.warning.reset_mock()
            pool.request.side_effect = exc
            self.assertIsNone(req.request('http://example.com/x'))
            self.assertTrue(tpl.warning.called)

    def test_close_releases_http_pool_resources(self):
        """HttpRequest.close() should release owned pool resources."""

        req = HttpRequest(self.make_cfg(), SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])
        pool = MagicMock()
        manager = MagicMock()
        req._HttpRequest__pool = pool
        req._HttpRequest__manager = manager

        req.close()

        pool.close.assert_called_once_with()
        manager.close.assert_called_once_with()

    def test_init_wraps_errors(self):
        """HttpRequest.__init__() should wrap provider setup failures."""

        cfg = self.make_cfg()
        with patch('src.core.http.http.RequestProvider.__init__', side_effect=TypeError('bad')):
            with self.assertRaises(HttpRequestError):
                HttpRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])


class TestHttpsRequest(unittest.TestCase):
    """TestHttpsRequest class."""

    def make_cfg(self, **kwargs):
        base = {
            'host': 'example.com',
            'port': 443,
            'threads': 1,
            'timeout': 1,
            'keep_alive': False,
            'DEFAULT_SCAN': 'directories',
            'scan': 'directories',
            'retries': False,
            'accept_cookies': False,
            'method': 'HEAD',
            'scheme': 'https://',
            'is_random_user_agent': False,
            'user_agent': 'UA',
            'is_tls_legacy': False,
        }
        base.update(kwargs)
        return SimpleNamespace(**base)

    def test_provide_ssl_auth_required(self):
        """HttpsRequest should provide a synthetic SSL-auth-required response."""

        req = HttpsRequest(self.make_cfg(), SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])
        response = req._provide_ssl_auth_required()

        self.assertEqual(response.status, 496)

    def test_request_passes_configured_retries_to_directory_pool(self):
        """HttpsRequest.request() should pass cfg.retries to urllib3 for directory requests."""

        cfg = self.make_cfg(retries=8)
        req = HttpsRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])
        pool = MagicMock()
        pool.request.return_value = HTTPResponse(status=200, body=b'ok', headers={})
        req._HttpsRequest__pool = pool

        req.request('https://example.com/path')

        self.assertEqual(pool.request.call_args.kwargs['retries'], 8)

    def test_request_passes_configured_retries_to_poolmanager(self):
        """HttpsRequest.request() should pass cfg.retries to urllib3 for non-directory requests."""

        cfg = self.make_cfg(scan='subdomains', retries=5)

        with patch('src.core.http.https.PoolManager') as pm_cls:
            pm = pm_cls.return_value
            pm.request.return_value = HTTPResponse(status=200, body=b'ok', headers={})

            req = HttpsRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])
            req.request('https://api.example.com')

        self.assertEqual(pm.request.call_args.kwargs['retries'], 5)

    def test_request_refreshes_random_user_agent_for_each_https_request(self):
        """HttpsRequest.request() should refresh managed random User-Agent before every request."""

        cfg = self.make_cfg(is_random_user_agent=True)
        req = HttpsRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA-0'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            return HTTPResponse(status=200, body=b'ok', headers={})

        pool = MagicMock()
        pool.request.side_effect = fake_request
        req._HttpsRequest__pool = pool

        with patch.object(HttpsRequest, '_user_agent', new_callable=PropertyMock, create=True) as user_agent_mock:
            user_agent_mock.side_effect = ['UA-1', 'UA-2']

            req.request('https://example.com/a')
            req.request('https://example.com/b')

        self.assertEqual(captured_headers[0]['User-Agent'], 'UA-1')
        self.assertEqual(captured_headers[1]['User-Agent'], 'UA-2')
        self.assertEqual(pool.request.call_count, 2)

    def test_request_keeps_custom_user_agent_header_even_when_https_random_agent_enabled(self):
        """HttpsRequest.request() should not overwrite a user-provided User-Agent header."""

        cfg = self.make_cfg(
            is_random_user_agent=True,
            headers=['User-Agent: Custom-UA'],
            header=None,
            cookies=None,
            cookie=None,
            request_body=None,
        )
        req = HttpsRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA-0'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            return HTTPResponse(status=200, body=b'ok', headers={})

        pool = MagicMock()
        pool.request.side_effect = fake_request
        req._HttpsRequest__pool = pool

        with patch.object(HttpsRequest, '_user_agent', new_callable=PropertyMock, create=True) as user_agent_mock:
            user_agent_mock.side_effect = ['UA-1', 'UA-2']

            req.request('https://example.com/a')
            req.request('https://example.com/b')

        self.assertEqual(captured_headers[0]['User-Agent'], 'Custom-UA')
        self.assertEqual(captured_headers[1]['User-Agent'], 'Custom-UA')
        self.assertEqual(pool.request.call_count, 2)


    def test_tls_legacy_builds_ssl_context_and_logs_policy(self):
        """HttpsRequest should pass an opt-in legacy SSL context to urllib3."""

        cfg = self.make_cfg(is_tls_legacy=True)
        tpl = MagicMock()

        with patch('src.core.http.https.HTTPSConnectionPool') as pool_cls:
            HttpsRequest(cfg, SimpleNamespace(level=0), tpl=tpl, agent_list=['UA'])

        kwargs = pool_cls.call_args.kwargs
        self.assertIsNotNone(kwargs.get('ssl_context'))
        tpl.debug.assert_called_once()
        self.assertIn('DEFAULT:!DHE', tpl.debug.call_args.kwargs.get('msg', ''))

    def test_tls_dh_key_error_is_reported_with_tls_legacy_hint(self):
        """HttpsRequest should expose weak-DH TLS failures as actionable diagnostics."""

        cfg = self.make_cfg()
        tpl = MagicMock()
        req = HttpsRequest(cfg, SimpleNamespace(level=0), tpl=tpl, agent_list=['UA'])
        pool = MagicMock()
        pool.request.side_effect = MaxRetryError(None, '/', SSLError('dh key too small'))
        req._HttpsRequest__pool = pool

        self.assertIsNone(req.request('https://example.com/x'))
        self.assertIn('DH_KEY_TOO_SMALL', cfg.last_transport_error)
        self.assertIn('--tls-legacy', cfg.last_transport_error)
        self.assertTrue(any(
            'DH_KEY_TOO_SMALL' in call.kwargs.get('msg', '')
            for call in tpl.warning.call_args_list
        ))

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
        with patch('src.core.http.https.PoolManager') as pm_cls:
            pm = pm_cls.return_value
            pm.request.side_effect = SSLError(None)
            req_sub = HttpsRequest(cfg_sub, SimpleNamespace(level=0), tpl=tpl, agent_list=['UA'])
            response = req_sub.request('https://api.example.com')
        self.assertEqual(response.status, 496)

        pool.request.reset_mock(side_effect=True)
        tpl.warning.reset_mock()
        pool.request.side_effect = MaxRetryError(None, '/', None)
        self.assertIsNone(req.request('https://example.com/x'))
        tpl.warning.assert_not_called()

        for exc in [HostChangedError(None, '/', 0), ReadTimeoutError(None, '/', 'x'), DecodeError('bad gzip'), ConnectTimeoutError(None, '/', 'x')]:
            pool.request.reset_mock(side_effect=True)
            tpl.warning.reset_mock()
            pool.request.side_effect = exc
            self.assertIsNone(req.request('https://example.com/x'))
            self.assertTrue(tpl.warning.called)

    def test_close_releases_https_pool_resources(self):
        """HttpsRequest.close() should release owned pool resources."""

        req = HttpsRequest(self.make_cfg(), SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])
        pool = MagicMock()
        manager = MagicMock()
        req._HttpsRequest__pool = pool
        req._HttpsRequest__manager = manager

        req.close()

        pool.close.assert_called_once_with()
        manager.close.assert_called_once_with()

    def test_init_wraps_errors(self):
        """HttpsRequest.__init__() should wrap provider setup failures."""

        cfg = self.make_cfg()
        with patch('src.core.http.https.RequestProvider.__init__', side_effect=TypeError('bad')):
            with self.assertRaises(HttpsRequestError):
                HttpsRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])


class TestProxy(unittest.TestCase):
    """TestProxy class."""

    def make_cfg(self, **kwargs):
        base = {
            'host': 'example.com',
            'port': 80,
            'threads': 1,
            'timeout': 1,
            'keep_alive': False,
            'DEFAULT_SCAN': 'directories',
            'scan': 'directories',
            'retries': False,
            'accept_cookies': False,
            'method': 'HEAD',
            'scheme': 'http://',
            'is_random_user_agent': False,
            'user_agent': 'UA',
            'is_standalone_proxy': False,
            'proxy': '',
            'is_proxy_pool': False,
            'is_tls_legacy': False,
        }
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


    def test_proxy_tls_legacy_passes_ssl_context_to_proxy_manager(self):
        """Proxy should pass legacy TLS context to urllib3 when --tls-legacy is enabled."""

        debug = SimpleNamespace(level=0, debug_proxy_pool=lambda: None)
        tpl = MagicMock()
        proxy = Proxy(
            self.make_cfg(is_tls_legacy=True),
            debug,
            tpl=tpl,
            proxy_list=['http://127.0.0.1:8080'],
            agent_list=['UA'],
        )

        with patch('src.core.http.proxy.ProxyManager') as pm_cls:
            pm_cls.return_value.request.return_value = HTTPResponse(status=200, body=b'ok', headers={})
            proxy.request('https://example.com/x')

        self.assertIsNotNone(pm_cls.call_args.kwargs.get('ssl_context'))
        tpl.debug.assert_called_once()


    def test_proxy_tls_error_records_legacy_hint(self):
        """Proxy should expose weak-DH TLS failures as actionable diagnostics."""

        debug = SimpleNamespace(level=0, debug_proxy_pool=lambda: None)
        cfg = self.make_cfg()
        tpl = MagicMock()
        proxy = Proxy(cfg, debug, tpl=tpl, proxy_list=['http://127.0.0.1:8080'], agent_list=['UA'])

        with patch('src.core.http.proxy.ProxyManager') as pm_cls:
            pm_cls.return_value.request.side_effect = MaxRetryError(None, '/', SSLError('dh key too small'))
            proxy.request('https://example.com/x')

        self.assertIn('DH_KEY_TOO_SMALL', cfg.last_transport_error)
        self.assertTrue(any(
            'DH_KEY_TOO_SMALL' in call.kwargs.get('msg', '')
            for call in tpl.warning.call_args_list
        ))

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


    def test_close_releases_cached_proxy_pools(self):
        """Proxy.close() should clear all cached proxy pool resources."""

        proxy = Proxy(
            self.make_cfg(),
            SimpleNamespace(level=0, debug_proxy_pool=lambda: None),
            tpl=MagicMock(),
            proxy_list=['http://127.0.0.1:8080'],
            agent_list=['UA'],
        )
        pool_a = MagicMock()
        pool_b = MagicMock()
        proxy._Proxy__proxy_pools = {
            'http://127.0.0.1:8080': pool_a,
            'http://127.0.0.1:8081': pool_b,
        }

        proxy.close()

        pool_a.close.assert_called_once_with()
        pool_b.close.assert_called_once_with()
        self.assertEqual(proxy._Proxy__proxy_pools, {})

    def test_proxy_request_handles_decode_error_without_crashing(self):
        """Proxy.request() should skip corrupted encoded responses without raising worker-fatal errors."""

        cfg = self.make_cfg(scan='directories')
        tpl = MagicMock()
        proxy = Proxy(cfg, SimpleNamespace(level=0, debug_proxy_pool=lambda: None), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__pool_request', side_effect=DecodeError('bad gzip')):
            actual = proxy.request('http://example.com/path')

        self.assertIsNone(actual)
        tpl.warning.assert_called_once_with(key='decode_error', url='/path')

    def test_proxy_retry_handles_decode_error_without_marking_proxy_unavailable(self):
        """Proxy retry path should not escalate DecodeError as a proxy outage."""

        cfg = self.make_cfg(scan='directories', is_standalone_proxy=True)
        tpl = MagicMock()
        proxy = Proxy(cfg, SimpleNamespace(level=0, debug_proxy_pool=lambda: None), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])
        proxy._Proxy__server = 'http://127.0.0.1:8080'

        with patch.object(
            proxy,
            '_Proxy__pool_request',
            side_effect=[MaxRetryError(None, '/', None), DecodeError('bad gzip')],
        ):
            actual = proxy.request('http://example.com/path')

        self.assertIsNone(actual)
        tpl.error.assert_not_called()
        self.assertEqual(tpl.warning.call_args_list[-1].kwargs['key'], 'decode_error')


class TestSocket(unittest.TestCase):
    """TestSocket class."""

    def test_ping_and_ip_helpers(self):
        """Socket helpers should ping and resolve IP addresses."""

        fake_socket = MagicMock()
        with patch('src.core.http.socks.socket.create_connection', return_value=fake_socket) as connect_mock:
            Socket.ping('example.com', 80, timeout=1)

        connect_mock.assert_called_once_with(('example.com', 80), timeout=1)
        fake_socket.close.assert_called_once()

        with patch('src.core.http.socks.socket.gethostbyname', return_value='127.0.0.1'):
            self.assertEqual(Socket.get_ip_address('example.com'), '127.0.0.1')

        with patch('src.core.http.socks.socket.gethostbyname_ex', return_value=('example.com', [], ['1.1.1.1', '2.2.2.2'])):
            self.assertEqual(Socket.get_ips_addresses('example.com'), '[1.1.1.1, 2.2.2.2]')

    def test_socket_wraps_errors(self):
        """Socket helpers should wrap low-level socket errors."""

        with patch('src.core.http.socks.socket.create_connection', side_effect=OSError('boom')), \
                patch('src.core.http.socks.socket.getaddrinfo', return_value=[
                    (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80)),
                ]):
            with self.assertRaises(SocketError) as context:
                Socket.ping('example.com', 80)

        self.assertIn('Unable to connect to example.com:80 within 10s', str(context.exception))
        self.assertIn('127.0.0.1', str(context.exception))

        with patch('src.core.http.socks.socket.gethostbyname', side_effect=socket.gaierror('boom')):
            with self.assertRaises(SocketError):
                Socket.get_ip_address('example.com')

        with patch('src.core.http.socks.socket.gethostbyname_ex', side_effect=socket.gaierror('boom')):
            self.assertEqual(Socket.get_ips_addresses('example.com'), '')

    def test_get_proxy_type_and_random_proxy(self):
        """Proxy helpers should detect proxy type and return a trimmed random proxy."""

        self.assertEqual(Proxy._Proxy__get_proxy_type('socks5://x'), 'socks')
        self.assertEqual(Proxy._Proxy__get_proxy_type('socks://x'), 'socks')
        self.assertEqual(Proxy._Proxy__get_proxy_type('https://x'), 'https')
        self.assertEqual(Proxy._Proxy__get_proxy_type('http://x'), 'http')
        self.assertEqual(
            Proxy._Proxy__normalize_proxy_server(' socks://127.0.0.1:9050 '),
            'socks5://127.0.0.1:9050',
        )

if __name__ == '__main__':
    unittest.main()
