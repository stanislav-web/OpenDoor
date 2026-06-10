# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from urllib.error import HTTPError, URLError
from unittest.mock import MagicMock, patch

from src.lib.reader.remote_wordlist import RemoteWordlistDownloader, RemoteWordlistError


class FakeHeaders(dict):
    """Case-tolerant minimal header mapping for downloader tests."""

    def get(self, key, default=None):
        """Return header by exact or lower-case key."""

        return super().get(key, super().get(str(key).lower(), default))


class FakeResponse:
    """Minimal urllib-like streaming response."""

    def __init__(self, chunks, status=200, headers=None):
        """
        Create fake response.

        :param list[bytes] chunks: Response chunks.
        :param int status: HTTP status code.
        :param dict | None headers: Response headers.
        """

        self._chunks = list(chunks)
        self.status = status
        self.headers = FakeHeaders(headers or {})

    def __enter__(self):
        """Enter context manager."""

        return self

    def __exit__(self, exc_type, exc, _tb):
        """Exit context manager."""

        return False

    def read(self, size):
        """Read next chunk."""

        if len(self._chunks) <= 0:
            return b''
        return self._chunks.pop(0)

    def getcode(self):
        """Return HTTP status code."""

        return self.status


class TestRemoteWordlistDownloader(unittest.TestCase):
    """Remote wordlist downloader tests."""

    def make_output_path(self):
        """
        Create a temporary output path.

        :return: Output file path.
        :rtype: str
        """

        tmpdir = tempfile.mkdtemp(prefix='opendoor-remote-wordlist-test-')
        self.addCleanup(lambda: os.path.exists(tmpdir) and __import__('shutil').rmtree(tmpdir, ignore_errors=True))
        return os.path.join(tmpdir, 'wordlist.tmp')

    def test_download_writes_utf8_body_and_emits_progress(self):
        """Downloader should stream a valid UTF-8 remote wordlist to disk."""

        events = []

        def opener(request, timeout=None):
            self.assertEqual(request.full_url, 'https://example.test/list.txt')
            self.assertEqual(timeout, 3.0)
            return FakeResponse(
                [b'admin\n', b'login\n'],
                headers={'Content-Length': '12', 'Content-Type': 'text/plain'},
            )

        downloader = RemoteWordlistDownloader(
            opener=opener,
            progress_callback=lambda downloaded, total, done: events.append((downloaded, total, done)),
            max_bytes=1024,
            chunk_size=6,
        )
        output_path = self.make_output_path()

        result = downloader.download('https://example.test/list.txt', output_path, timeout=3)

        self.assertEqual(result.status, 200)
        self.assertEqual(result.bytes_downloaded, 12)
        self.assertEqual(result.content_type, 'text/plain')
        with open(output_path, 'rb') as handler:
            self.assertEqual(handler.read(), b'admin\nlogin\n')
        self.assertIn((12, 12, True), events)

    def test_download_rejects_invalid_scheme(self):
        """Only HTTP(S) remote wordlist URLs should be accepted."""

        downloader = RemoteWordlistDownloader(opener=lambda *_args, **_kwargs: None)

        with self.assertRaisesRegex(RemoteWordlistError, 'supports only http:// or https://'):
            downloader.download('ftp://example.test/list.txt', self.make_output_path())

    def test_download_rejects_missing_host(self):
        """Remote URL should include a host."""

        downloader = RemoteWordlistDownloader(opener=lambda *_args, **_kwargs: None)

        with self.assertRaisesRegex(RemoteWordlistError, 'missing host'):
            downloader.download('https:///list.txt', self.make_output_path())

    def test_download_rejects_non_2xx_status(self):
        """Non-2xx response should fail clearly."""

        downloader = RemoteWordlistDownloader(
            opener=lambda *_args, **_kwargs: FakeResponse([b'nope'], status=404),
        )

        with self.assertRaisesRegex(RemoteWordlistError, 'HTTP status 404'):
            downloader.download('https://example.test/missing.txt', self.make_output_path())

    def test_download_rejects_http_error(self):
        """urllib HTTPError should be converted to RemoteWordlistError."""

        def opener(_request, timeout=None):
            raise HTTPError('https://example.test/list.txt', 500, 'boom', hdrs=None, fp=None)

        downloader = RemoteWordlistDownloader(opener=opener)

        with self.assertRaisesRegex(RemoteWordlistError, 'HTTP status 500'):
            downloader.download('https://example.test/list.txt', self.make_output_path())

    def test_download_rejects_url_error(self):
        """urllib URLError should be converted to RemoteWordlistError."""

        def opener(_request, timeout=None):
            raise URLError('network down')

        downloader = RemoteWordlistDownloader(opener=opener)

        with self.assertRaisesRegex(RemoteWordlistError, 'network down'):
            downloader.download('https://example.test/list.txt', self.make_output_path())

    def test_download_rejects_declared_oversized_body_before_read(self):
        """Content-Length above max_bytes should fail before body streaming."""

        response = FakeResponse([b'admin\n'], headers={'Content-Length': '2048'})
        downloader = RemoteWordlistDownloader(
            opener=lambda *_args, **_kwargs: response,
            max_bytes=1024,
        )

        with self.assertRaisesRegex(RemoteWordlistError, 'too large'):
            downloader.download('https://example.test/huge.txt', self.make_output_path())

        self.assertEqual(response._chunks, [b'admin\n'])

    def test_download_rejects_stream_that_exceeds_limit_without_content_length(self):
        """Streaming limit should stop unknown-length oversized bodies."""

        output_path = self.make_output_path()
        downloader = RemoteWordlistDownloader(
            opener=lambda *_args, **_kwargs: FakeResponse([b'a' * 8, b'b' * 8]),
            max_bytes=10,
            chunk_size=8,
        )

        with self.assertRaisesRegex(RemoteWordlistError, 'Download this wordlist separately'):
            downloader.download('https://example.test/huge.txt', output_path)

        self.assertFalse(os.path.exists(output_path))

    def test_download_rejects_empty_body(self):
        """Empty remote body should fail before scan setup."""

        output_path = self.make_output_path()
        downloader = RemoteWordlistDownloader(
            opener=lambda *_args, **_kwargs: FakeResponse([]),
        )

        with self.assertRaisesRegex(RemoteWordlistError, 'empty'):
            downloader.download('https://example.test/empty.txt', output_path)

        self.assertFalse(os.path.exists(output_path))

    def test_download_rejects_non_utf8_body_and_removes_partial_file(self):
        """Remote wordlist must be valid UTF-8 text."""

        output_path = self.make_output_path()
        downloader = RemoteWordlistDownloader(
            opener=lambda *_args, **_kwargs: FakeResponse([b'admin\n', b'\xff']),
        )

        with self.assertRaisesRegex(RemoteWordlistError, 'valid UTF-8'):
            downloader.download('https://example.test/binary.txt', output_path)

        self.assertFalse(os.path.exists(output_path))

    def test_format_bytes_uses_human_readable_units(self):
        """Byte formatter should keep CLI limit messages readable."""

        self.assertEqual(RemoteWordlistDownloader._format_bytes(500 * 1024 * 1024), '500.0MB')
        self.assertEqual(RemoteWordlistDownloader._format_bytes(1024 * 1024 * 1024), '1.0GB')

    def test_max_bytes_property_returns_configured_limit(self):
        """max_bytes should expose the configured safety limit."""

        downloader = RemoteWordlistDownloader(opener=lambda *_args, **_kwargs: None, max_bytes=123)

        self.assertEqual(downloader.max_bytes, 123)

    def test_download_closes_http_error_resource(self):
        """HTTPError resources should be closed before converting the error."""

        error = HTTPError('https://example.test/list.txt', 500, 'boom', hdrs=None, fp=None)
        original_close = error.close
        error.close = MagicMock(side_effect=original_close)

        def opener(_request, timeout=None):
            raise error

        downloader = RemoteWordlistDownloader(opener=opener)

        with self.assertRaisesRegex(RemoteWordlistError, 'HTTP status 500'):
            downloader.download('https://example.test/list.txt', self.make_output_path())

        error.close.assert_called_once_with()

    def test_download_converts_os_error_and_removes_partial_file(self):
        """Filesystem errors should be converted and cleanup should be attempted."""

        output_path = self.make_output_path()
        downloader = RemoteWordlistDownloader(
            opener=lambda *_args, **_kwargs: FakeResponse([b'admin\n']),
        )

        with patch('src.lib.reader.remote_wordlist.open', side_effect=OSError('disk full')), \
                patch.object(RemoteWordlistDownloader, '_remove_partial') as remove_mock:
            with self.assertRaisesRegex(RemoteWordlistError, 'disk full'):
                downloader.download('https://example.test/list.txt', output_path)

        remove_mock.assert_any_call(output_path)

    def test_normalize_timeout_uses_default_for_invalid_or_non_positive_values(self):
        """Invalid timeout values should fall back to the safe default."""

        self.assertEqual(RemoteWordlistDownloader._normalize_timeout(None), RemoteWordlistDownloader.DEFAULT_TIMEOUT)
        self.assertEqual(RemoteWordlistDownloader._normalize_timeout('nope'), RemoteWordlistDownloader.DEFAULT_TIMEOUT)
        self.assertEqual(RemoteWordlistDownloader._normalize_timeout(0), RemoteWordlistDownloader.DEFAULT_TIMEOUT)
        self.assertEqual(RemoteWordlistDownloader._normalize_timeout(-1), RemoteWordlistDownloader.DEFAULT_TIMEOUT)
        self.assertEqual(RemoteWordlistDownloader._normalize_timeout(2.5), 2.5)

    def test_response_status_uses_getcode_when_status_attribute_is_missing(self):
        """urllib-like responses without .status should still be supported."""

        class GetCodeOnlyResponse:
            def getcode(self):
                return 204

        self.assertEqual(RemoteWordlistDownloader._response_status(GetCodeOnlyResponse()), 204)

    def test_header_value_returns_none_for_non_mapping_headers(self):
        """Header lookup should tolerate unexpected header containers."""

        self.assertIsNone(RemoteWordlistDownloader._header_value(object(), 'Content-Length'))

    def test_parse_content_length_ignores_invalid_and_negative_values(self):
        """Bad Content-Length values should not crash or become trusted sizes."""

        self.assertIsNone(RemoteWordlistDownloader._parse_content_length('bad'))
        self.assertIsNone(RemoteWordlistDownloader._parse_content_length('-1'))
        self.assertEqual(RemoteWordlistDownloader._parse_content_length('42'), 42)

    def test_remove_partial_ignores_os_error(self):
        """Best-effort cleanup should not mask the original failure."""

        with patch('src.lib.reader.remote_wordlist.os.path.exists', return_value=True), \
                patch('src.lib.reader.remote_wordlist.os.remove', side_effect=OSError('locked')):
            RemoteWordlistDownloader._remove_partial('/tmp/partial-wordlist')

    def test_close_quietly_ignores_missing_close_method(self):
        """Closing helper should tolerate objects without close()."""

        RemoteWordlistDownloader._close_quietly(object())

    def test_close_quietly_ignores_close_errors(self):
        """Closing helper should not mask the HTTPError conversion path."""

        resource = MagicMock()
        resource.close.side_effect = OSError('already closed')

        RemoteWordlistDownloader._close_quietly(resource)

        resource.close.assert_called_once_with()

    def test_stream_to_file_tolerates_empty_directory_name(self):
        """Streaming helper should tolerate paths whose dirname resolves to an empty value."""

        downloader = RemoteWordlistDownloader(
            opener=lambda *_args, **_kwargs: None,
            progress_callback=None,
        )
        response = FakeResponse([b'admin\n'])
        output_path = self.make_output_path()

        with patch('src.lib.reader.remote_wordlist.os.path.abspath', return_value='wordlist.tmp'), \
                patch('src.lib.reader.remote_wordlist.os.path.dirname', return_value=''), \
                patch('src.lib.reader.remote_wordlist.filesystem.makedir') as makedir_mock:
            downloaded = downloader._stream_to_file(response, output_path)

        self.assertEqual(downloaded, 6)
        makedir_mock.assert_not_called()

    def test_format_bytes_handles_unknown_values(self):
        """Byte formatter should handle invalid values in defensive paths."""

        self.assertEqual(RemoteWordlistDownloader._format_bytes(None), 'unknown size')

if __name__ == '__main__':
    unittest.main()
