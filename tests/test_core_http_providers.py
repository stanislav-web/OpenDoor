# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.core.http.providers.accept import AcceptHeaderProvider
from src.core.http.providers.cache import CacheControlProvider
from src.core.http.providers.connection import ConnectionHeaderProvider
from src.core.http.providers.cookies import CookiesProvider
from src.core.http.providers.header import HeaderProvider
from src.core.http.providers.user_agent import UserAgentHeaderProvider
from src.core.http.providers.request import RequestProvider
from src.core.http.providers.debug import DebugProvider
from src.core.http.exceptions import SocketError, ProxyRequestError, HttpRequestError, HttpsRequestError, ResponseError


class TestHttpProviders(unittest.TestCase):
    """TestHttpProviders class."""

    def test_accept_cache_and_connection_headers(self):
        """Header providers should expose stable defaults."""

        accept = AcceptHeaderProvider()
        with patch('src.core.http.providers.accept.random.randrange', return_value=0):
            self.assertEqual(accept._accept, '*/*')
            self.assertEqual(accept._accept_encoding, 'identity')
            self.assertIn('en-US', accept._accept_language)

        self.assertEqual(CacheControlProvider()._cache_control, 'max-age=0')
        self.assertEqual(ConnectionHeaderProvider(SimpleNamespace())._keep_alive, 'keep-alive')

    def test_cookies_provider_flow(self):
        """CookiesProvider should fetch and push cookies."""

        provider = CookiesProvider()
        self.assertFalse(provider._is_cookie_fetched)

        provider._fetch_cookies({'set-cookie': ' token=value '})
        self.assertTrue(provider._is_cookie_fetched)
        self.assertEqual(provider._push_cookies(), 'token=value')

    def test_header_provider_builds_default_headers(self):
        """HeaderProvider should build a default browser-like header set."""

        cfg = SimpleNamespace(scheme='http://', host='example.com', port=80)
        provider = HeaderProvider(cfg)

        provider.add_header('X-Test', ' value ')
        headers = provider._headers

        self.assertEqual(headers['X-Test'], 'value')
        self.assertEqual(headers['Origin'], 'http://example.com')
        self.assertEqual(headers['Referer'], 'http://example.com:80')
        self.assertEqual(headers['Cache-Control'], 'max-age=0')

    def test_user_agent_provider_uses_random_or_default(self):
        """UserAgentHeaderProvider should return either the configured UA or a random one."""

        cfg = SimpleNamespace(is_random_user_agent=False, user_agent='UA')
        provider = UserAgentHeaderProvider(cfg, ['A', 'B'])
        self.assertEqual(provider._user_agent, 'UA')

        random_cfg = SimpleNamespace(is_random_user_agent=True, user_agent='UA')
        provider = UserAgentHeaderProvider(random_cfg, ['A\n', 'B\n'])
        with patch('src.core.http.providers.user_agent.random.randrange', return_value=1):
            self.assertEqual(provider._user_agent, 'B')

    def test_request_provider_cookies_middleware(self):
        """RequestProvider.cookies_middleware() should propagate cookies only when enabled."""

        cfg = SimpleNamespace(scheme='http://', host='example.com', port=80, is_random_user_agent=False, user_agent='UA')
        provider = RequestProvider(cfg, ['UA'])
        response = SimpleNamespace(headers={'set-cookie': ' token=value '})

        provider.cookies_middleware(True, response)
        self.assertEqual(provider._headers['Cookie'], 'token=value')

        provider = RequestProvider(cfg, ['UA'])
        provider.cookies_middleware(False, response)
        self.assertNotIn('Cookie', provider._headers)

    def test_debug_provider_base_contract(self):
        """DebugProvider base methods should remain no-op."""

        provider = DebugProvider()
        self.assertIsNone(provider.level)
        self.assertIsNone(provider.debug_user_agents())
        self.assertIsNone(provider.debug_connection_pool('k', object(), 'http'))
        self.assertIsNone(provider.debug_proxy_pool())
        self.assertIsNone(provider.debug_list(1))
        self.assertIsNone(provider.debug_request({}, 'http://example.com', 'HEAD'))
        self.assertIsNone(provider.debug_response({}))
        self.assertIsNone(provider.debug_request_uri('success', 'http://example.com'))
        self.assertIsNone(provider.debug_load_sniffer_plugin('desc'))

    def test_http_exceptions_preserve_message(self):
        """HTTP exception classes should preserve the provided message."""

        for exc in [SocketError('a'), ProxyRequestError('b'), HttpRequestError('c'), HttpsRequestError('d'), ResponseError('e')]:
            self.assertTrue(str(exc))


if __name__ == '__main__':
    unittest.main()