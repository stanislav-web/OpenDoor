# -*- coding: utf-8 -*-

import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response.file import FileResponsePlugin


class TestFileResponsePluginSoft404Fallback(unittest.TestCase):
    """Regression tests for extension-based file findings on soft fallback pages."""

    def make_response(self, status=200, body=b'', headers=None, url='https://example.com/users/backup.db'):
        response = HTTPResponse(status=status, body=body, headers=headers or {})
        response.opendoor_request_url = url
        return response

    def test_db_path_does_not_override_headerless_html_fallback(self):
        """Should not classify headerless soft-404 HTML pages as DB files."""

        response = self.make_response(
            body=(
                b'<!doctype html><html><head><title>404</title></head>'
                b'<body>Not found</body></html>'
            ),
        )

        self.assertIsNone(FileResponsePlugin(None).process(response))

    def test_db_path_does_not_override_unknown_type_html_fallback(self):
        """Should not trust .db extension when body is visibly HTML fallback."""

        response = self.make_response(
            body=b'<html><body>Page not found</body></html>',
            headers={'Content-Type': 'application/x-custom'},
        )

        self.assertIsNone(FileResponsePlugin(None).process(response))

    def test_db_path_does_not_override_json_error_fallback(self):
        """Should not classify JSON error payloads as DB files by path alone."""

        response = self.make_response(
            body=b'{"status":404,"error":"not found"}',
            headers={'Content-Type': 'application/x-custom'},
        )

        self.assertIsNone(FileResponsePlugin(None).process(response))

    def test_db_path_keeps_real_binary_body_with_unknown_content_type(self):
        """Should still classify .db responses that contain binary-looking data."""

        response = self.make_response(
            body=b'SQLite format 3\x00' + (b'\x00' * 64),
            headers={'Content-Type': 'application/x-custom'},
        )

        self.assertEqual(FileResponsePlugin(None).process(response), 'file')

    def test_db_path_ignores_non_success_html_fallback(self):
        """Should not report explicit 404 HTML pages as files."""

        response = self.make_response(
            status=404,
            body=b'<html><body>Not found</body></html>',
            headers={'Content-Type': 'text/html; charset=utf-8'},
        )

        self.assertIsNone(FileResponsePlugin(None).process(response))


if __name__ == '__main__':
    unittest.main()
