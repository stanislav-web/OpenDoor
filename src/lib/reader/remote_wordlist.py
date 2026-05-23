# -*- coding: utf-8 -*-

"""
    Remote wordlist downloader.

    Remote wordlists are treated as external, trusted input. The downloader
    stores the body in a managed local runtime file and enforces a hard size
    limit before the scan engine reads the file as a normal local wordlist.
"""

from dataclasses import dataclass
import codecs
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from src.core import filesystem


class RemoteWordlistError(Exception):
    """Raised when a remote wordlist cannot be downloaded safely."""


@dataclass(frozen=True)
class RemoteWordlistResult:
    """Downloaded remote wordlist metadata.

    :param url: Original remote wordlist URL.
    :param path: Runtime local file path.
    :param status: HTTP status code.
    :param bytes_downloaded: Number of downloaded bytes.
    :param content_type: Response Content-Type value.
    """

    url: str
    path: str
    status: int
    bytes_downloaded: int
    content_type: str | None = None


class RemoteWordlistDownloader(object):
    """Safely download one HTTP(S) wordlist into a local runtime file."""

    ALLOWED_SCHEMES = ('http', 'https')
    DEFAULT_MAX_BYTES = 500 * 1024 * 1024
    DEFAULT_TIMEOUT = 10
    CHUNK_SIZE = 1024 * 1024
    USER_AGENT = 'OpenDoor remote-wordlist-loader'

    def __init__(self, opener=None, progress_callback=None, max_bytes=None, chunk_size=None):
        """
        Create downloader.

        :param callable | None opener: URL opener compatible with urllib.request.urlopen.
        :param callable | None progress_callback: Callback receiving downloaded, total, done.
        :param int | None max_bytes: Maximum allowed remote body size.
        :param int | None chunk_size: Streaming chunk size.
        """

        self.__opener = opener or urlopen
        self.__progress_callback = progress_callback
        self.__max_bytes = int(max_bytes or self.DEFAULT_MAX_BYTES)
        self.__chunk_size = int(chunk_size or self.CHUNK_SIZE)

    @property
    def max_bytes(self):
        """Return maximum allowed remote body size in bytes.

        :return: Maximum bytes.
        :rtype: int
        """

        return self.__max_bytes

    def download(self, url, output_path, timeout=None):
        """
        Download URL to output_path with strict size and UTF-8 validation.

        :param str url: Remote HTTP(S) wordlist URL.
        :param str output_path: Local runtime output file.
        :param int | float | None timeout: Request timeout in seconds.
        :raise RemoteWordlistError:
        :return: Download metadata.
        :rtype: RemoteWordlistResult
        """

        url = self._validate_url(url)
        timeout = self._normalize_timeout(timeout)
        request = Request(url, headers={'User-Agent': self.USER_AGENT})

        try:
            with self.__opener(request, timeout=timeout) as response:
                status = self._response_status(response)
                headers = getattr(response, 'headers', {}) or {}
                content_type = self._header_value(headers, 'Content-Type')
                content_length = self._parse_content_length(self._header_value(headers, 'Content-Length'))

                if status < 200 or status >= 300:
                    raise RemoteWordlistError(
                        'Remote wordlist download failed: HTTP status {0} for {1}'.format(status, url)
                    )

                self._reject_if_too_large(content_length, url)
                bytes_downloaded = self._stream_to_file(response, output_path, content_length)

                if bytes_downloaded <= 0:
                    self._remove_partial(output_path)
                    raise RemoteWordlistError('Remote wordlist is empty: {0}'.format(url))

                self._emit_progress(bytes_downloaded, content_length or bytes_downloaded, done=True)
                return RemoteWordlistResult(
                    url=url,
                    path=output_path,
                    status=status,
                    bytes_downloaded=bytes_downloaded,
                    content_type=content_type,
                )
        except HTTPError as error:
            status = error.code
            self._close_quietly(error)
            raise RemoteWordlistError(
                'Remote wordlist download failed: HTTP status {0} for {1}'.format(status, url)
            )
        except URLError as error:
            raise RemoteWordlistError('Remote wordlist download failed: {0}'.format(error.reason))
        except UnicodeDecodeError:
            self._remove_partial(output_path)
            raise RemoteWordlistError('Remote wordlist must be valid UTF-8 text: {0}'.format(url))
        except OSError as error:
            self._remove_partial(output_path)
            raise RemoteWordlistError('Remote wordlist download failed: {0}'.format(error))

    @staticmethod
    def _close_quietly(resource):
        """Close a urllib resource without masking the original error.

        :param object resource: Resource with optional close() method.
        :return: None
        """

        close = getattr(resource, 'close', None)
        if not callable(close):
            return

        try:
            close()
        except (OSError, ValueError):
            pass

    @classmethod
    def _validate_url(cls, url):
        """
        Validate remote wordlist URL.

        :param str url: Input URL.
        :raise RemoteWordlistError:
        :return: Normalized URL.
        :rtype: str
        """

        value = str(url or '').strip()
        parsed = urlsplit(value)
        scheme = parsed.scheme.lower()

        if scheme not in cls.ALLOWED_SCHEMES:
            raise RemoteWordlistError(
                'Remote wordlist supports only http:// or https:// URLs. Got: {0}'.format(url)
            )

        if not parsed.netloc:
            raise RemoteWordlistError('Remote wordlist URL is missing host: {0}'.format(url))

        return value

    @classmethod
    def _normalize_timeout(cls, timeout):
        """
        Normalize timeout value.

        :param int | float | None timeout: Raw timeout.
        :return: Timeout in seconds.
        :rtype: int | float
        """

        try:
            value = float(timeout)
        except (TypeError, ValueError):
            return cls.DEFAULT_TIMEOUT

        if value <= 0:
            return cls.DEFAULT_TIMEOUT

        return value

    @staticmethod
    def _response_status(response):
        """
        Resolve status from urllib-like response.

        :param object response: Response object.
        :return: HTTP status code.
        :rtype: int
        """

        status = getattr(response, 'status', None)
        if status is None and hasattr(response, 'getcode'):
            status = response.getcode()
        return int(status or 0)

    @staticmethod
    def _header_value(headers, name):
        """
        Read a response header from mapping-like objects.

        :param object headers: Header mapping.
        :param str name: Header name.
        :return: Header value or None.
        :rtype: str | None
        """

        getter = getattr(headers, 'get', None)
        if callable(getter):
            return getter(name) or getter(name.lower())
        return None

    @staticmethod
    def _parse_content_length(value):
        """
        Parse Content-Length safely.

        :param str | None value: Header value.
        :return: Parsed length or None.
        :rtype: int | None
        """

        if value is None:
            return None

        try:
            parsed = int(str(value).strip())
        except (TypeError, ValueError):
            return None

        return parsed if parsed >= 0 else None

    def _reject_if_too_large(self, content_length, url):
        """
        Reject known oversized response before body download.

        :param int | None content_length: Response Content-Length.
        :param str url: Remote URL.
        :raise RemoteWordlistError:
        :return: None
        """

        if content_length is None or content_length <= self.__max_bytes:
            return

        raise RemoteWordlistError(self._too_large_message(content_length, url))

    def _stream_to_file(self, response, output_path, total_bytes=None):
        """
        Stream response body into a local file while validating UTF-8.

        :param object response: Response body object.
        :param str output_path: Output file path.
        :param int | None total_bytes: Expected size if known.
        :raise RemoteWordlistError:
        :raise UnicodeDecodeError:
        :return: Downloaded byte count.
        :rtype: int
        """

        directory = os.path.dirname(os.path.abspath(output_path))
        if directory:
            filesystem.makedir(directory)

        decoder = codecs.getincrementaldecoder('utf-8')()
        downloaded = 0

        try:
            with open(output_path, 'wb') as output_file:
                while True:
                    chunk = response.read(self.__chunk_size)
                    if not chunk:
                        break

                    decoder.decode(chunk)
                    downloaded += len(chunk)

                    if downloaded > self.__max_bytes:
                        raise RemoteWordlistError(self._too_large_message(downloaded))

                    output_file.write(chunk)
                    self._emit_progress(downloaded, total_bytes, done=False)

                decoder.decode(b'', final=True)
        except Exception:
            self._remove_partial(output_path)
            raise

        return downloaded

    def _too_large_message(self, actual_bytes, url=None):
        """
        Build a user-facing oversized-wordlist message.

        :param int actual_bytes: Actual or declared body size.
        :param str | None url: Remote URL.
        :return: Error message.
        :rtype: str
        """

        source = '' if url is None else ' ({0})'.format(url)
        return (
            'Remote wordlist is too large{source}: {actual}. '
            'Maximum supported remote wordlist size is {limit}. '
            'Download this wordlist separately and pass the local file path with --wordlist.'
        ).format(
            source=source,
            actual=self._format_bytes(actual_bytes),
            limit=self._format_bytes(self.__max_bytes),
        )

    def _emit_progress(self, downloaded, total_bytes=None, done=False):
        """
        Emit optional progress callback.

        :param int downloaded: Downloaded bytes.
        :param int | None total_bytes: Total bytes if known.
        :param bool done: Whether download is complete.
        :return: None
        """

        if self.__progress_callback is None:
            return

        self.__progress_callback(downloaded, total_bytes, done)

    @staticmethod
    def _remove_partial(path):
        """
        Remove a partially downloaded file.

        :param str path: File path.
        :return: None
        """

        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    @staticmethod
    def _format_bytes(value):
        """
        Format byte size for CLI messages.

        :param int value: Size in bytes.
        :return: Human-readable size.
        :rtype: str
        """

        try:
            size = float(value)
        except (TypeError, ValueError):
            return 'unknown size'

        units = ('B', 'KB', 'MB', 'GB')
        index = 0
        while size >= 1024 and index < len(units) - 1:
            size /= 1024.0
            index += 1

        if index == 0:
            return '{0}B'.format(int(size))

        return '{0:.1f}{1}'.format(size, units[index])
