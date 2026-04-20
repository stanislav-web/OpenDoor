# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib3.exceptions import ConnectTimeoutError, HostChangedError, MaxRetryError, ReadTimeoutError, SSLError
from urllib3.response import HTTPResponse

from src.core.http.exceptions import HttpRequestError, HttpsRequestError
from src.core.http.http import HttpRequest
from src.core.http.https import HttpsRequest


class TestHttpRequestLowCoverage(unittest.TestCase):
    """TestHttpRequestLowCoverage class."""

    @staticmethod
    def make_cfg(**overrides):
        """Create a minimal config namespace for HTTP request tests."""

        base = {
            'host': 'example.com',
            'port': 80,
            'threads': 2,
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
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @staticmethod
    def make_debug(level=0):
        """Create a simple debug stub."""

        return SimpleNamespace(
            level=level,
            debug_connection_pool=MagicMock(),
            debug_request=MagicMock(),
        )

    def test_http_pool_wraps_construction_errors(self):
        """HttpRequest should wrap HTTPConnectionPool construction errors."""

        cfg = self.make_cfg()

        with patch('src.core.http.http.HTTPConnectionPool', side_effect=RuntimeError('boom')):
            with self.assertRaises(HttpRequestError):
                HttpRequest(cfg, self.make_debug(), tpl=MagicMock(), agent_list=['UA'])

    def test_http_pool_triggers_debug_connection_pool(self):
        """HttpRequest should debug-log connection pool creation when debug level is high."""

        cfg = self.make_cfg(keep_alive=True)
        debug = self.make_debug(level=99)
        pool = MagicMock()

        with patch('src.core.http.http.HTTPConnectionPool', return_value=pool):
            HttpRequest(cfg, debug, tpl=MagicMock(), agent_list=['UA'])

        debug.debug_connection_pool.assert_called_once_with('http_pool_start', pool, 'keep-alive')

    def test_http_request_directory_sets_headers_and_runs_cookie_middleware(self):
        """HttpRequest.request() should send keep-alive headers and call cookie middleware."""

        cfg = self.make_cfg(keep_alive=True, accept_cookies=True)
        debug = self.make_debug(level=99)
        requester = HttpRequest(cfg, debug, tpl=MagicMock(), agent_list=['UA'])

        response = HTTPResponse(status=200, body=b'ok', headers={})
        pool = MagicMock()
        pool.request.return_value = response
        requester._HttpRequest__pool = pool

        with patch.object(requester, 'cookies_middleware') as cookies_mock:
            actual = requester.request('http://example.com/admin')

        self.assertEqual(actual.status, 200)
        debug.debug_request.assert_called_once()

        kwargs = pool.request.call_args.kwargs
        self.assertEqual(kwargs['headers']['User-Agent'], 'UA')
        self.assertEqual(kwargs['headers']['Connection'], 'keep-alive')
        self.assertEqual(pool.request.call_args.args[1], '/admin')
        cookies_mock.assert_called_once_with(is_accept=True, response=response)

    def test_http_request_subdomain_uses_poolmanager_with_timeout(self):
        """HttpRequest.request() should use PoolManager for non-default scan mode."""

        cfg = self.make_cfg(scan='subdomains')
        debug = self.make_debug(level=99)

        response = HTTPResponse(status=200, body=b'ok', headers={})

        with patch('src.core.http.http.PoolManager') as pool_manager_cls:
            pool_manager = pool_manager_cls.return_value
            pool_manager.request.return_value = response

            requester = HttpRequest(cfg, debug, tpl=MagicMock(), agent_list=['UA'])
            actual = requester.request('http://api.example.com')

        self.assertEqual(actual.status, 200)
        debug.debug_request.assert_called_once()
        pool_manager.request.assert_called_once()

    def test_http_request_warns_on_host_changed_and_timeouts(self):
        """HttpRequest.request() should warn on host changes and timeouts."""

        cfg = self.make_cfg()
        tpl = MagicMock()
        requester = HttpRequest(cfg, self.make_debug(), tpl=tpl, agent_list=['UA'])
        pool = MagicMock()
        requester._HttpRequest__pool = pool

        for exc in [
            HostChangedError(None, '/', 0),
            ReadTimeoutError(None, '/', 'x'),
            ConnectTimeoutError(None, '/', 'x'),
        ]:
            pool.request.reset_mock(side_effect=True)
            tpl.warning.reset_mock()

            pool.request.side_effect = exc
            self.assertIsNone(requester.request('http://example.com/test'))
            self.assertTrue(tpl.warning.called)

    def test_http_request_warns_on_max_retry_only_for_default_scan(self):
        """HttpRequest.request() should warn on MaxRetryError only for default scan mode."""

        cfg = self.make_cfg()
        tpl = MagicMock()
        requester = HttpRequest(cfg, self.make_debug(), tpl=tpl, agent_list=['UA'])
        pool = MagicMock()
        requester._HttpRequest__pool = pool
        pool.request.side_effect = MaxRetryError(None, '/', None)

        self.assertIsNone(requester.request('http://example.com/test'))
        tpl.warning.assert_called_once()


class TestHttpsRequestLowCoverage(unittest.TestCase):
    """TestHttpsRequestLowCoverage class."""

    @staticmethod
    def make_cfg(**overrides):
        """Create a minimal config namespace for HTTPS request tests."""

        base = {
            'host': 'example.com',
            'port': 443,
            'threads': 2,
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
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @staticmethod
    def make_debug(level=0):
        """Create a simple debug stub."""

        return SimpleNamespace(
            level=level,
            debug_connection_pool=MagicMock(),
            debug_request=MagicMock(),
        )

    def test_https_pool_wraps_construction_errors(self):
        """HttpsRequest should wrap HTTPSConnectionPool construction errors."""

        cfg = self.make_cfg()

        with patch('src.core.http.https.HTTPSConnectionPool', side_effect=RuntimeError('boom')):
            with self.assertRaises(HttpsRequestError):
                HttpsRequest(cfg, self.make_debug(), tpl=MagicMock(), agent_list=['UA'])

    def test_https_pool_triggers_debug_connection_pool(self):
        """HttpsRequest should debug-log connection pool creation when debug level is high."""

        cfg = self.make_cfg(keep_alive=True)
        debug = self.make_debug(level=99)
        pool = MagicMock()

        with patch('src.core.http.https.HTTPSConnectionPool', return_value=pool):
            HttpsRequest(cfg, debug, tpl=MagicMock(), agent_list=['UA'])

        debug.debug_connection_pool.assert_called_once_with('https_pool_start', pool, 'keep-alive')

    def test_https_request_directory_sets_headers_and_runs_cookie_middleware(self):
        """HttpsRequest.request() should send keep-alive headers and call cookie middleware."""

        cfg = self.make_cfg(keep_alive=True, accept_cookies=True)
        debug = self.make_debug(level=99)
        requester = HttpsRequest(cfg, debug, tpl=MagicMock(), agent_list=['UA'])

        response = HTTPResponse(status=200, body=b'ok', headers={})
        pool = MagicMock()
        pool.request.return_value = response
        requester._HttpsRequest__pool = pool

        with patch('src.core.http.https.disable_warnings') as disable_mock, \
                patch.object(requester, 'cookies_middleware') as cookies_mock:
            actual = requester.request('https://example.com/admin')

        self.assertEqual(actual.status, 200)
        debug.debug_request.assert_called_once()
        disable_mock.assert_called_once()

        kwargs = pool.request.call_args.kwargs
        self.assertEqual(kwargs['headers']['User-Agent'], 'UA')
        self.assertEqual(kwargs['headers']['Connection'], 'keep-alive')
        self.assertEqual(pool.request.call_args.args[1], '/admin')
        cookies_mock.assert_called_once_with(is_accept=True, response=response)

    def test_https_request_subdomain_uses_poolmanager(self):
        """HttpsRequest.request() should use PoolManager for non-default scan mode."""

        cfg = self.make_cfg(scan='subdomains')
        debug = self.make_debug(level=99)
        response = HTTPResponse(status=200, body=b'ok', headers={})

        with patch('src.core.http.https.disable_warnings'), \
                patch('src.core.http.https.PoolManager') as pool_manager_cls:
            pool_manager = pool_manager_cls.return_value
            pool_manager.request.return_value = response

            requester = HttpsRequest(cfg, debug, tpl=MagicMock(), agent_list=['UA'])
            actual = requester.request('https://api.example.com')

        self.assertEqual(actual.status, 200)
        debug.debug_request.assert_called_once()
        pool_manager.request.assert_called_once()

    def test_https_request_warns_on_host_changed_and_timeouts(self):
        """HttpsRequest.request() should warn on host changes and timeouts."""

        cfg = self.make_cfg()
        tpl = MagicMock()
        requester = HttpsRequest(cfg, self.make_debug(), tpl=tpl, agent_list=['UA'])
        pool = MagicMock()
        requester._HttpsRequest__pool = pool

        for exc in [
            HostChangedError(None, '/', 0),
            ReadTimeoutError(None, '/', 'x'),
            ConnectTimeoutError(None, '/', 'x'),
        ]:
            pool.request.reset_mock(side_effect=True)
            tpl.warning.reset_mock()

            pool.request.side_effect = exc
            with patch('src.core.http.https.disable_warnings'):
                self.assertIsNone(requester.request('https://example.com/test'))
            self.assertTrue(tpl.warning.called)

    def test_https_request_returns_ssl_auth_required_for_subdomains(self):
        """HttpsRequest.request() should synthesize status 496 for subdomain SSL errors."""

        cfg = self.make_cfg(scan='subdomains')
        tpl = MagicMock()

        with patch('src.core.http.https.disable_warnings'), \
                patch('src.core.http.https.PoolManager') as pool_manager_cls:
            pool_manager = pool_manager_cls.return_value
            pool_manager.request.side_effect = SSLError(None)

            requester = HttpsRequest(cfg, self.make_debug(), tpl=tpl, agent_list=['UA'])
            actual = requester.request('https://api.example.com')

        self.assertEqual(actual.status, requester.DEFAULT_SSL_CERT_REQUIRED_STATUSES)

    def test_https_request_returns_none_for_directory_ssl_errors(self):
        """HttpsRequest.request() should return None for directory SSL errors."""

        cfg = self.make_cfg()
        requester = HttpsRequest(cfg, self.make_debug(), tpl=MagicMock(), agent_list=['UA'])
        pool = MagicMock()
        pool.request.side_effect = SSLError(None)
        requester._HttpsRequest__pool = pool

        with patch('src.core.http.https.disable_warnings'):
            self.assertIsNone(requester.request('https://example.com/test'))

    def test_https_request_warns_on_max_retry_only_for_default_scan(self):
        """HttpsRequest.request() should warn on MaxRetryError only for default scan mode."""

        cfg = self.make_cfg()
        tpl = MagicMock()
        requester = HttpsRequest(cfg, self.make_debug(), tpl=tpl, agent_list=['UA'])
        pool = MagicMock()
        requester._HttpsRequest__pool = pool
        pool.request.side_effect = MaxRetryError(None, '/', None)

        with patch('src.core.http.https.disable_warnings'):
            self.assertIsNone(requester.request('https://example.com/test'))
        tpl.warning.assert_called_once()


if __name__ == '__main__':
    unittest.main()