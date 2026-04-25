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

import re
from difflib import SequenceMatcher

from .provider import ResponsePluginProvider


class CollationResponsePlugin(ResponsePluginProvider):
    """Soft404-like response collation plugin with backward-compatible heuristics."""

    DESCRIPTION = 'Collation (detect repeated soft404/error templates)'
    RESPONSE_INDEX = 'failed'
    RESPONSE_FAILED = RESPONSE_INDEX
    DEFAULT_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]

    MIN_CONTENT_LENGTH = 100
    RATIO_THRESHOLD = 0.95

    EXPLICIT_HTML_PATTERNS = (
        r'<title>\s*404\s+not\s+found',
        r'<title>\s*page\s+not\s+found',
        r'<title>\s*not\s+found',
        r'page not found',
        r'requested url was not found',
        r'the requested url was not found',
        r'route not found',
        r'no such file or directory',
        r'cannot find the page',
    )

    EXPLICIT_JSON_PATTERNS = (
        r'"detail"\s*:\s*"not found"',
        r'"message"\s*:\s*"not found"',
        r'"error"\s*:\s*"not found"',
    )

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
    )

    UUID_RE = re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.IGNORECASE)
    LONG_HEX_RE = re.compile(r'\b[0-9a-f]{16,}\b', re.IGNORECASE)
    LONG_NUM_RE = re.compile(r'\b\d{5,}\b')
    URL_RE = re.compile(r'https?://[^\s"\']+', re.IGNORECASE)
    MULTISPACE_RE = re.compile(r'\s+')
    TITLE_RE = re.compile(r'<title>(.+?)</title>', re.IGNORECASE | re.DOTALL)

    TEMPLATE_THRESHOLD = 3
    BODY_SAMPLE_SIZE = 512

    def __init__(self, void):
        """
        ResponsePluginProvider constructor.
        """

        ResponsePluginProvider.__init__(self)
        self.previous_item = {}
        self.current_item = {}
        self._signatures = {}

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

    def _extract_title(self, body):
        """
        Extract normalized HTML title.

        :param str body: response body
        :return: str
        """

        title = self.TITLE_RE.search(body)
        if title is None:
            return ''

        return self.MULTISPACE_RE.sub(' ', title.group(1).strip().lower())

    def _normalize_template(self, body):
        """
        Normalize dynamic values out of the body to compare error templates.

        :param str body: response body
        :return: str
        """

        normalized = body.lower()
        normalized = self.URL_RE.sub(' URL ', normalized)
        normalized = self.UUID_RE.sub(' UUID ', normalized)
        normalized = self.LONG_HEX_RE.sub(' HEX ', normalized)
        normalized = self.LONG_NUM_RE.sub(' NUM ', normalized)
        normalized = self.MULTISPACE_RE.sub(' ', normalized).strip()

        if len(normalized) > self.BODY_SAMPLE_SIZE:
            normalized = normalized[:self.BODY_SAMPLE_SIZE]

        return normalized

    def _build_signature(self, response, body):
        """
        Build a normalized signature for repeated template detection.

        :param response: HTTP response
        :param str body: response body
        :return: tuple
        """

        headers = getattr(response, 'headers', {}) or {}
        content_type = str(headers.get('Content-Type', headers.get('content-type', ''))).lower()
        location = str(headers.get('Location', headers.get('location', ''))).lower()

        return (
            int(getattr(response, 'status', 0)),
            self._extract_title(body),
            content_type,
            location,
            self._normalize_template(body),
        )

    def _is_explicit_soft404(self, body):
        """
        Check explicit soft404 phrases in HTML or JSON responses.

        :param str body: response body
        :return: bool
        """

        body_lower = body.lower()

        if self._contains_any(self.LOGIN_PATTERNS, body_lower):
            return False

        if self._contains_any(self.DIRECTORY_LISTING_PATTERNS, body_lower):
            return False

        if self._contains_any(self.EXPLICIT_JSON_PATTERNS, body_lower):
            return True

        if self._contains_any(self.EXPLICIT_HTML_PATTERNS, body_lower):
            return True

        return False

    def _is_excluded_from_collation(self, body):
        """
        Skip bodies that should not participate in collation matching.

        :param str body: response body
        :return: bool
        """

        body_lower = body.lower()

        if self._contains_any(self.LOGIN_PATTERNS, body_lower):
            return True

        if self._contains_any(self.DIRECTORY_LISTING_PATTERNS, body_lower):
            return True

        return False

    def _extract_length(self, response):
        """
        Resolve effective response length using Content-Length when present.

        :param response: HTTP response
        :return: int
        """

        headers = getattr(response, 'headers', {}) or {}
        raw_length = headers.get('Content-Length', headers.get('content-length'))

        if raw_length is not None:
            try:
                return int(raw_length)
            except Exception:
                return len(self._body)

        return len(self._body)

    def _make_item(self, response):
        """
        Build legacy comparison item.

        :param response: HTTP response
        :return: dict
        """

        return {
            'length': self._extract_length(response),
            'text': self._body,
        }

    def _ratio_match(self, first_body, second_body):
        """
        Compare body similarity.

        :param str first_body: first body
        :param str second_body: second body
        :return: bool
        """

        return SequenceMatcher(None, first_body, second_body).ratio() >= self.RATIO_THRESHOLD

    def _legacy_match(self, first_item, second_item):
        """
        Backward-compatible legacy false-positive matching.

        :param dict first_item: first item
        :param dict second_item: second item
        :return: bool
        """

        if not first_item or not second_item:
            return False

        if first_item.get('length') == second_item.get('length'):
            return True

        return self._ratio_match(first_item.get('text', ''), second_item.get('text', ''))

    def process(self, response):
        """
        Process response and detect repeated soft404/error templates.

        :param response: HTTP response
        :return: str | None
        """

        if response.status not in self.DEFAULT_STATUSES:
            return None

        super().process(response)

        if len(self._body) <= 0:
            return None

        if self._is_excluded_from_collation(self._body):
            return None

        if self._is_explicit_soft404(self._body):
            return self.RESPONSE_FAILED

        current_item = self._make_item(response)

        if current_item['length'] <= 0:
            return None

        if current_item['length'] < self.MIN_CONTENT_LENGTH:
            return None

        signature = self._build_signature(response, self._body)
        self._signatures[signature] = self._signatures.get(signature, 0) + 1

        if self.previous_item == {}:
            self.previous_item = current_item
            return None

        if self._legacy_match(self.previous_item, current_item):
            return self.RESPONSE_FAILED

        if self.current_item != {} and self._legacy_match(self.current_item, current_item):
            return self.RESPONSE_FAILED

        if self._signatures[signature] >= self.TEMPLATE_THRESHOLD:
            return self.RESPONSE_FAILED

        if self.current_item == {}:
            self.current_item = current_item
            return None

        self.previous_item = self.current_item
        self.current_item = current_item
        return None