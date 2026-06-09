# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development: Stanislav WEB
"""

from urllib.parse import unquote, urlsplit

from .provider import ResponsePluginProvider


class FileResponsePlugin(ResponsePluginProvider):
    """Detect large files and explicit download/binary responses."""

    DESCRIPTION = 'File (detect large files and explicit downloads)'
    RESPONSE_INDEX = 'file'
    DEFAULT_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    DEFAULT_SOURCE_DETECT_MIN_SIZE = 1000000
    OLE_COMPOUND_FILE_MAGIC = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    DATABASE_FILE_EXTENSIONS = ('.db',)

    BINARY_CONTENT_TYPES = (
        'application/octet-stream',
        'application/zip',
        'application/x-zip-compressed',
        'application/gzip',
        'application/x-gzip',
        'application/x-tar',
        'application/x-7z-compressed',
        'application/x-rar-compressed',
        'application/pdf',
        'application/x-sqlite3',
        'application/vnd.sqlite3',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument',
        'application/msword',
        'application/vnd.ms-powerpoint',
        'image/',
        'audio/',
        'video/',
    )

    TEXTUAL_CONTENT_TYPES = (
        'text/html',
        'text/plain',
        'text/css',
        'text/javascript',
        'application/javascript',
        'application/x-javascript',
        'application/json',
        'application/xml',
        'text/xml',
        'application/xhtml+xml',
        'application/x-shockwave-flash',
        'image/svg+xml',
    )

    def __init__(self, _void):
        """
        ResponsePluginProvider constructor.
        """

        ResponsePluginProvider.__init__(self)

    @classmethod
    def _has_ole_compound_file_magic(cls, response):
        """
        Determine whether the response body starts with the OLE CFB magic.

        Windows thumbnail caches and other legacy database-like binary files can
        be small enough to avoid size-based detection.

        :param response: HTTP response
        :return: bool
        """

        data = getattr(response, 'data', b'')
        if not isinstance(data, (bytes, bytearray)):
            return False

        return bytes(data).startswith(cls.OLE_COMPOUND_FILE_MAGIC)

    @classmethod
    def _extract_request_filename(cls, response):
        """
        Extract the lowercase basename from the request URL attached by Response.

        :param response: HTTP response
        :return: URL path basename
        :rtype: str
        """

        request_url = getattr(response, 'opendoor_request_url', '')
        if request_url is None:
            return ''

        try:
            path = urlsplit(str(request_url).split()[0]).path
        except Exception:
            return ''

        if len(path) <= 0:
            return ''

        return unquote(path.rsplit('/', 1)[-1]).strip().lower()

    def _has_database_file_extension(self, response):
        """
        Detect generic database-like file paths by extension.

        The rule intentionally uses the extension rather than exact filenames so
        Windows thumbnail caches and custom database files such as `cache.db`,
        `catalog.db`, or `assets.db` are classified consistently.

        :param response: HTTP response
        :return: bool
        """

        filename = self._extract_request_filename(response)
        if len(filename) <= 0:
            return False

        return any(filename.endswith(extension) for extension in self.DATABASE_FILE_EXTENSIONS)

    def _looks_like_textual_fallback(self, content_type, body_length, content_length):
        """
        Return True when an extension hit likely resolved to a soft-200 page.

        Extension-based classification is useful for small or HEAD-only file
        responses, but it must not turn ordinary HTML catch-all pages into file
        findings.

        :param str content_type: normalized content type
        :param int body_length: decoded body length
        :param int | None content_length: parsed Content-Length
        :return: bool
        """

        if self._is_textual_content_type(content_type) is not True:
            return False

        if content_type in ('text/html', 'application/xhtml+xml'):
            return True

        return 0 < body_length or (content_length is not None and 0 < content_length)

    def _is_textual_content_type(self, content_type):
        """
        Determine whether a Content-Type is a textual web/API response.

        :param str content_type: normalized content type
        :return: bool
        """

        if len(content_type) <= 0:
            return False

        if content_type.startswith('text/'):
            return True

        for item in self.TEXTUAL_CONTENT_TYPES:
            if content_type == item:
                return True

        return False

    def _is_binary_content_type(self, content_type):
        """
        Determine whether a Content-Type looks like a real file/binary response.

        :param str content_type: normalized content type
        :return: bool
        """

        if len(content_type) <= 0:
            return False

        if self._is_textual_content_type(content_type) is True:
            return False

        for item in self.BINARY_CONTENT_TYPES:
            if content_type.startswith(item):
                return True

        return False

    def process(self, response):
        """
        Process data.

        :param response: HTTP response
        :return: str | None
        """

        if response.status not in self.DEFAULT_STATUSES:
            return None

        super().process(response)

        body_length = len(self._body)
        content_length = self._extract_content_length()
        content_type = self._extract_content_type()
        content_disposition = str(self._get_header('Content-Disposition') or '').lower()
        has_content = (content_length is not None and 0 < content_length) or 0 < body_length

        if self._has_ole_compound_file_magic(response) is True:
            return self.RESPONSE_INDEX

        if 'attachment' in content_disposition and has_content:
            return self.RESPONSE_INDEX

        if self._has_database_file_extension(response) is True \
                and self._looks_like_textual_fallback(content_type, body_length, content_length) is not True:
            return self.RESPONSE_INDEX

        if self._is_binary_content_type(content_type) and has_content:
            return self.RESPONSE_INDEX

        if self._is_textual_content_type(content_type) is True:
            return None

        if content_length is not None and self.DEFAULT_SOURCE_DETECT_MIN_SIZE <= content_length:
            return self.RESPONSE_INDEX

        if self.DEFAULT_SOURCE_DETECT_MIN_SIZE <= body_length:
            return self.RESPONSE_INDEX

        return None
