# -*- coding: utf-8 -*-

import json
import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response import secret
from src.core.http.plugins.response.secret import SecretResponsePlugin


class TestSecretResponsePlugin(unittest.TestCase):
    """SecretResponsePlugin test cases."""

    def make_response(self, status=200, body=b'', headers=None):
        """
        Build a urllib3 response for plugin tests.

        :param int status: HTTP status code
        :param bytes body: response body
        :param dict|None headers: response headers
        :return: HTTP response
        """

        return HTTPResponse(status=status, body=body, headers=headers or {'Content-Type': 'text/plain'})

    def assert_secret_detection(self, body, secret_type, confidence=70, headers=None):
        """
        Assert that a response body is classified as secret.

        :param str body: response body
        :param str secret_type: expected secret type
        :param int confidence: minimum expected confidence
        :param dict|None headers: optional response headers
        :return: secret detection metadata
        """

        plugin = SecretResponsePlugin(None)
        response = self.make_response(body=body.encode('utf-8'), headers=headers)

        self.assertEqual(plugin.process(response), 'secret')
        detection = getattr(response, 'opendoor_secret_detection')
        self.assertEqual(detection['type'], secret_type)
        self.assertGreaterEqual(detection['confidence'], confidence)
        self.assertEqual(detection['count'], 1)
        self.assertIn(secret_type, detection['types'])
        self.assertNotIn(body, json.dumps(detection, sort_keys=True))
        return detection

    def test_response_package_exports_secret_plugin_alias(self):
        """Response plugin loader should be able to resolve the secret alias."""

        self.assertIs(secret, SecretResponsePlugin)

    def test_detects_aws_access_key_and_returns_secret_bucket(self):
        """Should classify AWS access keys into the secret bucket."""

        detection = self.assert_secret_detection('AKIA1234567890ABCDEF', 'aws_access_key', 95)

        self.assertEqual(detection['redacted'], 'AKIA****CDEF')

    def test_detects_common_token_families(self):
        """Should detect common token families without storing raw values."""

        samples = [
            ('ghp_' + ('A' * 36), 'github_token', 95),
            ('xoxb-1234567890-abcdEFGHijk', 'slack_token', 95),
            ('sk_live_' + ('A' * 24), 'stripe_key', 95),
            ('AIza' + ('A' * 35), 'google_api_key', 90),
            ('github_pat_' + ('A' * 40), 'github_fine_grained_token', 95),
            ('sq0csp-' + ('A' * 24), 'square_token', 92),
        ]

        for value, secret_type, confidence in samples:
            with self.subTest(secret_type=secret_type):
                self.assert_secret_detection(value, secret_type, confidence)

    def test_detects_jwt_private_key_database_url_and_generic_assignment(self):
        """Should detect structured secrets and credentials in textual responses."""

        jwt = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature1234567890'
        samples = [
            (jwt, 'jwt', 90),
            ('-----BEGIN PRIVATE KEY-----\nredacted\n-----END PRIVATE KEY-----', 'private_key', 98),
            ('postgresql://app_user:superSecretPassword@db.local:5432/app', 'database_url', 92),
            ('api_key = "live_secret_value_12345"', 'generic_assignment', 70),
            ('access_secret = "live_access_secret_12345"', 'generic_assignment', 70),
        ]

        for value, secret_type, confidence in samples:
            with self.subTest(secret_type=secret_type):
                self.assert_secret_detection(value, secret_type, confidence)

    def test_detects_json_vendor_content_types(self):
        """Should inspect JSON and vendor JSON response bodies."""

        self.assert_secret_detection(
            '{"token":"ghp_' + ('B' * 36) + '"}',
            'github_token',
            95,
            headers={'Content-Type': 'application/vnd.api+json'},
        )

    def test_detects_authorization_bearer_without_storing_raw_token(self):
        """Should detect leaked bearer headers while storing only redacted metadata."""

        token = 'headerPayloadSignatureValue1234567890'
        detection = self.assert_secret_detection(
            'Authorization: Bearer ' + token,
            'authorization_bearer',
            88,
        )

        self.assertEqual(detection['redacted'], 'head****7890')

    def test_should_keep_secret_searcher_style_placeholder_hits_suppressed(self):
        """Should avoid broad keyword-style hits when values are placeholders."""

        self.assertIsNone(
            SecretResponsePlugin.detect('Authorization: Bearer redactedBearerToken123456')
        )
        self.assertIsNone(
            SecretResponsePlugin.detect('account_key = "maskedAccountKey123456"')
        )

    def test_ignores_binary_non_success_and_normal_responses(self):
        """Should avoid binary content, non-200 responses and ordinary text."""

        plugin = SecretResponsePlugin(None)
        binary = self.make_response(
            body=b'AKIA1234567890ABCDEF',
            headers={'Content-Type': 'application/pdf'},
        )
        forbidden = self.make_response(status=403, body=b'AKIA1234567890ABCDEF')
        normal = self.make_response(body=b'<html><body>Hello world</body></html>')

        self.assertIsNone(plugin.process(binary))
        self.assertFalse(hasattr(binary, 'opendoor_secret_detection'))
        self.assertIsNone(plugin.process(forbidden))
        self.assertFalse(hasattr(forbidden, 'opendoor_secret_detection'))
        self.assertIsNone(plugin.process(normal))
        self.assertFalse(hasattr(normal, 'opendoor_secret_detection'))

    def test_ignores_obvious_placeholders_and_unsigned_jwt(self):
        """Should reduce placeholder and unsigned JWT false positives."""

        plugin = SecretResponsePlugin(None)
        placeholder = self.make_response(body=b'api_key = "your_api_key_here"')
        unsigned_jwt = self.make_response(
            body=b'eyJhbGciOiJub25lIn0.eyJzdWIiOiIxMjMifQ.signature1234567890'
        )

        self.assertIsNone(plugin.process(placeholder))
        self.assertFalse(hasattr(placeholder, 'opendoor_secret_detection'))
        self.assertIsNone(plugin.process(unsigned_jwt))
        self.assertFalse(hasattr(unsigned_jwt, 'opendoor_secret_detection'))

    def test_should_cover_secret_detector_edge_paths(self):
        """Should cover edge paths without leaking raw secret values."""

        plugin = SecretResponsePlugin(None)

        empty = self.make_response(body=b'')
        self.assertIsNone(plugin.process(empty))

        without_content_type = HTTPResponse(
            status=200,
            body=b'ASIA1234567890ABCDEF',
            headers={},
        )
        self.assertEqual(plugin.process(without_content_type), 'secret')
        self.assertEqual(
            without_content_type.opendoor_secret_detection['type'],
            'aws_access_key',
        )

        xml_vendor = self.make_response(
            body=b'password = "uniqueSecretValue98765"',
            headers={'content-type': 'application/vnd.acme+xml; charset=utf-8'},
        )
        self.assertEqual(plugin.process(xml_vendor), 'secret')
        self.assertEqual(
            xml_vendor.opendoor_secret_detection['type'],
            'generic_assignment',
        )

        unknown_type = self.make_response(
            body=b'AKIA1234567890ABCDEF',
            headers={'Content-Type': 'application/x-custom'},
        )
        self.assertIsNone(plugin.process(unknown_type))

        class NullBodyResponse:
            status = 200
            headers = {'Content-Type': 'text/plain'}
            data = None

        self.assertIsNone(plugin.process(NullBodyResponse()))

        class StringBodyResponse:
            status = 200
            headers = {'Content-Type': 'text/plain'}
            data = 'AKIA1234567890ABCDEF'

        self.assertEqual(plugin.process(StringBodyResponse()), 'secret')

        class FrozenResponse:
            __slots__ = ('status', 'headers', 'data')

            def __init__(self):
                self.status = 200
                self.headers = {'Content-Type': 'text/plain'}
                self.data = b'AKIA1234567890ABCDEF'

        self.assertEqual(plugin.process(FrozenResponse()), 'secret')

    def test_should_cover_secret_false_positive_and_helper_edges(self):
        """Should keep helper edge cases deterministic and safe."""

        repeated = SecretResponsePlugin.detect('password = "aaaaaaaaaaaa"')
        self.assertIsNone(repeated)

        duplicate = SecretResponsePlugin.detect(
            'AKIA1234567890ABCDEF AKIA1234567890ABCDEF'
        )
        self.assertEqual(duplicate['count'], 1)

        many = SecretResponsePlugin.detect(' '.join([
            'AKIA000000000000{0:04d}'.format(index)
            for index in range(10)
        ]))
        self.assertEqual(many['count'], SecretResponsePlugin.MAX_FINDINGS)

        self.assertEqual(SecretResponsePlugin.redact('short'), '*****')
        self.assertTrue(
            SecretResponsePlugin._is_supported_status(type('BadStatus', (), {'status': object()})()) is False
        )
        self.assertEqual(
            SecretResponsePlugin._get_header(
                type('LowerHeader', (), {'headers': {'content-type': 'text/plain'}})(),
                'Content-Type',
            ),
            'text/plain',
        )
        self.assertIsNone(
            SecretResponsePlugin._get_header(
                type('Headers', (), {'headers': {'X-Test': '1'}})(),
                'Content-Type',
            )
        )
        self.assertTrue(SecretResponsePlugin._looks_like_unsigned_or_placeholder_jwt('broken'))
        self.assertFalse(
            SecretResponsePlugin._looks_like_unsigned_or_placeholder_jwt(
                'eyJbadbadbad.badbadbad.badbadbad'
            )
        )


if __name__ == '__main__':
    unittest.main()
