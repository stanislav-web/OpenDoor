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

    Development Team: Brain Storm Team
"""

from .provider import ResponsePluginProvider


class FileResponsePlugin(ResponsePluginProvider):
    """Detect large files and explicit download/binary responses."""

    DESCRIPTION = 'File (detect large files and explicit downloads)'
    RESPONSE_INDEX = 'file'
    DEFAULT_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    DEFAULT_SOURCE_DETECT_MIN_SIZE = 1000000

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
        'image/svg+xml',
    )

    def __init__(self, void):
        """
        ResponsePluginProvider constructor.
        """

        ResponsePluginProvider.__init__(self)

    def _get_header(self, name):
        """
        Return a header value using case-insensitive lookup.

        :param str name: header name
        :return: str | None
        """

        if name in self._headers:
            return self._headers[name]

        target = str(name).lower()
        for key, value in self._headers.items():
            if str(key).lower() == target:
                return value

        return None

    def _extract_content_length(self):
        """
        Extract Content-Length as int if possible.

        :return: int | None
        """

        raw_length = self._get_header('Content-Length')
        if raw_length is None:
            return None

        try:
            return int(raw_length)
        except Exception:
            return None

    def _extract_content_type(self):
        """
        Extract normalized Content-Type without parameters.

        :return: str
        """

        value = self._get_header('Content-Type')
        if value is None:
            return ''

        return str(value).split(';', 1)[0].strip().lower()

    def _is_binary_content_type(self, content_type):
        """
        Determine whether a Content-Type looks like a real file/binary response.

        :param str content_type: normalized content type
        :return: bool
        """

        if len(content_type) <= 0:
            return False

        for item in self.TEXTUAL_CONTENT_TYPES:
            if content_type == item:
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

        if content_length is not None and self.DEFAULT_SOURCE_DETECT_MIN_SIZE <= content_length:
            return self.RESPONSE_INDEX

        if self.DEFAULT_SOURCE_DETECT_MIN_SIZE <= body_length:
            return self.RESPONSE_INDEX

        has_content = (content_length is not None and 0 < content_length) or 0 < body_length

        if 'attachment' in content_disposition and has_content:
            return self.RESPONSE_INDEX

        if self._is_binary_content_type(content_type) and has_content:
            return self.RESPONSE_INDEX

        return None