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

import re

from src.core import helper


class ResponsePluginProvider(object):
    """"ResponsePluginProvider class"""

    def __init__(self):
        """
        PluginProvider constructor
        """
        self._status = 0
        self._headers = {}
        self._body = ''

    def __set_body(self, body):
        """
        Set response data
        :param str body: response data
        :return: None
        """

        if False is isinstance(body, str):
            self._body = helper.decode(body)

    def _get_header(self, name):
        """
        Return a response header value using case-insensitive lookup.

        :param str name: Header name.
        :return: Header value or None.
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

        :return: Parsed content length or None.
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

        :return: Normalized content type.
        :rtype: str
        """

        value = self._get_header('Content-Type')
        if value is None:
            return ''

        return str(value).split(';', 1)[0].strip().lower()

    @staticmethod
    def _contains_any(patterns, value):
        """
        Check whether any regex pattern exists in the given text.

        :param tuple patterns: Regex patterns.
        :param str value: Input text.
        :return: True when any pattern matches.
        """

        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                return True
        return False

    @classmethod
    def _is_response_status_in(cls, response, statuses):
        """
        Return True when response.status is in the allowed status set.

        :param response: HTTP response-like object.
        :param tuple statuses: Allowed integer statuses.
        :return: True when response status is allowed.
        :rtype: bool
        """

        try:
            return int(getattr(response, 'status', 0)) in statuses
        except (TypeError, ValueError):
            return False

    @classmethod
    def _get_response_header(cls, response, name):
        """
        Return a response header value using case-insensitive lookup.

        :param response: HTTP response-like object.
        :param str name: Header name.
        :return: Header value or None.
        """

        headers = getattr(response, 'headers', {}) or {}
        if name in headers:
            return headers[name]

        target = str(name).lower()
        for key, value in getattr(headers, 'items', lambda: [])():
            if str(key).lower() == target:
                return value

        return None

    @classmethod
    def _extract_response_content_type(cls, response):
        """
        Extract normalized response Content-Type without parameters.

        :param response: HTTP response-like object.
        :return: Normalized content type.
        :rtype: str
        """

        value = cls._get_response_header(response, 'Content-Type')
        if value is None:
            return ''

        return str(value).split(';', 1)[0].strip().lower()

    @classmethod
    def _extract_response_body(cls, response, max_body_bytes):
        """
        Decode a bounded response body.

        :param response: HTTP response-like object.
        :param int max_body_bytes: Maximum number of source bytes or chars to decode.
        :return: Decoded bounded body.
        :rtype: str
        """

        data = getattr(response, 'data', b'')
        if data is None:
            return ''

        if isinstance(data, bytes):
            data = data[:max_body_bytes]
            return helper.decode(data, errors='ignore')

        return str(data)[:max_body_bytes]

    def process(self, response):
        """
        Process data from the given response object.
        :param urllib3.response.HTTPResponse response: The response object containing the data to be processed.
        :return: A string representing the processed data.
        """

        self._status = int(float(response.status))
        self._headers = response.headers
        self.__set_body(response.data)

