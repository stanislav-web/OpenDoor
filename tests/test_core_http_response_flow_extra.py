# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib3.response import HTTPResponse

from src.core.http.providers.cookies import CookiesProvider
from src.core.http.providers.response import ResponseProvider
from src.core.http.response import Response


class TestResponseProviderExtra(unittest.TestCase):
    """TestResponseProviderExtra class."""

    @staticmethod
    def make_response(status=200, body=b'', headers=None):
        """Create a simple HTTPResponse for response-flow tests."""

        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_get_redirect_url_returns_none_when_location_is_false(self):
        """ResponseProvider._get_redirect_url() should return None when there is no redirect location."""

        response = self.make_response(status=200, body=b'', headers={})
        self.assertIsNone(ResponseProvider._get_redirect_url('http://example.com', response))

    def test_redirect_detection_fails_for_same_root_url(self):
        """ResponseProvider.detect() should treat redirects to the same root as failed."""

        provider = ResponseProvider(SimpleNamespace())
        response = self.make_response(status=301, body=b'', headers={'Location': 'http://example.com/'})

        self.assertEqual(provider.detect('http://example.com/path', response), 'failed')

    def test_redirect_detection_fails_when_redirect_query_is_already_in_path(self):
        """ResponseProvider.detect() should treat self-referential query redirects as failed."""

        provider = ResponseProvider(SimpleNamespace())
        response = self.make_response(status=301, body=b'', headers={'Location': 'http://example.com/next?bar'})

        self.assertEqual(provider.detect('http://example.com/path/bar', response), 'failed')

    def test_get_content_size_uses_body_when_content_length_header_is_missing(self):
        """ResponseProvider._get_content_size() should fall back to response body length."""

        response = SimpleNamespace(data=b'abc', headers={})
        self.assertEqual(ResponseProvider._get_content_size(response), '3B')


class TestResponseFlowExtra(unittest.TestCase):
    """TestResponseFlowExtra class."""

    @staticmethod
    def make_config(**overrides):
        """Create a minimal config namespace for Response tests."""

        base = {
            'is_sniff': False,
            'sniffers': [],
            'SUBDOMAINS_SCAN': 'subdomains',
            'scan': 'directories',
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @staticmethod
    def make_debug(level=0):
        """Create a simple debug stub."""

        return SimpleNamespace(
            level=level,
            debug_load_sniffer_plugin=MagicMock(),
            debug_response=MagicMock(),
            debug_request_uri=MagicMock(),
        )

    @staticmethod
    def make_response(status=200, body=b'', headers=None):
        """Create a simple HTTPResponse for Response.handle tests."""

        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_handle_uses_dict_debug_branch_when_headers_items_are_not_jsonable(self):
        """Response.handle() should debug-log dict(headers) when headers.items() is not jsonable."""

        debug = self.make_debug(level=99)
        response_handler = Response(self.make_config(scan='directories'), debug, tpl=MagicMock())
        response = self.make_response(status=200, body=b'ok', headers={'Content-Length': '2'})

        with patch('src.core.http.response.helper.is_jsonable', return_value=False):
            status, url, size, code = response_handler.handle(response, 'http://example.com/path', 1, 2, [])

        self.assertEqual((status, url, size, code), ('success', 'http://example.com/path', '2B', '200'))
        debug.debug_response.assert_called_once()

    def test_handle_redirect_in_subdomain_scan_appends_ips_and_applies_ignore_list(self):
        """Response.handle() should downgrade ignored redirects and append IPs for subdomain scan."""

        cfg = self.make_config(scan='subdomains')
        debug = self.make_debug(level=0)
        response_handler = Response(cfg, debug, tpl=MagicMock())
        response = self.make_response(status=301, body=b'', headers={'Location': '/admin', 'Content-Length': '0'})

        with patch('src.core.http.response.Socket.get_ips_addresses', return_value='[1.1.1.1]'):
            status, url, size, code = response_handler.handle(response, 'http://sub.example.com/path', 1, 2, ['admin'])

        self.assertEqual((status, url, size, code), ('failed', 'http://sub.example.com/path [1.1.1.1]', '0B', '301'))

    def test_handle_non_redirect_in_subdomain_scan_appends_ips(self):
        """Response.handle() should append IPs for non-redirect subdomain responses."""

        cfg = self.make_config(scan='subdomains')
        debug = self.make_debug(level=0)
        response_handler = Response(cfg, debug, tpl=MagicMock())
        response = self.make_response(status=200, body=b'ok', headers={'Content-Length': '2'})

        with patch('src.core.http.response.Socket.get_ips_addresses', return_value='[2.2.2.2]'):
            status, url, size, code = response_handler.handle(response, 'http://sub.example.com/path', 1, 2, [])

        self.assertEqual((status, url, size, code), ('success', 'http://sub.example.com/path [2.2.2.2]', '2B', '200'))

    def test_handle_returns_none_for_statusless_non_subdomain_response(self):
        """Response.handle() should return None for statusless non-subdomain inputs."""

        cfg = self.make_config(scan='directories')
        debug = self.make_debug(level=0)
        response_handler = Response(cfg, debug, tpl=MagicMock())
        response = SimpleNamespace(data=b'', headers={})

        self.assertIsNone(response_handler.handle(response, 'http://example.com/path', 1, 2, []))


class TestCookiesProviderExtra(unittest.TestCase):
    """TestCookiesProviderExtra class."""

    def test_fetch_cookies_without_header_keeps_none(self):
        """CookiesProvider._fetch_cookies() should ignore headers without set-cookie."""

        provider = CookiesProvider()
        provider._fetch_cookies({'x-test': '1'})

        self.assertFalse(provider._is_cookie_fetched)
        self.assertIsNone(provider._cookies)

    def test_push_cookies_strips_whitespace(self):
        """CookiesProvider._push_cookies() should strip surrounding whitespace."""

        provider = CookiesProvider()
        provider._cookies = ' token=value '
        self.assertEqual(provider._push_cookies(), 'token=value')


if __name__ == '__main__':
    unittest.main()