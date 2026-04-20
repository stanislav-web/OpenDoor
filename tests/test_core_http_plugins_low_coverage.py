# -*- coding: utf-8 -*-

import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response.collation import CollationResponsePlugin
from src.core.http.plugins.response.indexof import IndexofResponsePlugin
from src.core.http.plugins.response.skipempty import SkipemptyResponsePlugin


class TestHttpResponsePluginsLowCoverage(unittest.TestCase):
    """TestHttpResponsePluginsLowCoverage class."""

    @staticmethod
    def make_response(status=200, body=b'', headers=None):
        """Create a simple HTTPResponse for plugin tests."""

        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_collation_returns_none_for_non_default_status(self):
        """CollationResponsePlugin should ignore unsupported statuses."""

        plugin = CollationResponsePlugin(None)
        response = self.make_response(status=404, body=b'A' * 200, headers={'Content-Length': '200'})

        self.assertIsNone(plugin.process(response))

    def test_collation_first_match_sets_previous_item(self):
        """CollationResponsePlugin should store the first eligible response for future comparison."""

        plugin = CollationResponsePlugin(None)
        response = self.make_response(status=200, body=b'A' * 120, headers={'Content-Length': '120'})

        self.assertIsNone(plugin.process(response))
        self.assertEqual(plugin.previous_item['length'], 120)
        self.assertEqual(plugin.previous_item['text'], 'A' * 120)

    def test_collation_identical_content_length_is_failed(self):
        """CollationResponsePlugin should mark identical eligible content length as failed."""

        plugin = CollationResponsePlugin(None)

        first = self.make_response(status=200, body=b'A' * 120, headers={'Content-Length': '120'})
        second = self.make_response(status=200, body=b'B' * 120, headers={'Content-Length': '120'})

        self.assertIsNone(plugin.process(first))
        self.assertEqual(plugin.process(second), plugin.RESPONSE_INDEX)

    def test_collation_ratio_above_threshold_is_failed(self):
        """CollationResponsePlugin should mark near-identical pages as failed based on ratio."""

        plugin = CollationResponsePlugin(None)

        first = self.make_response(status=200, body=b'A' * 120, headers={'Content-Length': '120'})
        second = self.make_response(status=200, body=b'A' * 121, headers={'Content-Length': '121'})

        self.assertIsNone(plugin.process(first))
        self.assertEqual(plugin.process(second), plugin.RESPONSE_INDEX)

    def test_collation_current_item_ratio_match_branch_is_failed(self):
        """CollationResponsePlugin should hit the current_item ratio equality branch."""

        plugin = CollationResponsePlugin(None)

        first = self.make_response(status=200, body=b'A' * 120, headers={'Content-Length': '120'})
        second = self.make_response(status=200, body=b'B' * 130, headers={'Content-Length': '130'})
        third = self.make_response(status=200, body=b'C' * 140, headers={'Content-Length': '140'})

        self.assertIsNone(plugin.process(first))
        self.assertIsNone(plugin.process(second))
        self.assertEqual(plugin.process(third), plugin.RESPONSE_INDEX)

    def test_collation_uses_body_length_when_content_length_header_is_missing(self):
        """CollationResponsePlugin should fall back to body length when Content-Length is absent."""

        plugin = CollationResponsePlugin(None)
        response = self.make_response(status=200, body=b'Z' * 120, headers={})

        self.assertIsNone(plugin.process(response))
        self.assertEqual(plugin.previous_item['length'], 120)

    def test_collation_ignores_short_pages(self):
        """CollationResponsePlugin should ignore pages below minimum content length."""

        plugin = CollationResponsePlugin(None)
        response = self.make_response(status=200, body=b'Short', headers={'Content-Length': '5'})

        self.assertIsNone(plugin.process(response))
        self.assertEqual(plugin.previous_item, {})
        self.assertEqual(plugin.current_item, {})

    def test_indexof_returns_none_for_non_default_status(self):
        """IndexofResponsePlugin should ignore unsupported statuses."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(status=404, body=b'<title>Index of /</title>')

        self.assertIsNone(plugin.process(response))

    def test_indexof_detects_index_of_title_case_insensitively(self):
        """IndexofResponsePlugin should detect Index Of title case-insensitively."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(status=200, body=b'<HTML><TITLE>index of /</TITLE></HTML>')

        self.assertEqual(plugin.process(response), plugin.RESPONSE_INDEX)

    def test_indexof_returns_none_when_body_is_empty(self):
        """IndexofResponsePlugin should return None for empty bodies."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(status=200, body=b'')

        self.assertIsNone(plugin.process(response))

    def test_indexof_returns_none_when_title_is_missing(self):
        """IndexofResponsePlugin should return None when title tag is missing."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(status=200, body=b'<html><body>No title here</body></html>')

        self.assertIsNone(plugin.process(response))

    def test_indexof_returns_none_when_title_does_not_match(self):
        """IndexofResponsePlugin should return None for non-index titles."""

        plugin = IndexofResponsePlugin(None)
        response = self.make_response(status=200, body=b'<title>Welcome</title>')

        self.assertIsNone(plugin.process(response))

    def test_skipempty_returns_none_for_non_default_status(self):
        """SkipemptyResponsePlugin should ignore unsupported statuses."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(status=404, body=b'a', headers={'Content-Length': '1'})

        self.assertIsNone(plugin.process(response))

    def test_skipempty_skips_when_content_length_header_is_small(self):
        """SkipemptyResponsePlugin should skip when Content-Length is at or below threshold."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(status=200, body=b'a', headers={'Content-Length': '500'})

        self.assertEqual(plugin.process(response), plugin.RESPONSE_INDEX)

    def test_skipempty_returns_none_when_content_length_header_is_large(self):
        """SkipemptyResponsePlugin should not skip when Content-Length is above threshold."""

        plugin = SkipemptyResponsePlugin(None)
        response = self.make_response(status=200, body=b'a' * 600, headers={'Content-Length': '600'})

        self.assertIsNone(plugin.process(response))

    def test_skipempty_uses_body_length_when_header_is_missing(self):
        """SkipemptyResponsePlugin should use body length when Content-Length is missing."""

        plugin = SkipemptyResponsePlugin(None)

        small = self.make_response(status=200, body=b'a' * 10, headers={})
        large = self.make_response(status=200, body=b'a' * 600, headers={})

        self.assertEqual(plugin.process(small), plugin.RESPONSE_INDEX)
        self.assertIsNone(plugin.process(large))


if __name__ == '__main__':
    unittest.main()