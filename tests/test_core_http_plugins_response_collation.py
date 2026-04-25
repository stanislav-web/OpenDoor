# -*- coding: utf-8 -*-

import unittest

from src.core.http.plugins.response.collation import CollationResponsePlugin


class FakeResponse(object):
    """Fake HTTP response object for response plugins."""

    def __init__(self, status=200, body='', headers=None):
        self.status = status
        self.body = body
        self.data = body.encode('utf-8')
        self.headers = headers or {}


class TestCollationResponsePlugin(unittest.TestCase):
    """Coverage and regression tests for CollationResponsePlugin."""

    def make_plugin(self):
        return CollationResponsePlugin(None)

    def test_detects_explicit_html_soft404(self):
        """Should fail explicit HTML soft404 pages."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html><head><title>Page Not Found</title></head>'
            '<body><h1>Page Not Found</h1>'
            '<p>The requested URL was not found on this server.</p>'
            '</body></html>'
        )

        self.assertEqual(plugin.process(response), 'failed')

    def test_detects_explicit_json_soft404(self):
        """Should fail explicit JSON soft404 payloads."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '{"detail":"Not Found"}',
            {'Content-Type': 'application/json'}
        )

        self.assertEqual(plugin.process(response), 'failed')

    def test_does_not_fail_article_that_mentions_not_found(self):
        """Should not fail normal articles that mention not found errors."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html><head><title>How to fix not found errors</title></head>'
            '<body><article>'
            '<h1>How to fix not found errors in your app</h1>'
            '<p>This guide explains why users may see not found messages.</p>'
            '</article></body></html>'
        )

        self.assertIsNone(plugin.process(response))

    def test_does_not_fail_login_page(self):
        """Should not fail login pages."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html><head><title>Sign in</title></head>'
            '<body><form><input type="password" name="password"></form></body></html>'
        )

        self.assertIsNone(plugin.process(response))

    def test_does_not_fail_directory_listing(self):
        """Should not fail open directory listing pages."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '<html><head><title>Index of /backup/</title></head>'
            '<body><a href="../">Parent Directory</a>'
            '<pre><a href="dump.sql">dump.sql</a> Last modified Size</pre>'
            '</body></html>'
        )

        self.assertIsNone(plugin.process(response))

    def test_does_not_fail_normal_json_success_payload(self):
        """Should not fail regular JSON success responses."""

        plugin = self.make_plugin()
        response = FakeResponse(
            200,
            '{"status":"ok","result":{"id":1}}',
            {'Content-Type': 'application/json'}
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_non_default_status(self):
        """Should ignore statuses outside the default response set."""

        plugin = self.make_plugin()
        response = FakeResponse(
            404,
            '{"detail":"Not Found"}',
            {'Content-Type': 'application/json'}
        )

        self.assertIsNone(plugin.process(response))

    def test_detects_repeated_non_explicit_template_on_third_hit(self):
        """Should fail a repeated non-explicit template on the third hit."""

        plugin = self.make_plugin()

        response1 = FakeResponse(
            200,
            '<html><head><title>Oops</title></head>'
            '<body><div class="error-box">Resource unavailable</div>'
            '<p>https://short.example/111111</p>'
            '</body></html>'
        )
        response2 = FakeResponse(
            200,
            '<html><head><title>Oops</title></head>'
            '<body><div class="error-box">Resource unavailable</div>'
            '<p>https://very-long-example-hostname.example.com/path/to/resource/222222/alpha/beta/gamma</p>'
            '</body></html>'
        )
        response3 = FakeResponse(
            200,
            '<html><head><title>Oops</title></head>'
            '<body><div class="error-box">Resource unavailable</div>'
            '<p>https://another-very-long-example-hostname.example.com/path/to/resource/333333/alpha/beta/gamma/delta</p>'
            '</body></html>'
        )

        self.assertIsNone(plugin.process(response1))
        self.assertIsNone(plugin.process(response2))
        self.assertEqual(plugin.process(response3), 'failed')