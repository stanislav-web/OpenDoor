# -*- coding: utf-8 -*-

import re
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
        """
        Process fake response without depending on provider body extraction.

        :param FakeResponse response: fake HTTP response
        :return: response index or None
        :rtype: str | None
        """

        if response.status not in self.DEFAULT_STATUSES:
            return None

        self._body = response.body

        if len(self._body) <= 0:
            return None

        body = self._body.lower()

        if self._count_matches(self.DENY_PATTERNS, body) > 0:
            return None

        if self._is_directory_listing(body):
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

    def test_detects_apache_table_index_of_listing(self):
        """Should detect classic Apache table based autoindex pages."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">'
            '<html>'
            '<head><title>Index of /soap</title></head>'
            '<body>'
            '<h1>Index of /soap</h1>'
            '<table>'
            '<tr>'
            '<th><a href="?C=N;O=D">Name</a></th>'
            '<th><a href="?C=M;O=A">Last modified</a></th>'
            '<th><a href="?C=S;O=A">Size</a></th>'
            '<th><a href="?C=D;O=A">Description</a></th>'
            '</tr>'
            '<tr>'
            '<td><a href="/">Parent Directory</a></td>'
            '</tr>'
            '<tr>'
            '<td><a href="client.php">client.php</a></td>'
            '</tr>'
            '<tr>'
            '<td><a href="service.wsdl">service.wsdl</a></td>'
            '</tr>'
            '</table>'
            '</body>'
            '</html>'
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

    def test_returns_none_for_regular_gallery_page_with_index_links(self):
        """Should not detect regular gallery pages with index.php links as directory listings."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<!DOCTYPE html>'
            '<html>'
            '<head>'
            '<title>City photo gallery - Example</title>'
            '<meta name="description" content="City photo gallery" />'
            '</head>'
            '<body>'
            '<!--noindex-->'
            '<a href="/index.php?wx=16">News</a>'
            '<a href="/index.php?wx=33">Weather</a>'
            '<a href="/index.php?wx=49">Terms of use</a>'
            '<table width="500" border="0" cellspacing="5" cellpadding="5">'
            '<tr>'
            '<td style="font-size: 10px;">'
            '<a href="photo.php?razdel=25">May gallery</a>'
            '<a href="photo.php?razdel=1">City anniversary</a>'
            '<a href="photo.php?razdel=17">Gallery section</a>'
            '<a href="add_image.php">Add photo</a>'
            '</td>'
            '</tr>'
            '</table>'
            '<!--/noindex-->'
            '</body>'
            '</html>'
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

    def test_count_listing_links_skips_empty_and_auth_links(self):
        """Should cover listing link skip branches for empty and auth links."""

        plugin = self.make_plugin()
        plugin.LINK_PATTERN = re.compile(r'href=["\']([^"\']*)["\']', re.IGNORECASE)

        body = (
            '<a href="">empty</a>'
            '<a href="logout.php">logout</a>'
            '<a href="login.php">login</a>'
            '<a href="file.txt">file.txt</a>'
        )

        self.assertEqual(plugin._count_listing_links(body), 1)

    def test_detects_title_with_apache_sort_links(self):
        """Should detect listing by title and Apache sort links."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html>'
            '<head><title>Index of /public/</title></head>'
            '<body>'
            '<table>'
            '<tr>'
            '<th><a href="?C=N;O=D">Name</a></th>'
            '</tr>'
            '</table>'
            '</body>'
            '</html>'
        )

        self.assertEqual(plugin.process(response), 'indexof')

    def test_detects_title_with_layout_and_relative_listing_link(self):
        """Should detect listing by title, autoindex layout, and relative entry."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html>'
            '<head><title>Index of /files/</title></head>'
            '<body>'
            '<pre>'
            '<a href="dump.sql">dump.sql</a>'
            '</pre>'
            '</body>'
            '</html>'
        )

        self.assertEqual(plugin.process(response), 'indexof')

    def test_detects_body_header_with_parent_directory_without_title(self):
        """Should detect listing by body Index Of header and parent directory."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html>'
            '<body>'
            '<h1>Index of /files/</h1>'
            '<a href="../">Parent Directory</a>'
            '</body>'
            '</html>'
        )

        self.assertEqual(plugin.process(response), 'indexof')

    def test_detects_parent_directory_with_apache_sort_without_title(self):
        """Should detect listing by parent directory and Apache sort links."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html>'
            '<body>'
            '<a href="../">Parent Directory</a>'
            '<a href="?C=N;O=D">Name</a>'
            '</body>'
            '</html>'
        )

        self.assertEqual(plugin.process(response), 'indexof')

    def test_detects_parent_directory_with_headers_and_listing_link(self):
        """Should detect listing by parent directory, headers, and relative entry."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html>'
            '<body>'
            '<a href="../">Parent Directory</a>'
            '<span>Last modified</span>'
            '<span>Size</span>'
            '<a href="backup.zip">backup.zip</a>'
            '</body>'
            '</html>'
        )

        self.assertEqual(plugin.process(response), 'indexof')

    def test_detects_apache_sort_with_headers_and_listing_link(self):
        """Should detect listing by Apache sort links, headers, and relative entry."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html>'
            '<body>'
            '<a href="?C=N;O=D">Name</a>'
            '<span>Last modified</span>'
            '<span>Size</span>'
            '<a href="backup.zip">backup.zip</a>'
            '</body>'
            '</html>'
        )

        self.assertEqual(plugin.process(response), 'indexof')

    def test_is_directory_listing_returns_false_for_incomplete_listing_markers(self):
        """Should return false when listing markers are incomplete."""

        plugin = self.make_plugin()
        body = (
            '<html>'
            '<body>'
            '<span>Last modified</span>'
            '<a href="backup.zip">backup.zip</a>'
            '</body>'
            '</html>'
        )

        self.assertFalse(plugin._is_directory_listing(body.lower()))

    def test_real_process_returns_none_for_denied_page(self):
        """Should cover deny branch in the real process implementation."""

        plugin = IndexofResponsePlugin(None)
        response = FakeResponse(
            200,
            '<html>'
            '<head><title>Index of /private/</title></head>'
            '<body>'
            '<p>Access denied</p>'
            '<a href="backup.zip">backup.zip</a>'
            '</body>'
            '</html>'
        )

        self.assertIsNone(plugin.process(response))
