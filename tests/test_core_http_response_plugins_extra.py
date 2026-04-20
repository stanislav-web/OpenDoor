# -*- coding: utf-8 -*-

import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response.collation import CollationResponsePlugin
from src.core.http.plugins.response.file import FileResponsePlugin
from src.core.http.plugins.response.skipempty import SkipemptyResponsePlugin
from src.core.http.plugins.response.skipsizes import SkipSizesResponsePlugin


class TestHttpResponsePluginsExtra(unittest.TestCase):
    """TestHttpResponsePluginsExtra class."""

    def make_response(self, status=200, body=b'', headers=None):
        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_file_plugin_detects_large_body_when_header_small(self):
        """FileResponsePlugin should classify large bodies as files even when Content-Length is small."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(body=b'x' * 1000001, headers={'Content-Length': '10'})

        self.assertEqual(plugin.process(response), 'file')

    def test_file_plugin_returns_none_for_unsupported_status(self):
        """FileResponsePlugin should ignore unsupported statuses."""

        plugin = FileResponsePlugin(None)
        response = self.make_response(status=404, body=b'x' * 1000001, headers={'Content-Length': '1000001'})

        self.assertIsNone(plugin.process(response))

    def test_skipempty_handles_large_header_and_small_body_without_header(self):
        """SkipemptyResponsePlugin should cover both header and body-only branches."""

        plugin = SkipemptyResponsePlugin(None)

        self.assertIsNone(plugin.process(self.make_response(body=b'x' * 10, headers={'Content-Length': '700'})))
        self.assertEqual(plugin.process(self.make_response(body=b'x' * 10, headers={})), 'skip')

    def test_skipsizes_none_values_and_body_size_branch(self):
        """SkipSizesResponsePlugin should work with manually populated size list and body length fallback."""

        plugin = SkipSizesResponsePlugin(None)
        plugin.SIZE_VALUES = ['2KB']

        self.assertEqual(plugin.process(self.make_response(body=b'x' * 2048, headers={})), 'skip')
        self.assertIsNone(plugin.process(self.make_response(body=b'x' * 10, headers={})))

    def test_collation_handles_small_body_and_body_without_header(self):
        """CollationResponsePlugin should ignore short bodies and compare body lengths without headers."""

        plugin = CollationResponsePlugin(None)

        self.assertIsNone(plugin.process(self.make_response(body=b'x' * 50, headers={})))

        body1 = b'a' * 120 + b'b' * 10
        body2 = b'a' * 119 + b'b' * 11

        self.assertIsNone(plugin.process(self.make_response(body=body1, headers={})))
        self.assertEqual(plugin.process(self.make_response(body=body2, headers={})), 'failed')

    def test_collation_current_item_ratio_match_branch(self):
        """CollationResponsePlugin should trigger the current_item ratio branch on repeated near-matches."""

        plugin = CollationResponsePlugin(None)

        first = (b'a' * 120) + (b'b' * 10)
        second = (b'a' * 100) + (b'c' * 40)
        third = (b'a' * 100) + (b'd' * 40)

        self.assertIsNone(plugin.process(self.make_response(body=first, headers={'Content-Length': str(len(first))})))
        self.assertIsNone(plugin.process(self.make_response(body=second, headers={'Content-Length': str(len(second))})))
        self.assertEqual(plugin.process(self.make_response(body=third, headers={'Content-Length': str(len(third))})), 'failed')


if __name__ == '__main__':
    unittest.main()