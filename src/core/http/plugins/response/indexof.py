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


class IndexofResponsePlugin(ResponsePluginProvider):
    """Detect open directory listing pages across multiple server styles."""

    DESCRIPTION = 'IndexOf (detect directory listings across Apache/nginx/IIS/generic layouts)'
    RESPONSE_INDEX = 'indexof'
    DEFAULT_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]

    STRONG_TITLE_PATTERNS = (
        r'<title>\s*index\s+of\s+/?[^<]*</title>',
        r'<title>\s*directory\s+listing\s+for\s+/?[^<]*</title>',
        r'<title>\s*directory\s+listing\s+--\s+/?[^<]*</title>',
    )

    STRONG_BODY_PATTERNS = (
        r'<h1[^>]*>\s*index\s+of\s+/?[^<]*</h1>',
        r'<h1[^>]*>\s*directory\s+listing\s+for\s+/?[^<]*</h1>',
        r'<h1[^>]*>\s*directory\s+listing\s+--\s+/?[^<]*</h1>',
    )

    PARENT_DIRECTORY_PATTERNS = (
        r'>\s*parent\s+directory\s*</a>',
        r'href=["\']\.\./?["\'][^>]*>\s*\.\./?\s*</a>',
    )

    APACHE_SORT_PATTERNS = (
        r'href=["\']\?C=(?:N|M|S|D);O=(?:A|D)["\']',
    )

    AUTO_INDEX_LAYOUT_PATTERNS = (
        r'/icons/(?:blank|back|folder|unknown|text)\.gif',
        r'<pre[^>]*>.*?</pre>',
        r'<table[^>]*>.*?</table>',
    )

    LISTING_HEADER_PATTERNS = (
        r'>\s*name\s*</a>',
        r'>\s*last\s+modified\s*</a>',
        r'>\s*size\s*</a>',
        r'>\s*description\s*</a>',
        r'>\s*last\s+modified\s*<',
        r'>\s*size\s*<',
    )

    PATH_HEADING_PATTERNS = (
        r'<title>\s*index\s+of\s+/[^<]*</title>',
        r'<h1[^>]*>\s*index\s+of\s+/[^<]*</h1>',
        r'<title>\s*directory\s+listing\s+(?:for|--)\s+/?[^<]*</title>',
        r'<h1[^>]*>\s*directory\s+listing\s+(?:for|--)\s+/?[^<]*</h1>',
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
    LINK_SKIP_PREFIXES = ('#', '?', '/', '//', 'javascript:', 'mailto:', 'tel:', 'data:')

    def __init__(self, void):
        """
        ResponsePluginProvider constructor.
        """

        ResponsePluginProvider.__init__(self)

    @staticmethod
    def _count_matches(patterns, body):
        """
        Count how many patterns are present in the body.

        :param tuple patterns: regex patterns
        :param str body: normalized body
        :return: count of matched patterns
        :rtype: int
        """

        hits = 0
        for pattern in patterns:
            if re.search(pattern, body, re.IGNORECASE | re.DOTALL):
                hits += 1
        return hits

    def _count_listing_links(self, body):
        """
        Count candidate file/directory links from server-generated listings.

        Normal website navigation usually uses absolute paths, query strings,
        anchors, JavaScript links, or full URLs. Real autoindex pages usually
        expose plain relative entries like file.txt, client.php, folder/.

        :param str body: normalized body
        :return: number of unique candidate listing links
        :rtype: int
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
            if '?' in link or '#' in link:
                continue
            if link in ('.', './', '..', '../'):
                continue
            if link.startswith('logout') or link.startswith('login'):
                continue

            links.append(link)

        return len(set(links))

    def _is_directory_listing(self, body):
        """
        Check if response body looks like a real directory listing.

        :param str body: normalized body
        :return: True if body contains directory listing structure
        :rtype: bool
        """

        title_hits = self._count_matches(self.STRONG_TITLE_PATTERNS, body)
        strong_body_hits = self._count_matches(self.STRONG_BODY_PATTERNS, body)
        parent_hits = self._count_matches(self.PARENT_DIRECTORY_PATTERNS, body)
        apache_sort_hits = self._count_matches(self.APACHE_SORT_PATTERNS, body)
        layout_hits = self._count_matches(self.AUTO_INDEX_LAYOUT_PATTERNS, body)
        header_hits = self._count_matches(self.LISTING_HEADER_PATTERNS, body)
        listing_links = self._count_listing_links(body)
        path_heading_hits = self._count_matches(self.PATH_HEADING_PATTERNS, body)

        if title_hits > 0 and strong_body_hits > 0:
            if parent_hits > 0 or apache_sort_hits > 0:
                return True
            if layout_hits > 0 and listing_links >= 1:
                return True
            if header_hits >= 2 and listing_links >= 1:
                return True
            if path_heading_hits >= 2 and listing_links >= 1:
                return True

        if title_hits > 0 and parent_hits > 0:
            return True

        if title_hits > 0 and apache_sort_hits > 0:
            return True

        if title_hits > 0 and layout_hits > 0 and listing_links >= 1:
            return True

        if strong_body_hits > 0 and parent_hits > 0:
            return True

        if parent_hits > 0 and apache_sort_hits > 0:
            return True

        if parent_hits > 0 and header_hits >= 2 and listing_links >= 1:
            return True

        if apache_sort_hits > 0 and header_hits >= 2 and listing_links >= 1:
            return True

        return False

    def process(self, response):
        """
        Process data.

        :param response: HTTP response
        :return: response index or None
        :rtype: str | None
        """

        if response.status not in self.DEFAULT_STATUSES:
            return None

        super().process(response)

        if len(self._body) <= 0:
            return None

        body = self._body.lower()

        if self._count_matches(self.DENY_PATTERNS, body) > 0:
            return None

        if self._is_directory_listing(body):
            return self.RESPONSE_INDEX

        return None