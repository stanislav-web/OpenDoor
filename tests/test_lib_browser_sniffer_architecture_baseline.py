# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from urllib3.response import HTTPResponse

from src.core.http.plugins.response_plugin import ResponsePlugin
from src.core.http.response import Response
from src.core.http.providers.response import ResponseProvider


class TestSnifferArchitectureBaseline(unittest.TestCase):
    """Regression safety net for the legacy response-sniffer architecture."""

    @staticmethod
    def make_response(status=200, body=b'', headers=None):
        """Create a response object for sniffer classification tests."""

        return HTTPResponse(status=status, body=body, headers=headers or {})

    @staticmethod
    def make_cfg(**overrides):
        """Create a minimal Response configuration object."""

        base = {
            'is_sniff': True,
            'sniffers': [],
            'SUBDOMAINS_SCAN': 'subdomains',
            'scan': 'directories',
            'is_waf_detect': False,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @staticmethod
    def make_debug(level=0):
        """Create a debug stub accepted by Response."""

        return SimpleNamespace(
            level=level,
            debug_load_sniffer_plugin=MagicMock(),
            debug_response=MagicMock(),
            debug_request_uri=MagicMock(),
            debug_classification=MagicMock(),
        )

    def test_all_public_sniffer_aliases_load_without_cli_renames(self):
        """Every documented --sniff alias should resolve through the legacy plugin loader."""

        aliases = {
            'file': 'file',
            'secret': 'secret',
            'indexof': 'indexof',
            'stacktrace': 'stacktrace',
            'skipempty': 'skip',
            'collation': 'failed',
            'shadow': 'shadow',
            'openredirect': 'openredirect',
            'skipsizes=1:2': 'skip',
        }

        for alias, expected_index in aliases.items():
            with self.subTest(alias=alias):
                plugin = ResponsePlugin.load(alias)

                self.assertEqual(plugin.RESPONSE_INDEX, expected_index)
                self.assertTrue(callable(plugin.process))

    def test_response_loads_enabled_sniffers_in_requested_cli_order(self):
        """Response should preserve selected --sniff aliases while loading plugin instances."""

        sniffers = [
            'file',
            'secret',
            'indexof',
            'stacktrace',
            'skipempty',
            'collation',
            'shadow',
            'openredirect',
            'skipsizes=1:2',
        ]
        response = Response(self.make_cfg(sniffers=sniffers), self.make_debug(level=1), tpl=MagicMock())

        self.assertEqual(
            [plugin.RESPONSE_INDEX for plugin in response._response_plugins],
            ['file', 'secret', 'indexof', 'stacktrace', 'skip', 'failed', 'shadow', 'openredirect', 'skip'],
        )

    def test_active_marker_sniffers_do_not_passively_block_later_detectors(self):
        """Active-only sniffers should return None and let passive sniffers classify the response."""

        provider = ResponseProvider(self.make_cfg())
        provider._response_plugins = [
            ResponsePlugin.load('shadow'),
            ResponsePlugin.load('openredirect'),
            ResponsePlugin.load('secret'),
        ]
        response = self.make_response(
            body=b'window.__cfg = {"aws_key":"AKIAABCDEFGHIJKLMNOP"};',
            headers={'Content-Type': 'text/html'},
        )

        self.assertEqual(provider.detect('https://example.com/config.js', response), 'secret')
        self.assertIsNotNone(getattr(response, 'opendoor_secret_detection', None))

    def test_legacy_passive_sniffer_chain_is_currently_first_match(self):
        """Document current first-match behavior before the multi-finding engine migration."""

        body = b'window.__cfg = {"aws_key":"AKIAABCDEFGHIJKLMNOP"};'
        headers = {'Content-Length': '1000000'}

        file_first = ResponseProvider(self.make_cfg())
        file_first._response_plugins = [ResponsePlugin.load('file'), ResponsePlugin.load('secret')]
        self.assertEqual(
            file_first.detect('https://example.com/download.js', self.make_response(body=body, headers=headers)),
            'file',
        )

        secret_first = ResponseProvider(self.make_cfg())
        secret_first._response_plugins = [ResponsePlugin.load('secret'), ResponsePlugin.load('file')]
        response = self.make_response(body=body, headers=headers)

        self.assertEqual(secret_first.detect('https://example.com/download.js', response), 'secret')
        self.assertIsNotNone(getattr(response, 'opendoor_secret_detection', None))


if __name__ == '__main__':
    unittest.main()
