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

import json
import re

from .provider import ResponsePluginProvider


class SkipemptyResponsePlugin(ResponsePluginProvider):
    """Skip only truly empty or semantically empty short success pages."""

    DESCRIPTION = 'SkipEmpty (skip empty success pages)'
    RESPONSE_INDEX = 'skip'
    DEFAULT_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    DEFAULT_RECON_TO_SKIP_EMPTY_PAGE = 500

    LOGIN_PATTERNS = (
        r'type=["\']password["\']',
        r'\bsign in\b',
        r'\blog in\b',
        r'\bauthentication required\b',
    )

    DIRECTORY_LISTING_PATTERNS = (
        r'<title>\s*index of\s',
        r'parent directory',
        r'last modified',
        r'<pre[^>]*>.*href=',
        r'<table[^>]*>.*href=',
    )

    BINARY_CONTENT_TYPES = (
        'application/octet-stream',
        'application/zip',
        'application/x-zip-compressed',
        'application/gzip',
        'application/x-gzip',
        'application/pdf',
        'application/x-sqlite3',
        'application/vnd.sqlite3',
        'image/',
        'audio/',
        'video/',
    )

    TEXTUAL_JSON_TYPES = (
        'application/json',
        'application/problem+json',
        'text/json',
    )

    TAG_RE = re.compile(r'<[^>]+>')
    MULTISPACE_RE = re.compile(r'\s+')

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

    @staticmethod
    def _contains_any(patterns, value):
        """
        Check whether any regex pattern exists in the given text.

        :param tuple patterns: regex patterns
        :param str value: input text
        :return: bool
        """

        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                return True
        return False

    def _is_binary_content_type(self, content_type):
        """
        Determine whether a Content-Type looks like a real binary/file response.

        :param str content_type: normalized content type
        :return: bool
        """

        if len(content_type) <= 0:
            return False

        for item in self.BINARY_CONTENT_TYPES:
            if content_type.startswith(item):
                return True

        return False

    def _is_meaningful_json(self, body):
        """
        Detect whether JSON payload contains useful data and should not be skipped.

        :param str body: response body
        :return: bool
        """

        try:
            data = json.loads(body)
        except Exception:
            return False

        if data is None:
            return False

        if data == {} or data == [] or data == '':
            return False

        if isinstance(data, dict):
            return len(data) > 0

        if isinstance(data, list):
            return len(data) > 0

        return True

    def _extract_visible_text(self, body):
        """
        Strip HTML tags and normalize whitespace.

        :param str body: response body
        :return: str
        """

        text = self.TAG_RE.sub(' ', body)
        text = self.MULTISPACE_RE.sub(' ', text).strip()
        return text

    def process(self, response):
        """
        Process data.

        :param response: HTTP response
        :return: str | None
        """

        if response.status not in self.DEFAULT_STATUSES:
            return None

        super().process(response)

        content_length = self._extract_content_length()
        body_length = len(self._body)
        content_type = self._extract_content_type()
        content_disposition = str(self._get_header('Content-Disposition') or '').lower()
        body_lower = self._body.lower()

        if content_length is not None:
            if self.DEFAULT_RECON_TO_SKIP_EMPTY_PAGE < content_length:
                return None
        elif self.DEFAULT_RECON_TO_SKIP_EMPTY_PAGE < body_length:
            return None

        if 'attachment' in content_disposition:
            return None

        if self._is_binary_content_type(content_type):
            return None

        if self._contains_any(self.LOGIN_PATTERNS, body_lower):
            return None

        if self._contains_any(self.DIRECTORY_LISTING_PATTERNS, body_lower):
            return None

        if content_type in self.TEXTUAL_JSON_TYPES and self._is_meaningful_json(self._body):
            return None

        visible_text = self._extract_visible_text(self._body)

        if len(visible_text) <= 0:
            return self.RESPONSE_INDEX

        if len(visible_text) <= 20:
            return self.RESPONSE_INDEX

        return None