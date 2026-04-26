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
            'is_waf_detect': False,
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

    def test_detect_marks_anubis_cookie_challenge_as_blocked(self):
        """ResponseProvider.detect() should not classify Anubis challenge pages as success."""

        provider = ResponseProvider(SimpleNamespace(is_waf_detect=True))
        response = self.make_response(
            status=200,
            body=b'<html>challenge</html>',
            headers={
                'Set-Cookie': (
                    'techaro.lol-anubis-auth=; Max-Age=0; '
                    'techaro.lol-anubis-cookie-verification=token'
                )
            }
        )

        self.assertEqual(provider.detect('https://example.com/predictions', response), 'blocked')

    def test_detect_marks_waf_body_challenge_as_blocked_before_plugins(self):
        """ResponseProvider.detect() should run WAF detection before response sniffers."""

        plugin = MagicMock()
        plugin.process.return_value = 'success'

        provider = ResponseProvider(SimpleNamespace(is_waf_detect=True))
        provider._response_plugins.append(plugin)

        response = self.make_response(
            status=200,
            body=b'<html>Making sure you\'re not a bot</html>',
            headers={}
        )

        self.assertEqual(provider.detect('https://example.com/login.php', response), 'blocked')
        plugin.process.assert_not_called()

    def test_handle_keeps_waf_challenge_out_of_success(self):
        """Response.handle() should return blocked for WAF challenge responses."""

        cfg = self.make_config(scan='directories', is_waf_detect=True)
        debug = self.make_debug(level=0)
        response_handler = Response(cfg, debug, tpl=MagicMock())
        response = self.make_response(
            status=200,
            body=b'<html>Anubis proof-of-work</html>',
            headers={'Content-Length': '32'}
        )

        status, url, size, code = response_handler.handle(
            response,
            'https://example.com/predictions',
            1,
            1,
            []
        )

        self.assertEqual((status, url, size, code), ('blocked', 'https://example.com/predictions', '32B', '200'))

    def test_detect_identifies_cloudflare_challenge_and_exposes_vendor_metadata(self):
        """ResponseProvider.detect() should identify Cloudflare instead of generic blocked."""

        provider = ResponseProvider(SimpleNamespace(is_waf_detect=True))
        response = self.make_response(
            status=200,
            body=b'<html>Checking your browser before accessing the site</html>',
            headers={
                'Server': 'cloudflare',
                'CF-Ray': '1234567890',
            }
        )

        self.assertEqual(provider.detect('https://example.com/login', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Cloudflare')
        self.assertEqual(provider.waf_detection['confidence'], 92)

    def test_detect_identifies_akamai_challenge(self):
        """ResponseProvider.detect() should identify Akamai challenge pages."""

        provider = ResponseProvider(SimpleNamespace(is_waf_detect=True))
        response = self.make_response(
            status=403,
            body=b'<html>Access Denied Reference #18. generated by Akamai</html>',
            headers={
                'Akamai-GRN': '0.0.0000.00000000',
            }
        )

        self.assertEqual(provider.detect('https://example.com/admin', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Akamai')
        self.assertEqual(provider.waf_detection['confidence'], 88)

    def test_handle_keeps_blocked_status_but_exposes_cloudflare_metadata(self):
        """Response.handle() should keep blocked status while exposing Cloudflare metadata."""

        cfg = self.make_config(scan='directories', is_waf_detect=True)
        debug = self.make_debug(level=0)
        response_handler = Response(cfg, debug, tpl=MagicMock())
        response = self.make_response(
            status=200,
            body=b'<html>Just a moment...</html>',
            headers={
                'Content-Length': '25',
                'Server': 'cloudflare',
                'CF-Ray': 'abcdef123456',
            }
        )

        status, url, size, code = response_handler.handle(
            response,
            'https://example.com/',
            1,
            1,
            []
        )

        self.assertEqual((status, url, size, code), ('blocked', 'https://example.com/', '25B', '200'))
        self.assertEqual(response_handler.waf_detection['name'], 'Cloudflare')
        self.assertEqual(response_handler.waf_detection['confidence'], 92)

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