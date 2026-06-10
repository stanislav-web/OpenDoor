# -*- coding: utf-8 -*-

import base64
import json
import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response import secret
from src.core.http.plugins.response.secret import SecretResponsePlugin


class TestSecretResponsePlugin(unittest.TestCase):
    """SecretResponsePlugin test cases."""

    @staticmethod
    def make_slack_fixture_token(prefix='xoxb'):
        """Build Slack-shaped fixtures without storing token-shaped literals."""

        if prefix == 'xoxa-2':
            return ''.join([
                'xoxa',
                '-2',
                '-123456789012',
                '-123456789012',
                '-abcdefghijklmnopqrstuvwx',
            ])

        return ''.join([
            prefix,
            '-123456789012',
            '-123456789012',
            '-abcdefghijklmnopqrstuvwx',
        ])

    @staticmethod
    def make_slack_like_text(prefix='xoxa', suffix=''):
        """Build xox*-like false-positive fixtures without raw token-like literals."""

        return ''.join([prefix, suffix])

    def make_response(self, status=200, body=b'', headers=None):
        """
        Build a urllib3 response for plugin tests.

        :param int status: HTTP status code
        :param bytes body: response body
        :param dict|None headers: response headers
        :return: HTTP response
        """

        return HTTPResponse(status=status, body=body, headers=headers or {'Content-Type': 'text/plain'})

    def make_jwt(self, header=None, payload=None, signature='signature1234567890'):
        """
        Build a compact JWT-like value for deterministic tests.

        :param dict|None header: JWT header values
        :param dict|None payload: JWT payload values
        :param str signature: bounded signature placeholder
        :return: JWT-like value
        :rtype: str
        """

        def encode(value):
            raw = json.dumps(value, separators=(',', ':')).encode('utf-8')
            return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')

        header = header or {'alg': 'HS256', 'typ': 'JWT'}
        payload = payload or {'iss': 'https://issuer.example', 'aud': 'api'}
        return '.'.join((encode(header), encode(payload), signature))

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
            (self.make_slack_fixture_token('xoxb'), 'slack_token', 95),
            (self.make_slack_fixture_token('xoxa-2'), 'slack_token', 95),
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
        self.assertIsNone(
            SecretResponsePlugin.detect(
                'https://example.com/ot-gory-iumor-do-reki-'
                + self.make_slack_like_text('xoxa', '-v')
                + '-priamure-nasli-smesnye-geograficeskie-obieekty'
            )
        )

    def test_slack_token_shape_validator_rejects_malformed_candidates(self):
        """Slack validator should reject malformed xox*-style false positives."""

        invalid_values = [
            self.make_slack_like_text('xoxb'),
            ''.join(['xoxo', '-123456789012', '-abcdefghijklmnopqrstuvwx']),
            ''.join(['xoxb', '-123456789012', '-short']),
            ''.join(['xoxa', '-2', '-abcdefghijklmnopqrstuvwx']),
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                self.assertFalse(SecretResponsePlugin._looks_like_slack_token(value))

    def test_ignores_slack_like_url_slugs_inside_sitemap_locations(self):
        """Should not classify sitemap URL slugs that only look like Slack token prefixes."""

        plugin = SecretResponsePlugin(None)
        response = self.make_response(
            body=(
                b'<?xml version="1.0" encoding="UTF-8"?>'
                b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                b'<url><loc>https://example.com/news/'
                + self.make_slack_like_text('xoxa', '-hozyaystvennye-proekty').encode('ascii')
                + b'</loc></url>'
                b'<url><loc>https://ampravda.ru/2026/04/01/'
                b'ot-gory-iumor-do-reki-'
                + self.make_slack_like_text('xoxa', '-v-priamure').encode('ascii')
                + b'-nasli-smesnye-'
                b'geograficeskie-obieekty</loc></url>'
                b'</urlset>'
            ),
            headers={'Content-Type': 'application/xml; charset=utf-8'},
        )

        self.assertIsNone(plugin.process(response))
        self.assertFalse(hasattr(response, 'opendoor_secret_detection'))

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

    def test_enriches_jwt_secret_with_bounded_claims_metadata(self):
        """Should add bounded JWT claims metadata only after JWT detection."""

        token = self.make_jwt(
            header={'alg': 'HS256', 'typ': 'JWT', 'kid': 'app-1'},
            payload={
                'iss': 'https://idp.example',
                'aud': 'api',
                'exp': 1893456000,
                'iat': 1717200000,
                'sub': 'user-123',
                'email': 'user@example.com',
                'roles': ['admin'],
            },
        )

        detection = self.assert_secret_detection(token, 'jwt', 90)
        match = detection['matches'][0]
        claims = match['jwt_claims']

        self.assertEqual(detection['jwt_claims'], claims)
        self.assertEqual(claims['alg'], 'HS256')
        self.assertEqual(claims['typ'], 'JWT')
        self.assertEqual(claims['kid'], 'app-1')
        self.assertEqual(claims['iss'], 'https://idp.example')
        self.assertEqual(claims['aud'], 'api')
        self.assertEqual(claims['exp'], 1893456000)
        self.assertEqual(claims['iat'], 1717200000)
        self.assertIn('long_lived', claims['risk_flags'])
        self.assertNotIn('sub', claims)
        self.assertNotIn('email', claims)
        self.assertNotIn('roles', claims)
        self.assertNotIn(token, json.dumps(detection, sort_keys=True))
        self.assertNotIn('signature1234567890', json.dumps(detection, sort_keys=True))

    def test_jwt_claims_metadata_reports_conservative_risk_flags(self):
        """Should report conservative JWT metadata risk flags deterministically."""

        missing_exp = self.make_jwt(payload={'iss': 'https://issuer.example'})
        missing_exp_claims = SecretResponsePlugin._extract_jwt_claims_metadata(
            missing_exp,
            now=1700000000,
        )
        self.assertIn('missing_exp', missing_exp_claims['risk_flags'])

        risky = self.make_jwt(
            header={'alg': 'none', 'typ': 'JWT'},
            payload={'exp': 100, 'nbf': 2000, 'iat': 1},
        )
        risky_claims = SecretResponsePlugin._extract_jwt_claims_metadata(
            risky,
            now=1000,
        )

        self.assertEqual(risky_claims['alg'], 'none')
        self.assertIn('alg_none', risky_claims['risk_flags'])
        self.assertIn('expired', risky_claims['risk_flags'])
        self.assertIn('not_yet_valid', risky_claims['risk_flags'])

    def test_jwt_claims_metadata_handles_malformed_and_bounded_values(self):
        """Should keep JWT metadata parsing bounded and best-effort."""

        malformed = 'eyJbadbadbad.badbadbad.signature1234567890'
        self.assertEqual(
            SecretResponsePlugin._extract_jwt_claims_metadata(malformed),
            {},
        )

        large_part = 'A' * (SecretResponsePlugin.JWT_MAX_PART_BYTES + 1)
        self.assertEqual(
            SecretResponsePlugin._decode_jwt_json_part(large_part),
            {},
        )

        token = self.make_jwt(
            header={'alg': 'HS256', 'typ': 'JWT', 'kid': 'k' * 200},
            payload={
                'iss': 'i' * 300,
                'aud': ['api', 'admin', 42, 'ops', 'extra', 'ignored'],
                'exp': '1893456000',
                'iat': True,
            },
        )
        claims = SecretResponsePlugin._extract_jwt_claims_metadata(token, now=1700000000)

        self.assertEqual(len(claims['kid']), 128)
        self.assertEqual(len(claims['iss']), 256)
        self.assertEqual(claims['aud'], ['api', 'admin', 'ops', 'extra'])
        self.assertEqual(claims['exp'], 1893456000)
        self.assertNotIn('iat', claims)

    def test_jwt_claims_metadata_covers_empty_and_unsupported_values(self):
        """Should safely degrade JWT metadata for empty and unsupported claim values."""

        self.assertEqual(SecretResponsePlugin._extract_jwt_claims_metadata('broken'), {})

        token = self.make_jwt(
            header={'alg': '', 'typ': 'JWT', 'kid': None},
            payload={'iss': '   ', 'aud': 123, 'exp': 1700000100},
        )
        claims = SecretResponsePlugin._extract_jwt_claims_metadata(token, now=1700000000)

        self.assertEqual(claims['typ'], 'JWT')
        self.assertEqual(claims['exp'], 1700000100)
        self.assertNotIn('alg', claims)
        self.assertNotIn('kid', claims)
        self.assertNotIn('iss', claims)
        self.assertNotIn('aud', claims)
        self.assertNotIn('risk_flags', claims)

    def test_jwt_detection_omits_empty_claims_metadata(self):
        """Should keep JWT detection when claims metadata cannot be decoded."""

        token = 'eyJaaaaaaaaa.bbbbbbbbbb.signature1234567890'
        detection = self.assert_secret_detection(token, 'jwt', 90)

        self.assertNotIn('jwt_claims', detection)
        self.assertNotIn('jwt_claims', detection['matches'][0])

    def test_non_jwt_secret_matches_do_not_get_jwt_claims_metadata(self):
        """Should not add JWT metadata to non-JWT secret matches."""

        detection = self.assert_secret_detection('AKIA1234567890ABCDEF', 'aws_access_key', 95)

        self.assertNotIn('jwt_claims', detection['matches'][0])

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

    def test_ignores_ckeditor_advanced_dialog_field_mapping(self):
        """CKEditor advanced-dialog field names should not be reported as secrets."""

        body = """
            CKEDITOR.plugins.add('link', {
                init:function(editor){
                    var m = {
                        id:"advId",
                        dir:"advLangDir",
                        accessKey:"advAccessKey",
                        name:"advName",
                        lang:"advLangCode",
                        tabindex:"advTabIndex",
                        title:"advTitle",
                        type:"advContentType",
                        "class":"advCSSClasses",
                        charset:"advCharset",
                        style:"advStyles",
                        rel:"advRel"
                    };
                }
            });
        """
        response = self.make_response(
            body=body.encode('utf-8'),
            headers={'Content-Type': 'application/javascript'},
        )

        self.assertIsNone(SecretResponsePlugin(None).process(response))
        self.assertFalse(hasattr(response, 'opendoor_secret_detection'))

    def test_still_detects_real_generic_access_key_assignment(self):
        """The CKEditor field-name allowlist must not hide real generic assignments."""

        self.assert_secret_detection(
            'accessKey:"realSecretAccessKey987654321"',
            'generic_assignment',
            70,
            headers={'Content-Type': 'application/javascript'},
        )


if __name__ == '__main__':
    unittest.main()
