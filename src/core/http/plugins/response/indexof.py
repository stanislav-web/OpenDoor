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

from .provider import ResponsePluginProvider


class IndexofResponsePlugin(ResponsePluginProvider):
    """Detect open directory listing pages across multiple server styles."""

    DESCRIPTION = 'IndexOf (detect directory listings across Apache/nginx/IIS/generic layouts)'
    RESPONSE_INDEX = 'indexof'
    DEFAULT_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]

    STRONG_TITLE_PATTERNS = (
        r'<title>\s*index of\s',
        r'<title>\s*directory listing for\s',
        r'<title>\s*directory listing --\s',
    )

    STRONG_BODY_PATTERNS = (
        r'index of /',
        r'directory listing for /',
        r'parent directory.*last modified.*size',
    )

    MEDIUM_PATTERNS = (
        r'parent directory',
        r'href=["\']\.\./?["\']',
        r'>\.\./?<',
        r'last modified',
        r'\bsize\b',
        r'\bdescription\b',
        r'<pre[^>]*>.*href=',
        r'<table[^>]*>.*href=',
    )

    DENY_PATTERNS = (
        r'type=["\']password["\']',
        r'access denied',
        r'unauthorized',
        r'forbidden',
        r'sign in',
        r'log in',
    )

    LINK_PATTERN = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
    LINK_SKIP_PREFIXES = ('#', '?', 'javascript:', 'mailto:')

    def __init__(self, void):
        """
        ResponsePluginProvider constructor
        """

        ResponsePluginProvider.__init__(self)

    @staticmethod
    def _count_matches(patterns, body):
        """
        Count how many patterns are present in the body.

        :param tuple patterns: regex patterns
        :param str body: normalized body
        :return: int
        """

        hits = 0
        for pattern in patterns:
            if re.search(pattern, body, re.IGNORECASE | re.DOTALL):
                hits += 1
        return hits

    def _count_listing_links(self, body):
        """
        Count candidate file/directory links.

        :param str body: normalized body
        :return: int
        """

        links = []
        for match in self.LINK_PATTERN.findall(body):
            link = str(match).strip().lower()

            if len(link) <= 0:
                continue
            if link.startswith(self.LINK_SKIP_PREFIXES):
                continue
            if link.startswith('http://') or link.startswith('https://'):
                continue
            if link.startswith('/logout') or link.startswith('/login'):
                continue

            links.append(link)

        return len(set(links))

    def process(self, response):
        """
        Process data.

        :param response: HTTP response
        :return: str | None
        """

        if response.status not in self.DEFAULT_STATUSES:
            return None

        super().process(response)

        if len(self._body) <= 0:
            return None

        body = self._body.lower()

        if self._count_matches(self.DENY_PATTERNS, body) > 0:
            return None

        title_hits = self._count_matches(self.STRONG_TITLE_PATTERNS, body)
        strong_body_hits = self._count_matches(self.STRONG_BODY_PATTERNS, body)
        medium_hits = self._count_matches(self.MEDIUM_PATTERNS, body)
        listing_links = self._count_listing_links(body)

        if title_hits > 0:
            if strong_body_hits > 0 or medium_hits >= 1 or listing_links >= 2:
                return self.RESPONSE_INDEX

        if strong_body_hits > 0 and (medium_hits >= 1 or listing_links >= 2):
            return self.RESPONSE_INDEX

        if medium_hits >= 3 and listing_links >= 2:
            return self.RESPONSE_INDEX

        return None