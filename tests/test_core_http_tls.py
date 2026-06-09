# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from src.core.http.tls import (
    TLS_LEGACY_CIPHERS,
    describe_tls_transport_error,
    emit_tls_legacy_policy,
    maybe_build_ssl_context,
    tls_pool_kwargs,
    warn_tls_transport_error,
)


class ReasonError(Exception):
    """Exception with nested urllib3-like reason attribute."""

    def __init__(self, reason):
        """Initialize with a reason value."""

        super(ReasonError, self).__init__('outer')
        self.reason = reason


class TestTlsHelpers(unittest.TestCase):
    """Test TLS helper behavior."""

    def test_maybe_build_ssl_context_defaults_to_none(self):
        """maybe_build_ssl_context() should preserve default TLS policy when disabled."""

        self.assertIsNone(maybe_build_ssl_context(False))
        self.assertIsNone(maybe_build_ssl_context(None))

    def test_maybe_build_ssl_context_excludes_dhe_when_enabled(self):
        """maybe_build_ssl_context() should build a legacy context when enabled."""

        context = maybe_build_ssl_context(True)

        self.assertIsNotNone(context)
        self.assertIn('!DHE', TLS_LEGACY_CIPHERS)
        self.assertFalse(context.check_hostname)

    def test_describe_tls_transport_error_detects_weak_dh(self):
        """describe_tls_transport_error() should detect weak-DH OpenSSL failures."""

        message = describe_tls_transport_error(ReasonError('ssl routines: dh key too small'))

        self.assertIn('DH_KEY_TOO_SMALL', message)
        self.assertIn('--tls-legacy', message)

    def test_describe_tls_transport_error_handles_generic_and_long_tls_errors(self):
        """describe_tls_transport_error() should compact generic TLS diagnostics."""

        message = describe_tls_transport_error(Exception('TLS alert handshake failure'))
        self.assertEqual(message, 'TLS handshake failed: TLS alert handshake failure')

        long_message = 'SSL ' + ('x' * 400)
        compacted = describe_tls_transport_error(Exception(long_message))
        self.assertTrue(compacted.endswith('...'))
        self.assertLess(len(compacted), len(long_message))

    def test_describe_tls_transport_error_ignores_non_tls_errors(self):
        """describe_tls_transport_error() should ignore non-TLS transport failures."""

        self.assertIsNone(describe_tls_transport_error(Exception('connection refused')))

    def test_describe_tls_transport_error_ignores_dns_failures_with_tls_like_hostnames(self):
        """DNS failures should not become TLS warnings because the hostname contains ssl/tls."""

        samples = [
            "HTTPSConnection(host='mtls.localhost', port=443): Failed to resolve 'mtls.localhost' ([Errno 8] nodename nor servname provided, or not known)",
            "HTTPSConnection(host='ssl.localhost', port=443): Failed to resolve 'ssl.localhost' ([Errno -2] Name or service not known)",
            "NameResolutionError: Failed to resolve 'tls.example.test' (Temporary failure in name resolution)",
            "Failed to resolve 'api-tls.example.test' (No address associated with hostname)",
        ]

        for sample in samples:
            with self.subTest(sample=sample):
                self.assertIsNone(describe_tls_transport_error(Exception(sample)))

    def test_tls_pool_kwargs_returns_context_only_when_present(self):
        """tls_pool_kwargs() should preserve urllib3 defaults unless a context exists."""

        context = object()

        self.assertEqual(tls_pool_kwargs(None), {})
        self.assertEqual(tls_pool_kwargs(context), {'ssl_context': context})

    def test_emit_tls_legacy_policy_only_logs_when_enabled(self):
        """emit_tls_legacy_policy() should keep legacy-mode debug output centralized."""

        tpl = Mock()
        emit_tls_legacy_policy(Mock(is_tls_legacy=False), tpl)
        tpl.debug.assert_not_called()

        emit_tls_legacy_policy(Mock(is_tls_legacy=True), tpl)
        tpl.debug.assert_called_once()
        self.assertIn(TLS_LEGACY_CIPHERS, tpl.debug.call_args.kwargs['msg'])

    def test_warn_tls_transport_error_stores_warns_and_finishes_line(self):
        """warn_tls_transport_error() should centralize TLS warning propagation."""

        cfg = Mock()
        tpl = Mock()
        line_finisher = Mock()

        message = warn_tls_transport_error(
            cfg,
            tpl,
            ReasonError('ssl routines: dh key too small'),
            line_finisher=line_finisher,
        )

        self.assertIn('DH_KEY_TOO_SMALL', message)
        self.assertEqual(cfg.last_transport_error, message)
        line_finisher.assert_called_once_with()
        tpl.warning.assert_called_once_with(msg=message)

    def test_warn_tls_transport_error_ignores_non_tls_errors(self):
        """warn_tls_transport_error() should avoid warnings for non-TLS failures."""

        cfg = SimpleNamespace()
        tpl = Mock()
        line_finisher = Mock()

        self.assertIsNone(warn_tls_transport_error(cfg, tpl, Exception('connection refused'), line_finisher))
        self.assertFalse(hasattr(cfg, 'last_transport_error'))
        line_finisher.assert_not_called()
        tpl.warning.assert_not_called()


if __name__ == '__main__':
    unittest.main()
