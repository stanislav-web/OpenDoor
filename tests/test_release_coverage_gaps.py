# -*- coding: utf-8 -*-

import socket as py_socket
import unittest
from unittest.mock import patch

from src.core.http.exceptions import SocketError
from src.core.http.socks import Socket
from src.lib.browser.config import Config
from src.lib.browser.sniffers import SnifferContext, SnifferDecision, SnifferEngine, SnifferResult


class _TupleDetector(object):
    """Fake detector returning a tuple of findings."""

    NAME = 'tuple-detector'
    KIND = 'detector'

    def match(self, context):
        """Return one finding as a tuple to exercise engine normalization."""

        return (SnifferResult(bucket='tuple', url=context.request_url),)


class TestReleaseCoverageGaps(unittest.TestCase):
    """Release hardening tests for remaining coverage gaps."""

    def test_config_validation_covers_blank_and_malformed_filter_tokens(self):
        """Config should ignore blank filter tokens and reject malformed filter values."""

        cfg = Config({
            'reports': 'std',
            'include_status': [' ', '200'],
            'exclude_size': [' ', '0'],
            'exclude_size_range': [' ', '0-1'],
        })

        self.assertEqual(cfg.include_status, ['200'])
        self.assertEqual(cfg.exclude_size, [0])
        self.assertEqual(cfg.exclude_size_range, [(0, 1)])
        self.assertIsNone(Config._normalize_text_filter_values('   '))

        invalid_cases = [
            {'min_response_length': 'abc'},
            {'include_status': '300-200'},
            {'include_status': '99-200'},
            {'include_status': '200-600'},
            {'exclude_size_range': '100'},
            {'exclude_size_range': 'a-b'},
        ]

        for params in invalid_cases:
            with self.subTest(params=params):
                payload = {'reports': 'std'}
                payload.update(params)
                with self.assertRaises(ValueError):
                    Config(payload)

    def test_config_method_override_deduplicates_existing_items_and_fractional_delay(self):
        """Config should avoid duplicate override labels and preserve fractional delays below one second."""

        original = Config.BODY_REQUIRED_SNIFFERS
        Config.BODY_REQUIRED_SNIFFERS = original + ('--match-text',)
        try:
            cfg = Config({
                'reports': 'std',
                'method': 'HEAD',
                'sniff': '--match-text',
                'match_text': ['login'],
                'delay': 0.25,
            })
            self.assertEqual(cfg.method_override_items, ['--match-text'])
            self.assertEqual(cfg.delay, 0.25)
        finally:
            Config.BODY_REQUIRED_SNIFFERS = original

    def test_socket_connect_address_helpers_cover_error_and_dedupe_paths(self):
        """Socket diagnostics should handle DNS errors, malformed records and duplicate addresses."""

        with patch('src.core.http.socks.socket.getaddrinfo', side_effect=py_socket.gaierror(-2, 'fail')):
            self.assertEqual(Socket._resolve_connect_addresses('bad.local', 80), [])

        with patch('src.core.http.socks.socket.getaddrinfo', return_value=[
            (py_socket.AF_INET, py_socket.SOCK_STREAM, 6, ''),
            (py_socket.AF_INET, py_socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80)),
            (py_socket.AF_INET, py_socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80)),
        ]):
            self.assertEqual(Socket._resolve_connect_addresses('example.com', 80), ['127.0.0.1'])

        self.assertEqual(Socket._format_connect_addresses([]), 'unresolved')

    def test_socket_ping_does_not_close_missing_socket_on_connect_failure(self):
        """Socket.ping() should not try to close a socket when connection creation fails early."""

        with patch('src.core.http.socks.socket.create_connection', side_effect=ValueError('bad port')):
            with self.assertRaises(SocketError):
                Socket.ping('example.com', 'bad', timeout=1)

    def test_sniffer_engine_normalizes_tuple_results(self):
        """SnifferEngine should normalize tuple results into a list of findings."""

        context = SnifferContext(request_url='https://example.com/admin')
        engine = SnifferEngine(enabled=['tuple-detector'], sniffers=[_TupleDetector()])

        decision = engine.run_passive(context)

        self.assertEqual([result.bucket for result in decision.findings], ['tuple'])

    def test_sniffer_result_uses_explicit_evidence_key_and_extend_ignores_none(self):
        """SnifferResult should prefer explicit evidence keys and decisions should accept empty extensions."""

        result = SnifferResult(
            bucket='secret',
            url='https://example.com/config.php',
            metadata={'evidence': 'metadata-value'},
            evidence_key='explicit-value',
        )
        decision = SnifferDecision()

        self.assertEqual(result.dedupe_key(), ('secret', 'https://example.com/config.php', 'explicit-value'))
        self.assertIs(decision.extend(None), decision)
        self.assertEqual(decision.findings, [])


if __name__ == '__main__':
    unittest.main()
