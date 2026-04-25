# -*- coding: utf-8 -*-

import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response.file import FileResponsePlugin


class TestFileResponsePlugin(unittest.TestCase):
    """Coverage and regression tests for FileResponsePlugin."""

    def make_response(self, status=200, body=b'', headers=None):
        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_detects_large_body_without_content_length_header(self):
        """Should classify a large body as file even without Content-Length."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(body=b'x' * 1000001, headers={})

        self.assertEqual(plugin.process(response), 'file')

    def test_detects_attachment_header_as_file(self):
        """Should classify attachment responses as files even when they are small."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'hello',
            headers={
                'Content-Disposition': 'attachment; filename="dump.sql"',
                'Content-Type': 'text/plain',
            }
        )

        self.assertEqual(plugin.process(response), 'file')

    def test_detects_binary_content_type_as_file(self):
        """Should classify binary content types as files."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'%PDF-1.7',
            headers={'Content-Type': 'application/pdf'}
        )

        self.assertEqual(plugin.process(response), 'file')

    def test_detects_large_body_when_content_length_is_invalid(self):
        """Should fall back to body length when Content-Length is invalid."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'x' * 1000001,
            headers={'Content-Length': 'invalid'}
        )

        self.assertEqual(plugin.process(response), 'file')

    def test_returns_none_for_small_html_page(self):
        """Should not classify a normal small HTML page as file."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'<html><body>Hello</body></html>',
            headers={'Content-Type': 'text/html'}
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_empty_binary_response_without_size(self):
        """Should not classify empty binary-like responses without content as file."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'',
            headers={'Content-Type': 'application/octet-stream'}
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_unsupported_status(self):
        """Should ignore unsupported statuses."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            status=404,
            body=b'x' * 1000001,
            headers={'Content-Length': '1000001'}
        )

        self.assertIsNone(plugin.process(response))