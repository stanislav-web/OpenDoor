# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib3.response import HTTPResponse

from src.core.http.providers.response import ResponseProvider
from src.core.http.response import Response
from src.core.http.plugins.response_plugin import ResponsePlugin
from src.core.http.plugins.exceptions import ResponsePluginError
from src.core.http.plugins.response.collation import CollationResponsePlugin
from src.core.http.plugins.response.file import FileResponsePlugin
from src.core.http.plugins.response.indexof import IndexofResponsePlugin
from src.core.http.plugins.response.skipempty import SkipemptyResponsePlugin
from src.core.http.plugins.response.skipsizes import SkipSizesResponsePlugin
from src.core.http.plugins.response.provider.provider import ResponsePluginProvider
from src.core.http.exceptions import ResponseError


class TestResponsePluginProvider(unittest.TestCase):
    """TestResponsePluginProvider class."""

    def test_process_decodes_body(self):
        """ResponsePluginProvider.process() should decode byte bodies."""

        provider = ResponsePluginProvider()
        response = HTTPResponse(status=200, body='тест'.encode('cp1251'), headers={'X-Test': '1'})

        provider.process(response)

        self.assertEqual(provider._status, 200)
        self.assertEqual(provider._headers['X-Test'], '1')
        self.assertEqual(provider._body, 'тест')

    def test_process_keeps_string_body_untouched(self):
        """ResponsePluginProvider.process() should leave string bodies untouched."""

        provider = ResponsePluginProvider()
        response = SimpleNamespace(status='200.0', headers={'X-Test': '1'}, data='plain-text')

        provider.process(response)

        self.assertEqual(provider._status, 200)
        self.assertEqual(provider._headers['X-Test'], '1')
        self.assertEqual(provider._body, '')


class TestResponsePlugins(unittest.TestCase):
    """TestResponsePlugins class."""

    def make_response(self, status=200, body=b'', headers=None):
        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_file_plugin_detects_large_files(self):
        """FileResponsePlugin should classify large responses as files."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(body=b'x' * 10, headers={'Content-Length': str(1000000)})

        self.assertEqual(plugin.process(response), 'file')

    def test_file_plugin_detects_large_body_when_header_is_lower(self):
        """FileResponsePlugin should also detect files by decoded body length when header is lower."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(body=b'x' * 1000000, headers={'Content-Length': '1'})

        self.assertEqual(plugin.process(response), 'file')

    def test_file_plugin_returns_none_for_small_allowed_response(self):
        """FileResponsePlugin should ignore small responses with allowed statuses."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(body=b'small', headers={'Content-Length': '5'})

        self.assertIsNone(plugin.process(response))

    def test_file_plugin_returns_none_for_unsupported_status(self):
        """FileResponsePlugin should ignore unsupported statuses even for large responses."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(status=404, body=b'x' * 1000000, headers={'Content-Length': str(1000000)})

        self.assertIsNone(plugin.process(response))

    def test_indexof_plugin_detects_index_page(self):
        """IndexofResponsePlugin should detect Index Of pages."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(body=b'<title>Index of /</title>')

        self.assertEqual(plugin.process(response), 'indexof')

    def test_skipempty_plugin_detects_empty_success_page(self):
        """SkipemptyResponsePlugin should skip near-empty success pages."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(body=b'a', headers={'Content-Length': '10'})

        self.assertEqual(plugin.process(response), 'skip')

    def test_skipsizes_plugin_detects_matching_size(self):
        """SkipSizesResponsePlugin should skip configured response sizes."""

        plugin = SkipSizesResponsePlugin('1:2')
        response = self.make_response(body=b'a' * 2048, headers={'Content-Length': '2048'})

        self.assertEqual(plugin.process(response), 'skip')

    def test_collation_plugin_detects_false_positive_pages(self):
        """CollationResponsePlugin should mark identical long pages as failed."""

        plugin = CollationResponsePlugin(None)
        first = self.make_response(body=b'a' * 150, headers={'Content-Length': '150'})
        second = self.make_response(body=b'a' * 150, headers={'Content-Length': '150'})

        self.assertIsNone(plugin.process(first))
        self.assertEqual(plugin.process(second), 'failed')

    def test_collation_plugin_uses_ratio_match(self):
        """CollationResponsePlugin should also detect near-identical bodies by ratio."""

        plugin = CollationResponsePlugin(None)
        body1 = ('A' * 120 + 'B' * 30).encode()
        body2 = ('A' * 119 + 'B' * 31).encode()

        self.assertIsNone(plugin.process(self.make_response(body=body1, headers={'Content-Length': str(len(body1))})))
        self.assertEqual(plugin.process(self.make_response(body=body2, headers={'Content-Length': str(len(body2))})), 'failed')

    def test_collation_plugin_ignores_short_content(self):
        """CollationResponsePlugin should ignore short successful bodies."""

        plugin = CollationResponsePlugin(None)
        response = self.make_response(body=b'a' * 50, headers={'Content-Length': '50'})

        self.assertIsNone(plugin.process(response))
        self.assertEqual(plugin.previous_item, {})
        self.assertEqual(plugin.current_item, {})

    def test_collation_plugin_ignores_zero_content_length_header(self):
        """CollationResponsePlugin should ignore zero-length headers even when body exists."""

        plugin = CollationResponsePlugin(None)
        response = self.make_response(body=b'x' * 1000, headers={'Content-Length': '0'})

        self.assertIsNone(plugin.process(response))
        self.assertEqual(plugin.previous_item, {})

    def test_collation_plugin_uses_current_item_ratio_equality_branch(self):
        """CollationResponsePlugin should detect repeated ratios using current_item comparison."""

        plugin = CollationResponsePlugin(None)

        first = self.make_response(body=b'A' * 130, headers={'Content-Length': '130'})
        second = self.make_response(body=b'B' * 140, headers={'Content-Length': '140'})
        third = self.make_response(body=b'C' * 141, headers={'Content-Length': '141'})

        self.assertIsNone(plugin.process(first))
        self.assertIsNone(plugin.process(second))
        self.assertEqual(plugin.process(third), 'failed')

    def test_collation_plugin_returns_none_for_unsupported_status(self):
        """CollationResponsePlugin should ignore unsupported statuses."""

        plugin = CollationResponsePlugin(None)
        response = self.make_response(status=404, body=b'A' * 200, headers={'Content-Length': '200'})

        self.assertIsNone(plugin.process(response))


class TestResponsePluginLoader(unittest.TestCase):
    """TestResponsePluginLoader class."""

    def test_load_known_plugin_with_value(self):
        """ResponsePlugin.load() should load plugins with optional values."""

        plugin = ResponsePlugin.load('skipsizes=1:2')

        self.assertIsInstance(plugin, SkipSizesResponsePlugin)
        self.assertEqual(plugin.SIZE_VALUES, ['1KB', '2KB'])

    def test_load_raises_for_unknown_plugin(self):
        """ResponsePlugin.load() should reject unknown plugins."""

        with self.assertRaises(ResponsePluginError):
            ResponsePlugin.load('unknown')

    def test_load_wraps_import_error(self):
        """ResponsePlugin.load() should wrap import errors."""

        with patch('src.core.http.plugins.response_plugin.importlib.import_module', side_effect=ImportError):
            with self.assertRaises(ResponsePluginError):
                ResponsePlugin.load('file')


class TestResponseProvider(unittest.TestCase):
    """TestResponseProvider class."""

    def make_response(self, status=200, body=b'', headers=None):
        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_get_redirect_url_handles_absolute_and_relative(self):
        """ResponseProvider._get_redirect_url() should resolve absolute and relative locations."""

        response = self.make_response(status=301, headers={'Location': 'https://other.test/path'})
        self.assertEqual(ResponseProvider._get_redirect_url('http://example.com/a', response), 'https://other.test/path')

        response = self.make_response(status=301, headers={'Location': '/login'})
        self.assertEqual(ResponseProvider._get_redirect_url('http://example.com/a', response), 'http://example.com/login')

    def test_detect_maps_builtin_statuses(self):
        """ResponseProvider.detect() should classify standard HTTP statuses."""

        provider = ResponseProvider(SimpleNamespace())
        self.assertEqual(provider.detect('http://example.com', self.make_response(status=200)), 'success')
        self.assertEqual(provider.detect('http://example.com', self.make_response(status=404)), 'failed')
        self.assertEqual(provider.detect('http://example.com', self.make_response(status=401)), 'auth')
        self.assertEqual(provider.detect('http://example.com', self.make_response(status=403)), 'forbidden')
        self.assertEqual(provider.detect('http://example.com', self.make_response(status=400)), 'bad')
        self.assertEqual(provider.detect('http://example.com', self.make_response(status=496)), 'certificate')

    def test_detect_uses_plugins_first(self):
        """ResponseProvider.detect() should prefer plugin verdicts."""

        provider = ResponseProvider(SimpleNamespace())
        plugin = MagicMock()
        plugin.process.return_value = 'indexof'
        provider._response_plugins.append(plugin)

        self.assertEqual(provider.detect('http://example.com', self.make_response(status=200)), 'indexof')

    def test_detect_handles_redirect_and_unknown_status(self):
        """ResponseProvider.detect() should classify redirects and reject unknown statuses."""

        provider = ResponseProvider(SimpleNamespace())
        redirect_response = self.make_response(status=301, headers={'Location': '/next'})
        self.assertEqual(provider.detect('http://example.com/path', redirect_response), 'redirect')

        with self.assertRaises(Exception):
            provider.detect('http://example.com', self.make_response(status=999))

    def test_get_content_size_uses_header_or_body(self):
        """ResponseProvider._get_content_size() should use either Content-Length or body length."""

        header_response = self.make_response(body=b'abc', headers={'Content-Length': '2048'})
        body_response = self.make_response(body=b'abc', headers={})

        self.assertEqual(ResponseProvider._get_content_size(header_response), '2KB')
        self.assertEqual(ResponseProvider._get_content_size(body_response), '3B')


class TestResponse(unittest.TestCase):
    """TestResponse class."""

    def make_cfg(self, **kwargs):
        base = dict(is_sniff=False, sniffers=[], SUBDOMAINS_SCAN='subdomains', scan='directories')
        base.update(kwargs)
        return SimpleNamespace(**base)

    def make_debug(self, level=0):
        return SimpleNamespace(
            level=level,
            debug_load_sniffer_plugin=MagicMock(),
            debug_response=MagicMock(),
            debug_request_uri=MagicMock(),
        )

    def make_response(self, status=200, body=b'', headers=None):
        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_init_loads_plugins_when_sniff_enabled(self):
        """Response should load sniff plugins when enabled."""

        cfg = self.make_cfg(is_sniff=True, sniffers=['file'])
        debug = self.make_debug(level=1)

        response = Response(cfg, debug, tpl=MagicMock())

        self.assertEqual(len(response._response_plugins), 1)
        debug.debug_load_sniffer_plugin.assert_called_once()

    def test_init_wraps_plugin_errors(self):
        """Response.__init__() should wrap plugin loading failures."""

        cfg = self.make_cfg(is_sniff=True, sniffers=['unknown'])
        with self.assertRaises(ResponseError):
            Response(cfg, self.make_debug(), tpl=MagicMock())

    def test_handle_directory_success_and_redirect(self):
        """Response.handle() should process success and redirect directory responses."""

        cfg = self.make_cfg(scan='directories')
        debug = self.make_debug(level=3)
        response_handler = Response(cfg, debug, tpl=MagicMock())

        response = self.make_response(status=200, body=b'ok', headers={'Content-Length': '2'})
        status, url, size, code = response_handler.handle(response, 'http://example.com/path', 1, 2, [])
        self.assertEqual((status, url, size, code), ('success', 'http://example.com/path', '2B', '200'))
        debug.debug_request_uri.assert_called()

        redirect = self.make_response(status=301, body=b'', headers={'Location': '/next', 'Content-Length': '0'})
        status, url, size, code = response_handler.handle(redirect, 'http://example.com/path', 1, 2, [])
        self.assertEqual((status, url, size, code), ('redirect', 'http://example.com/next', '0B', '301'))

    def test_handle_redirect_becomes_failed_when_ignored(self):
        """Response.handle() should downgrade redirects to failed when target path is ignored."""

        cfg = self.make_cfg(scan='directories')
        debug = self.make_debug(level=0)
        response_handler = Response(cfg, debug, tpl=MagicMock())

        redirect = self.make_response(status=301, body=b'', headers={'Location': '/admin', 'Content-Length': '0'})
        status, url, size, code = response_handler.handle(redirect, 'http://example.com/path', 1, 2, ['admin'])

        self.assertEqual((status, url, size, code), ('failed', 'http://example.com/admin', '0B', '301'))

    def test_handle_subdomain_appends_ips_and_non_status_response(self):
        """Response.handle() should append IPs for subdomain scans and handle None-status responses."""

        cfg = self.make_cfg(scan='subdomains')
        debug = self.make_debug(level=0)
        response_handler = Response(cfg, debug, tpl=MagicMock())
        response = self.make_response(status=200, body=b'ok', headers={'Content-Length': '2'})

        with patch('src.core.http.response.Socket.get_ips_addresses', return_value='[127.0.0.1]'):
            status, url, size, code = response_handler.handle(response, 'http://sub.example.com', 1, 2, [])
        self.assertEqual((status, size, code), ('success', '2B', '200'))
        self.assertIn('[127.0.0.1]', url)

        no_status = SimpleNamespace(data=b'', headers={})
        with patch('src.core.http.response.Socket.get_ips_addresses', return_value=''):
            status, url, size, code = response_handler.handle(no_status, 'http://sub.example.com', 1, 2, [])
        self.assertEqual((status, url, size, code), ('failed', 'http://sub.example.com', '0B', '-'))

    def test_handle_wraps_detection_errors(self):
        """Response.handle() should wrap detection errors into ResponseError."""

        cfg = self.make_cfg(scan='directories')
        debug = self.make_debug(level=0)
        response_handler = Response(cfg, debug, tpl=MagicMock())
        response = self.make_response(status=999, body=b'', headers={})

        with self.assertRaises(ResponseError):
            response_handler.handle(response, 'http://example.com', 1, 2, [])


if __name__ == '__main__':
    unittest.main()