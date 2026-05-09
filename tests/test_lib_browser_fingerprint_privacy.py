# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from src.lib.browser.browser import Browser
from src.lib.browser.fingerprint import Fingerprint


class TestFingerprintPrivacyRisks(unittest.TestCase):
    """Fingerprint privacy-risk detector tests."""

    def test_default_result_contains_isolated_privacy_risks(self):
        """Default fingerprint result should expose isolated privacy risk metadata."""

        first = Fingerprint._default_result()
        second = Fingerprint._default_result()

        first['privacy_risks']['supercookie']['warnings'].append('mutated')
        first['privacy_risks']['supercookie']['signals'].append('mutated-signal')

        self.assertEqual(second['privacy_risks']['supercookie']['risk'], 'none')
        self.assertEqual(second['privacy_risks']['supercookie']['warnings'], [])
        self.assertEqual(second['privacy_risks']['supercookie']['signals'], [])

    def test_detects_hsts_tracking_surface_by_subdomain_fanout_not_names(self):
        """HSTS risk should use structural subdomain fan-out instead of name patterns."""

        privacy = Fingerprint._build_privacy_risks(
            headers={},
            body=(
                '<script src="https://assets.example.com/a.js"></script>'
                '<img src="https://static.example.com/pixel.png">'
                '<link href="https://media.example.com/style.css" rel="stylesheet">'
            ),
            body_size=2048,
            final_root_url='https://www.example.com/',
            security_headers={
                'hsts': {
                    'present': True,
                    'max_age': 31536000,
                }
            },
        )

        supercookie = privacy['supercookie']

        self.assertEqual(supercookie['risk'], 'medium')
        self.assertTrue(supercookie['hsts_tracking_surface'])
        self.assertIn('first_party_subdomain_fanout:3', supercookie['signals'])
        self.assertIn('long-lived HSTS combined with first-party subdomain fan-out', supercookie['warnings'])

    def test_strong_hsts_without_subdomain_fanout_does_not_warn(self):
        """Normal long-lived HSTS should not be reported as a supercookie by itself."""

        privacy = Fingerprint._build_privacy_risks(
            headers={},
            body='<html><body>ok</body></html>',
            body_size=28,
            final_root_url='https://example.com/',
            security_headers={
                'hsts': {
                    'present': True,
                    'max_age': 31536000,
                    'include_subdomains': True,
                    'preload': True,
                }
            },
        )

        supercookie = privacy['supercookie']

        self.assertEqual(supercookie['risk'], 'none')
        self.assertFalse(supercookie['hsts_tracking_surface'])
        self.assertEqual(supercookie['warnings'], [])

    def test_detects_etag_cache_tracking_surface(self):
        """Persistent ETag and long-lived cache on a small response should be reported."""

        privacy = Fingerprint._build_privacy_risks(
            headers={
                'etag': '"abc123"',
                'cache-control': 'public, max-age=31536000, immutable',
            },
            body='ok',
            body_size=2,
            final_root_url='https://example.com/',
            security_headers={'hsts': {}},
        )

        supercookie = privacy['supercookie']

        self.assertEqual(supercookie['risk'], 'medium')
        self.assertTrue(supercookie['etag_tracking_surface'])
        self.assertTrue(supercookie['cache_tracking_surface'])
        self.assertIn('persistent ETag/cache validator with long cache lifetime', supercookie['warnings'])

    def test_detects_persistent_cookie_surface_without_medium_warning(self):
        """Long-lived cookies should be preserved as low-risk signals when isolated."""

        privacy = Fingerprint._build_privacy_risks(
            headers={
                'set-cookie': 'uid=abc; Max-Age=31536000; Path=/',
            },
            body='',
            body_size=0,
            final_root_url='https://example.com/',
            security_headers={'hsts': {}},
        )

        supercookie = privacy['supercookie']

        self.assertEqual(supercookie['risk'], 'low')
        self.assertTrue(supercookie['persistent_cookie_surface'])
        self.assertEqual(supercookie['warnings'], [])
        self.assertEqual(
            supercookie['signals'],
            ['persistent_cookie:uid:max_age=31536000:missing=httponly|samesite|secure'],
        )

    def test_browser_prints_only_medium_and_high_privacy_warnings(self):
        """Browser should emit tpl.warning only for medium/high supercookie risk buckets."""

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            Browser._Browser__print_privacy_risk_warnings({
                'privacy_risks': {
                    'supercookie': {
                        'risk': 'medium',
                        'warnings': ['persistent ETag/cache validator with long cache lifetime'],
                    }
                }
            })

        warning_mock.assert_called_once_with(
            msg='Possible supercookie tracking surface: persistent ETag/cache validator with long cache lifetime'
        )

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            Browser._Browser__print_privacy_risk_warnings({
                'privacy_risks': {
                    'supercookie': {
                        'risk': 'low',
                        'warnings': ['long-lived client cookie surface'],
                    }
                }
            })

        warning_mock.assert_not_called()


if __name__ == '__main__':
    unittest.main()
