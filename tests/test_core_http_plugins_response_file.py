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

    def test_returns_none_for_large_html_page_with_content_length(self):
        """Should not classify large HTML documents as files."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'<html>' + (b'x' * 1000001) + b'</html>',
            headers={
                'Content-Type': 'text/html; charset=utf-8',
                'Content-Length': '1000014',
            }
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_large_json_response_with_content_length(self):
        """Should not classify large JSON API responses as files."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'{"items":[' + (b'1,' * 500001) + b'0]}',
            headers={
                'Content-Type': 'application/json',
                'Content-Length': '1000014',
            }
        )

        self.assertIsNone(plugin.process(response))

    def test_detects_large_unknown_content_type_as_file(self):
        """Should keep fallback detection for large unknown responses."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'x' * 1000001,
            headers={'Content-Type': 'application/x-custom-dump'}
        )

        self.assertEqual(plugin.process(response), 'file')

    def test_text_wildcard_content_type_is_not_file_by_size(self):
        """Should treat text/* responses as textual even when they are large."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'x' * 1000001,
            headers={
                'Content-Type': 'text/csv',
                'Content-Length': '1000001',
            }
        )

        self.assertIsNone(plugin.process(response))

    def test_request_filename_helper_handles_missing_and_empty_urls(self):
        """Request filename extraction should safely handle missing URL metadata."""

        response = self.make_response(body=b'', headers={})
        response.opendoor_request_url = None
        self.assertEqual(FileResponsePlugin._extract_request_filename(response), '')

        response.opendoor_request_url = 'https://example.com'
        self.assertEqual(FileResponsePlugin._extract_request_filename(response), '')

    def test_detects_generic_db_path_without_body_or_content_type(self):
        """Should classify arbitrary .db paths as file for HEAD-like responses."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(body=b'', headers={})
        response.opendoor_request_url = 'https://example.com/assets/custom-cache.db'

        self.assertEqual(plugin.process(response), 'file')

    def test_detects_encoded_generic_db_path(self):
        """Should classify URL-encoded .db path basenames."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(body=b'', headers={})
        response.opendoor_request_url = 'https://example.com/assets/catalog%2Edb'

        self.assertEqual(plugin.process(response), 'file')

    def test_detects_thumbs_db_as_generic_db_path(self):
        """Should classify Thumbs.db through the generic .db extension rule."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(body=b'', headers={})
        response.opendoor_request_url = 'https://example.com/images/Thumbs.db'

        self.assertEqual(plugin.process(response), 'file')

    def test_detects_ole_compound_file_magic_as_file(self):
        """Should classify OLE Compound File bodies as files."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + (b'\x00' * 16),
            headers={}
        )

        self.assertEqual(plugin.process(response), 'file')

    def test_detects_small_zip_file_by_magic_even_when_mislabelled(self):
        """Should classify real small ZIP archives even with bad MIME headers."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'PK\x03\x04' + (b'\x00' * 128),
            headers={
                'Content-Type': 'text/html; charset=utf-8',
                'Content-Length': '132',
            }
        )
        response.opendoor_request_url = 'https://example.com/Archive.zip'

        self.assertEqual(plugin.process(response), 'file')

    def test_detects_small_archive_path_with_unknown_content_type(self):
        """Should classify explicit small archive paths as file findings."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'\x00\x01\x02' * 20000,
            headers={
                'Content-Type': 'application/x-custom',
                'Content-Length': '60000',
            }
        )
        response.opendoor_request_url = 'https://example.com/Archive.zip'

        self.assertEqual(plugin.process(response), 'file')

    def test_archive_path_does_not_override_html_fallback(self):
        """Should not classify soft-200 HTML catch-all pages as archive files."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'<html><body>Not found</body></html>',
            headers={
                'Content-Type': 'text/html; charset=utf-8',
                'Content-Length': '35',
            }
        )
        response.opendoor_request_url = 'https://example.com/Archive.zip'

        self.assertIsNone(plugin.process(response))

    def test_db_path_does_not_override_html_fallback(self):
        """Should not classify soft-200 HTML catch-all pages as files by path alone."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'<html><body>Not found</body></html>',
            headers={
                'Content-Type': 'text/html; charset=utf-8',
                'Content-Length': '35',
            }
        )
        response.opendoor_request_url = 'https://example.com/assets/custom-cache.db'

        self.assertIsNone(plugin.process(response))

    def test_db_path_does_not_override_text_fallback(self):
        """Should not classify textual fallback payloads as files by .db path."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(
            body=b'not found',
            headers={
                'Content-Type': 'text/plain',
                'Content-Length': '9',
            }
        )
        response.opendoor_request_url = 'https://example.com/assets/custom-cache.db'

        self.assertIsNone(plugin.process(response))

    def test_non_db_path_with_empty_unknown_response_is_not_file(self):
        """Should keep empty unknown non-.db responses out of file findings."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(body=b'', headers={})
        response.opendoor_request_url = 'https://example.com/assets/custom-cache.bin'

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
