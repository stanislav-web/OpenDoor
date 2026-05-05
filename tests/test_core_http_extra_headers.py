# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, patch

from urllib3.response import HTTPResponse

from src.core.http.http import HttpRequest
from src.core.http.https import HttpsRequest
from src.core.http.proxy import Proxy
from src.core.http.providers.request import RequestProvider


class TestHttpExtraHeaders(unittest.TestCase):
    """Temporary per-request extra headers tests."""

    @staticmethod
    def make_cfg(**kwargs):
        """
        Build lightweight HTTP config.

        :param dict kwargs: config overrides
        :return: types.SimpleNamespace
        """

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
            headers=None,
            header=None,
            cookies=None,
            cookie=None,
            request_body=None,
        )
        base.update(kwargs)
        return SimpleNamespace(**base)

    def test_request_provider_builds_temporary_headers_without_mutating_base(self):
        """RequestProvider should merge temporary headers without mutating shared headers."""

        cfg = self.make_cfg()
        provider = RequestProvider(cfg, ['UA'])
        base_headers = provider._headers

        merged = provider._build_request_headers(base_headers, {
            'X-Original-URL': '/admin',
            'X-Forwarded-For': '127.0.0.1',
        })

        self.assertEqual(merged['X-Original-URL'], '/admin')
        self.assertEqual(merged['X-Forwarded-For'], '127.0.0.1')
        self.assertNotIn('X-Original-URL', base_headers)
        self.assertNotIn('X-Forwarded-For', base_headers)

    def test_request_provider_accepts_multiple_extra_header_formats(self):
        """RequestProvider should accept dicts, tuples and header-line strings."""

        cfg = self.make_cfg()
        provider = RequestProvider(cfg, ['UA'])
        base_headers = provider._headers

        merged = provider._build_request_headers(base_headers, [
            ('X-Tuple-Header', 'tuple-value'),
            'X-Line-Header: line-value',
        ])

        self.assertEqual(merged['X-Tuple-Header'], 'tuple-value')
        self.assertEqual(merged['X-Line-Header'], 'line-value')
        self.assertNotIn('X-Tuple-Header', base_headers)
        self.assertNotIn('X-Line-Header', base_headers)

    def test_request_provider_ignores_malformed_or_unsafe_extra_headers(self):
        """RequestProvider should ignore malformed temporary headers and CRLF payloads."""

        cfg = self.make_cfg()
        provider = RequestProvider(cfg, ['UA'])
        base_headers = provider._headers

        merged = provider._build_request_headers(base_headers, [
            'BrokenHeaderWithoutColon',
            ('BrokenTupleOnlyOneValue',),
            ('X-Unsafe-Name\r\nInjected', '1'),
            ('X-Unsafe-Value', '1\r\nInjected: true'),
            ('X-Empty-Value', ' '),
            ('X-Safe', '1'),
        ])

        self.assertEqual(merged['X-Safe'], '1')
        self.assertNotIn('BrokenHeaderWithoutColon', merged)
        self.assertNotIn('BrokenTupleOnlyOneValue', merged)
        self.assertNotIn('X-Unsafe-Name\r\nInjected', merged)
        self.assertNotIn('X-Unsafe-Value', merged)
        self.assertNotIn('X-Empty-Value', merged)

    def test_http_request_applies_extra_headers_only_to_current_request(self):
        """HttpRequest should not leak temporary headers into the next request."""

        cfg = self.make_cfg()
        req = HttpRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            return HTTPResponse(status=200, body=b'ok', headers={})

        pool = MagicMock()
        pool.request.side_effect = fake_request
        req._HttpRequest__pool = pool

        req.request('http://example.com/admin', extra_headers={'X-Original-URL': '/admin'})
        req.request('http://example.com/normal')

        self.assertEqual(captured_headers[0]['X-Original-URL'], '/admin')
        self.assertNotIn('X-Original-URL', captured_headers[1])
        self.assertEqual(pool.request.call_count, 2)

    def test_http_request_extra_headers_do_not_break_random_user_agent_rotation(self):
        """HttpRequest should merge temporary headers after managed random User-Agent selection."""

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

            req.request('http://example.com/admin', extra_headers={'X-Forwarded-For': '127.0.0.1'})
            req.request('http://example.com/normal')

        self.assertEqual(captured_headers[0]['User-Agent'], 'UA-1')
        self.assertEqual(captured_headers[0]['X-Forwarded-For'], '127.0.0.1')
        self.assertEqual(captured_headers[1]['User-Agent'], 'UA-2')
        self.assertNotIn('X-Forwarded-For', captured_headers[1])

    def test_https_request_applies_extra_headers_only_to_current_request(self):
        """HttpsRequest should not leak temporary headers into the next request."""

        cfg = self.make_cfg(port=443, scheme='https://')
        req = HttpsRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            return HTTPResponse(status=200, body=b'ok', headers={})

        pool = MagicMock()
        pool.request.side_effect = fake_request
        req._HttpsRequest__pool = pool

        req.request('https://example.com/admin', extra_headers={'X-Rewrite-URL': '/admin'})
        req.request('https://example.com/normal')

        self.assertEqual(captured_headers[0]['X-Rewrite-URL'], '/admin')
        self.assertNotIn('X-Rewrite-URL', captured_headers[1])
        self.assertEqual(pool.request.call_count, 2)

    def test_proxy_request_applies_extra_headers_only_to_current_request(self):
        """Proxy request should pass temporary headers to one proxy call only."""

        cfg = self.make_cfg(
            proxy='http://127.0.0.1:8080',
            is_standalone_proxy=True,
        )
        debug = MagicMock()
        debug.level = 0
        req = Proxy(cfg, debug, tpl=MagicMock(), agent_list=['UA'], proxy_list=[])

        pool_request = MagicMock(return_value=HTTPResponse(status=200, body=b'ok', headers={}))
        req._Proxy__pool_request = pool_request

        req.request('http://example.com/admin', extra_headers={'X-Host': 'localhost'})
        req.request('http://example.com/normal')

        first_headers = dict(pool_request.call_args_list[0].kwargs['headers'])
        second_headers = dict(pool_request.call_args_list[1].kwargs['headers'])

        self.assertEqual(first_headers['X-Host'], 'localhost')
        self.assertNotIn('X-Host', second_headers)
        self.assertNotIn('X-Host', req._Proxy__headers)
        self.assertEqual(pool_request.call_count, 2)

    def test_proxy_retry_reuses_same_temporary_headers(self):
        """Proxy retry path should preserve the same temporary headers for the retry request."""

        cfg = self.make_cfg(
            proxy='http://127.0.0.1:8080',
            is_standalone_proxy=True,
        )
        debug = MagicMock()
        debug.level = 0
        req = Proxy(cfg, debug, tpl=MagicMock(), agent_list=['UA'], proxy_list=[])

        from urllib3.exceptions import MaxRetryError

        pool_request = MagicMock(side_effect=[
            MaxRetryError(None, '/', None),
            HTTPResponse(status=200, body=b'ok', headers={}),
        ])
        req._Proxy__pool_request = pool_request

        response = req.request('http://example.com/admin', extra_headers={'X-Original-URL': '/admin'})

        self.assertEqual(response.status, 200)
        self.assertEqual(dict(pool_request.call_args_list[0].kwargs['headers'])['X-Original-URL'], '/admin')
        self.assertEqual(dict(pool_request.call_args_list[1].kwargs['headers'])['X-Original-URL'], '/admin')
        self.assertEqual(pool_request.call_count, 2)


    def test_http_request_routes_accepted_cookies_to_next_request(self):
        """HttpRequest should route accepted Set-Cookie values to the next request."""

        cfg = self.make_cfg(accept_cookies=True)
        req = HttpRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            if len(captured_headers) == 1:
                return HTTPResponse(
                    status=200,
                    body=b'ok',
                    headers={'Set-Cookie': '__js_p_=101,1800,0,0,0; Path=/'},
                )
            return HTTPResponse(status=200, body=b'ok', headers={})

        pool = MagicMock()
        pool.request.side_effect = fake_request
        req._HttpRequest__pool = pool

        req.request('http://example.com/fail001')
        req.request('http://example.com/currency')

        self.assertNotIn('Cookie', captured_headers[0])
        self.assertEqual(captured_headers[1]['Cookie'], '__js_p_=101,1800,0,0,0')

    def test_http_request_routes_accepted_cookies_with_extra_headers(self):
        """HttpRequest should preserve routed cookies when temporary headers are used."""

        cfg = self.make_cfg(accept_cookies=True)
        req = HttpRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            if len(captured_headers) == 1:
                return HTTPResponse(
                    status=200,
                    body=b'ok',
                    headers={'Set-Cookie': 'session_id=abc123; Path=/; HttpOnly'},
                )
            return HTTPResponse(status=200, body=b'ok', headers={})

        pool = MagicMock()
        pool.request.side_effect = fake_request
        req._HttpRequest__pool = pool

        req.request('http://example.com/fail001')
        req.request(
            'http://example.com/fail001',
            extra_headers={'X-Original-URL': '/fail001'},
        )

        self.assertEqual(captured_headers[1]['Cookie'], 'session_id=abc123')
        self.assertEqual(captured_headers[1]['X-Original-URL'], '/fail001')

    def test_https_request_routes_accepted_cookies_to_next_request(self):
        """HttpsRequest should route accepted Set-Cookie values to the next request."""

        cfg = self.make_cfg(port=443, scheme='https://', accept_cookies=True)
        req = HttpsRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            if len(captured_headers) == 1:
                return HTTPResponse(
                    status=200,
                    body=b'ok',
                    headers={'Set-Cookie': '__js_p_=101,1800,0,0,0; Path=/'},
                )
            return HTTPResponse(status=200, body=b'ok', headers={})

        pool = MagicMock()
        pool.request.side_effect = fake_request
        req._HttpsRequest__pool = pool

        req.request('https://example.com/fail001')
        req.request('https://example.com/currency')

        self.assertNotIn('Cookie', captured_headers[0])
        self.assertEqual(captured_headers[1]['Cookie'], '__js_p_=101,1800,0,0,0')

    def test_https_request_routes_accepted_cookies_with_extra_headers(self):
        """HttpsRequest should preserve routed cookies when temporary headers are used."""

        cfg = self.make_cfg(port=443, scheme='https://', accept_cookies=True)
        req = HttpsRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            if len(captured_headers) == 1:
                return HTTPResponse(
                    status=200,
                    body=b'ok',
                    headers={'Set-Cookie': 'session_id=abc123; Path=/; HttpOnly'},
                )
            return HTTPResponse(status=200, body=b'ok', headers={})

        pool = MagicMock()
        pool.request.side_effect = fake_request
        req._HttpsRequest__pool = pool

        req.request('https://example.com/fail001')
        req.request(
            'https://example.com/fail001',
            extra_headers={'X-Rewrite-URL': '/fail001'},
        )

        self.assertEqual(captured_headers[1]['Cookie'], 'session_id=abc123')
        self.assertEqual(captured_headers[1]['X-Rewrite-URL'], '/fail001')

    def test_http_manager_request_routes_accepted_cookies_to_next_request(self):
        """HttpRequest should route cookies in non-default scan mode too."""

        cfg = self.make_cfg(accept_cookies=True, scan='subdomains')
        req = HttpRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            if len(captured_headers) == 1:
                return HTTPResponse(
                    status=200,
                    body=b'ok',
                    headers={'Set-Cookie': 'manager_cookie=value; Path=/'},
                )
            return HTTPResponse(status=200, body=b'ok', headers={})

        manager = MagicMock()
        manager.request.side_effect = fake_request
        req._HttpRequest__manager = manager

        req.request('http://sub.example.com/')
        req.request('http://next.example.com/')

        self.assertNotIn('Cookie', captured_headers[0])
        self.assertEqual(captured_headers[1]['Cookie'], 'manager_cookie=value')

    def test_https_manager_request_routes_accepted_cookies_to_next_request(self):
        """HttpsRequest should route cookies in non-default scan mode too."""

        cfg = self.make_cfg(port=443, scheme='https://', accept_cookies=True, scan='subdomains')
        req = HttpsRequest(cfg, SimpleNamespace(level=0), tpl=MagicMock(), agent_list=['UA'])

        captured_headers = []

        def fake_request(*args, **kwargs):
            captured_headers.append(dict(kwargs['headers']))
            if len(captured_headers) == 1:
                return HTTPResponse(
                    status=200,
                    body=b'ok',
                    headers={'Set-Cookie': 'manager_cookie=value; Path=/'},
                )
            return HTTPResponse(status=200, body=b'ok', headers={})

        manager = MagicMock()
        manager.request.side_effect = fake_request
        req._HttpsRequest__manager = manager

        req.request('https://sub.example.com/')
        req.request('https://next.example.com/')

        self.assertNotIn('Cookie', captured_headers[0])
        self.assertEqual(captured_headers[1]['Cookie'], 'manager_cookie=value')


if __name__ == '__main__':
    unittest.main()