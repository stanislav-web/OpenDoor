# -*- coding: utf-8 -*-

import unittest

from src.core.http.plugins.response.indexof import IndexofResponsePlugin

class DummyResponse(object):
    def __init__(self, status=200, headers=None, body=b''):
        self.status = status
        self.headers = headers or {}
        self.data = body


class TestIndexOfResponseExtra(unittest.TestCase):
    """Extra coverage for IndexofResponsePlugin."""

    def make_response(self, body, status=200, headers=None):
        """Build a simple response object."""

        if isinstance(body, str):
            body = body.encode('utf-8')

        return DummyResponse(
            status=status,
            headers=headers or {'Content-Length': str(len(body))},
            body=body,
        )

    def test_process_returns_none_for_non_success_status(self):
        """IndexofResponsePlugin should skip non-200 style responses."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(
            "<html><title>Index of /</title></html>",
            status=403
        )

        self.assertIsNone(plugin.process(response))

    def test_process_returns_none_when_title_exists_but_is_not_indexof(self):
        """IndexofResponsePlugin should not match ordinary titles."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(
            """
            <html>
              <head><title>Admin panel</title></head>
              <body><h1>Welcome</h1></body>
            </html>
            """
        )

        self.assertIsNone(plugin.process(response))

    def test_process_matches_when_title_is_missing_but_body_has_directory_listing_markers(self):
        """IndexofResponsePlugin should detect body-level index listing markers even without a title."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(
            """
            <html>
              <body>
                <h1>Index of /backup/</h1>
                <pre>
                  <a href="../">../</a>
                  <a href="db.sql">db.sql</a>
                </pre>
              </body>
            </html>
            """
        )

        self.assertEqual(plugin.process(response), 'indexof')

    def test_process_does_not_match_partial_index_phrase_without_listing_context(self):
        """IndexofResponsePlugin should reject weak partial matches without directory-listing context."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(
            """
            <html>
              <head><title>Index optimization guide</title></head>
              <body>This page explains database indexes.</body>
            </html>
            """
        )

        self.assertIsNone(plugin.process(response))

    def test_process_matches_classic_indexof_title(self):
        """IndexofResponsePlugin should detect the classic title-based Apache/Nginx directory listing."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(
            """
            <html>
              <head><title>Index of /uploads/</title></head>
              <body>
                <h1>Index of /uploads/</h1>
                <a href="../">../</a>
              </body>
            </html>
            """
        )

        self.assertEqual(plugin.process(response), 'indexof')


if __name__ == '__main__':
    unittest.main()