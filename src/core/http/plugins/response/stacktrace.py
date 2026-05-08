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

from .provider import ResponsePluginProvider


class StacktraceResponsePlugin(ResponsePluginProvider):
    """Detect exposed stack traces and debug error details."""

    DESCRIPTION = 'Stacktrace (detect exposed debug stack traces and internal error details)'
    RESPONSE_INDEX = 'debug'

    TEXTUAL_CONTENT_TYPES = (
        '',
        'text/html',
        'text/plain',
        'text/json',
        'application/json',
        'application/problem+json',
        'application/xml',
        'text/xml',
        'application/xhtml+xml',
    )
    BINARY_CONTENT_TYPES = (
        'application/octet-stream',
        'application/zip',
        'application/x-zip-compressed',
        'application/gzip',
        'application/x-gzip',
        'application/pdf',
        'image/',
        'audio/',
        'video/',
    )
    SIGNALS = (
        {
            'runtime': 'python',
            'signal': 'python-traceback',
            'confidence': 95,
            'pattern': re.compile(r'Traceback \(most recent call last\)', re.IGNORECASE),
        },
        {
            'runtime': 'node',
            'signal': 'node-anonymous-stack-frame',
            'confidence': 90,
            'pattern': re.compile(r'at\s+Object\.<anonymous>.+?\.js:\d+:\d+', re.IGNORECASE | re.DOTALL),
        },
        {
            'runtime': 'node',
            'signal': 'node-stack-frame',
            'confidence': 90,
            'pattern': re.compile(r'at\s+.+?\.js:\d+:\d+', re.IGNORECASE | re.DOTALL),
        },
        {
            'runtime': 'nestjs',
            'signal': 'nestjs-error',
            'confidence': 85,
            'pattern': re.compile(r'(NestJS|\[Nest\]).{0,240}(Error:|Exception)', re.IGNORECASE | re.DOTALL),
        },
        {
            'runtime': 'php',
            'signal': 'php-error',
            'confidence': 90,
            'pattern': re.compile(r'PHP\s+(Fatal\s+error|Warning|Parse\s+error|Notice)', re.IGNORECASE),
        },
        {
            'runtime': 'java',
            'signal': 'java-exception',
            'confidence': 90,
            'pattern': re.compile(r'java\.lang\.[A-Za-z0-9_.$]+Exception', re.IGNORECASE),
        },
        {
            'runtime': 'sql',
            'signal': 'sqlstate-error',
            'confidence': 85,
            'pattern': re.compile(r'SQLSTATE\[[A-Z0-9]+\]', re.IGNORECASE),
        },
        {
            'runtime': 'oracle',
            'signal': 'oracle-error',
            'confidence': 85,
            'pattern': re.compile(r'\bORA-\d{5}\b', re.IGNORECASE),
        },
    )

    def __init__(self, void):
        """
        ResponsePluginProvider constructor.

        :param void: unused plugin value
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

    def _extract_content_type(self):
        """
        Extract normalized Content-Type without parameters.

        :return: normalized content type
        :rtype: str
        """

        value = self._get_header('Content-Type')
        if value is None:
            return ''

        return str(value).split(';', 1)[0].strip().lower()

    def _is_textual_response(self):
        """
        Decide whether the response body is safe and useful for text scanning.

        :return: True when response content type can contain text stack traces
        :rtype: bool
        """

        content_type = self._extract_content_type()

        for item in self.BINARY_CONTENT_TYPES:
            if content_type.startswith(item):
                return False

        if content_type in self.TEXTUAL_CONTENT_TYPES:
            return True

        if content_type.endswith('+json') or content_type.endswith('+xml'):
            return True

        return False

    @staticmethod
    def _build_detection(signal):
        """
        Build stacktrace debug detection metadata.

        :param dict signal: matched signal definition
        :return: debug detection metadata
        :rtype: dict
        """

        return {
            'type': 'stacktrace',
            'runtime': signal.get('runtime'),
            'signal': signal.get('signal'),
            'confidence': int(signal.get('confidence', 0)),
        }

    def process(self, response):
        """
        Process data.

        :param response: HTTP response
        :return: str | None
        """

        if not hasattr(response, 'status'):
            return None

        super().process(response)

        if len(self._body) <= 0:
            return None

        if self._is_textual_response() is False:
            return None

        for signal in self.SIGNALS:
            if signal.get('pattern').search(self._body):
                setattr(response, 'opendoor_debug_detection', self._build_detection(signal))
                return self.RESPONSE_INDEX

        return None
