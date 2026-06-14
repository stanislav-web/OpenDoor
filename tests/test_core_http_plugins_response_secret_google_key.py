# -*- coding: utf-8 -*-

import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response.secret import SecretResponsePlugin


class TestSecretResponsePluginGoogleApiKeyRegression(unittest.TestCase):
    """Regression tests for Google API key handling on normal and error pages."""

    def make_response(self, status=200, body=b'', headers=None):
        return HTTPResponse(
            status=status,
            body=body,
            headers=headers or {'Content-Type': 'text/html; charset=utf-8'},
        )

    def test_google_api_key_on_success_page_remains_secret(self):
        """Should keep real Google API key findings on ordinary 200 pages."""

        key = 'AIza' + ('C' * 35)
        response = self.make_response(
            body=('<script>window.mapsKey = "' + key + '";</script>').encode('utf-8'),
        )

        self.assertEqual(SecretResponsePlugin(None).process(response), 'secret')
        detection = response.opendoor_secret_detection
        self.assertEqual(detection['type'], 'google_api_key')
        self.assertEqual(detection['confidence'], 90)
        self.assertEqual(detection['redacted'], 'AIza****CCCC')

    def test_google_api_key_on_non_success_page_is_not_reported(self):
        """Should not report layout secrets from non-success error pages."""

        key = 'AIza' + ('D' * 35)
        response = self.make_response(
            status=404,
            body=('<html><body>Not found<script>"' + key + '"</script></body></html>').encode('utf-8'),
        )

        self.assertIsNone(SecretResponsePlugin(None).process(response))
        self.assertFalse(hasattr(response, 'opendoor_secret_detection'))


if __name__ == '__main__':
    unittest.main()
