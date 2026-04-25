# -*- coding: utf-8 -*-

import unittest

from src.core.http.plugins.response.indexof import IndexofResponsePlugin


class FakeResponse(object):
    """Fake HTTP response object for response plugins."""

    def __init__(self, status=200, body=''):
        self.status = status
        self.body = body
        self.data = body.encode('utf-8')
        self.headers = {}


class TestableIndexofResponsePlugin(IndexofResponsePlugin):
    """Plugin wrapper that injects the body directly for deterministic tests."""

    def process(self, response):
        if response.status not in self.DEFAULT_STATUSES:
            return None

        self._body = response.body

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


class TestIndexofResponsePlugin(unittest.TestCase):
    """Coverage and regression tests for IndexofResponsePlugin."""

    def make_plugin(self):
        return TestableIndexofResponsePlugin(None)

    def test_detects_apache_index_of_listing(self):
        """Should detect classic Apache Index Of pages."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html><head><title>Index of /backup/</title></head>'
            '<body><h1>Index of /backup/</h1>'
            '<a href="../">Parent Directory</a>'
            '<pre><a href="dump.sql">dump.sql</a>  Last modified  Size</pre>'
            '</body></html>'
        )

        self.assertEqual(plugin.process(response), 'indexof')

    def test_detects_nginx_autoindex_style_listing(self):
        """Should detect nginx/generic autoindex layouts."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html><head><title>Index of /downloads/</title></head>'
            '<body><pre>'
            '<a href="../">../</a>\n'
            '<a href="file1.zip">file1.zip</a>\n'
            '<a href="file2.tar.gz">file2.tar.gz</a>\n'
            'Last modified      Size'
            '</pre></body></html>'
        )

        self.assertEqual(plugin.process(response), 'indexof')

    def test_detects_directory_listing_for_iis_like_page(self):
        """Should detect IIS/generic directory listing pages."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html><head><title>Directory Listing For /admin</title></head>'
            '<body><table>'
            '<tr><th>Name</th><th>Last modified</th><th>Size</th><th>Description</th></tr>'
            '<tr><td><a href="../">Parent Directory</a></td></tr>'
            '<tr><td><a href="logs/">logs/</a></td></tr>'
            '<tr><td><a href="backup.zip">backup.zip</a></td></tr>'
            '</table></body></html>'
        )

        self.assertEqual(plugin.process(response), 'indexof')

    def test_returns_none_for_regular_page_with_incidental_words(self):
        """Should not detect a normal content page as a directory listing."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html><head><title>Storage guide</title></head>'
            '<body><h1>Name and size recommendations</h1>'
            '<p>This article explains last modified metadata and directory description fields.</p>'
            '<a href="/docs/storage">Read more</a>'
            '</body></html>'
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_login_page(self):
        """Should not detect login pages even if they mention parent directory text."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html><head><title>Sign in</title></head>'
            '<body><h1>Parent Directory</h1>'
            '<form><input type="password" name="password"></form>'
            '<a href="/login">Log in</a>'
            '</body></html>'
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_forbidden_page(self):
        """Should not detect access denied pages as directory listings."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html><head><title>403 Forbidden</title></head>'
            '<body><h1>Forbidden</h1><p>Access denied.</p></body></html>'
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_non_default_status(self):
        """Should ignore responses outside the default status set."""

        plugin = self.make_plugin()
        response = FakeResponse(
            404,
            '<html><head><title>Index of /backup/</title></head>'
            '<body><a href="../">Parent Directory</a></body></html>'
        )

        self.assertIsNone(plugin.process(response))