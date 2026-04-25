# -*- coding: utf-8 -*-

import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response.skipsizes import SkipSizesResponsePlugin


class TestSkipSizesResponsePlugin(unittest.TestCase):
    """Coverage and regression tests for SkipSizesResponsePlugin."""

    def make_response(self, status=200, body=b'', headers=None):
        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_detects_exact_size_from_content_length_header(self):
        """Should preserve legacy exact KB matching from Content-Length."""

        plugin = SkipSizesResponsePlugin('2')
        response = self.make_response(
            body=b'x' * 10,
            headers={'Content-Length': '2048'}
        )

        self.assertEqual(plugin.process(response), 'skip')

    def test_detects_exact_size_from_body_length_without_header(self):
        """Should preserve legacy fallback to body length."""

        plugin = SkipSizesResponsePlugin('2')
        response = self.make_response(
            body=b'x' * 2048,
            headers={}
        )

        self.assertEqual(plugin.process(response), 'skip')

    def test_detects_range_match_from_content_length_header(self):
        """Should match configured KB ranges from Content-Length."""

        plugin = SkipSizesResponsePlugin('2-3')
        response = self.make_response(
            body=b'x' * 10,
            headers={'Content-Length': str(2500)}
        )

        self.assertEqual(plugin.process(response), 'skip')

    def test_detects_range_match_from_body_length_without_header(self):
        """Should match configured KB ranges from body length fallback."""

        plugin = SkipSizesResponsePlugin('2-3')
        response = self.make_response(
            body=b'x' * 2800,
            headers={}
        )

        self.assertEqual(plugin.process(response), 'skip')

    def test_handles_invalid_content_length_with_body_fallback(self):
        """Should not fail on invalid Content-Length and should fall back to body size."""

        plugin = SkipSizesResponsePlugin('2')
        response = self.make_response(
            body=b'x' * 2048,
            headers={'Content-Length': 'invalid'}
        )

        self.assertEqual(plugin.process(response), 'skip')

    def test_returns_none_when_size_does_not_match(self):
        """Should return None when neither exact nor range sizes match."""

        plugin = SkipSizesResponsePlugin('2:4-5')
        response = self.make_response(
            body=b'x' * 3072,
            headers={}
        )

        self.assertIsNone(plugin.process(response))

    def test_returns_none_for_unsupported_status(self):
        """Should return None for unsupported statuses."""

        plugin = SkipSizesResponsePlugin('2')
        response = self.make_response(
            status=404,
            body=b'x' * 2048,
            headers={'Content-Length': '2048'}
        )

        self.assertIsNone(plugin.process(response))

    def test_keeps_legacy_manual_size_values_contract(self):
        """Should keep working with tests that manually populate SIZE_VALUES."""

        plugin = SkipSizesResponsePlugin(None)
        plugin.SIZE_VALUES = ['2KB']

        response = self.make_response(
            body=b'x' * 2048,
            headers={}
        )

        self.assertEqual(plugin.process(response), 'skip')

    def test_normalizes_reversed_range_bounds(self):
        """Should normalize reversed range bounds like 5-2."""

        plugin = SkipSizesResponsePlugin('5-2')
        response = self.make_response(
            body=b'x' * 3072,
            headers={}
        )

        self.assertEqual(plugin.process(response), 'skip')