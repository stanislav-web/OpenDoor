# -*- coding: utf-8 -*-

import unittest

from src.core.http.tls import (
    TLS_LEGACY_CIPHERS,
    describe_tls_transport_error,
    maybe_build_ssl_context,
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


if __name__ == '__main__':
    unittest.main()
