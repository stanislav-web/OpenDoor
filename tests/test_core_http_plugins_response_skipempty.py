# -*- coding: utf-8 -*-

import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response.skipempty import SkipemptyResponsePlugin


class TestSkipemptyResponsePlugin(unittest.TestCase):
    """Coverage and regression tests for SkipemptyResponsePlugin."""

    def make_response(self, status=200, body=b'', headers=None):
        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_skips_short_body_without_content_length(self):
        """Should keep legacy behavior for short body-only responses."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(body=b'x' * 10, headers={})

        self.assertEqual(plugin.process(response), 'skip')

    def test_returns_none_for_large_content_length(self):
        """Should not skip when Content-Length is above the threshold."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(body=b'x' * 10, headers={'Content-Length': '700'})

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_meaningful_small_json(self):
        """Should not skip small JSON payloads with useful data."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(
            body=b'{"status":"ok","id":1}',
            headers={'Content-Type': 'application/json'}
        )

        self.assertIsNone(plugin.process(response))

    def test_skips_empty_json_object(self):
        """Should skip semantically empty JSON payloads."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(
            body=b'{}',
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(plugin.process(response), 'skip')

    def test_returns_none_for_login_page(self):
        """Should not skip login pages."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(
            body=b'<html><body><form><input type="password" name="password"></form></body></html>',
            headers={'Content-Type': 'text/html'}
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_directory_listing_page(self):
        """Should not skip short directory listing pages."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(
            body=(
                b'<html><head><title>Index of /backup/</title></head>'
                b'<body><a href="../">Parent Directory</a></body></html>'
            ),
            headers={'Content-Type': 'text/html'}
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_attachment_response(self):
        """Should not skip attachment responses."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(
            body=b'abc',
            headers={'Content-Disposition': 'attachment; filename="dump.sql"'}
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_binary_content_type(self):
        """Should not skip binary/file-like content types."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(
            body=b'abc',
            headers={'Content-Type': 'application/octet-stream'}
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_unsupported_status(self):
        """Should ignore unsupported statuses."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(status=404, body=b'x' * 10, headers={})

        self.assertIsNone(plugin.process(response))