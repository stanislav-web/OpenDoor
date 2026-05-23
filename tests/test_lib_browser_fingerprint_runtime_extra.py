# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core import HttpRequestError
from src.lib.browser.browser import Browser


class StableFingerprintFailure(object):
    """Fake fingerprint class with stable DEFAULT_RESULT for fallback testing."""

    DEFAULT_RESULT = {
        'category': 'custom',
        'name': 'Unknown custom stack',
        'confidence': 35,
        'score': 0,
        'signals': [],
        'candidates': [],
        'infrastructure': {
            'provider': 'unknown',
            'confidence': 0,
            'signals': [],
            'candidates': [],
        }
    }

    def __init__(self, config, client):
        """
        Init fake fingerprint.

        :param mixed config: config
        :param mixed client: client
        """

        self.config = config
        self.client = client

    def detect(self):
        """
        Raise a deterministic error.

        :return: None
        """

        raise HttpRequestError('boom')


class TestBrowserFingerprintRuntimeExtra(unittest.TestCase):
    """Extra Browser.fingerprint coverage."""

    def make_browser(self):
        """
        Create Browser without __init__.

        :return: Browser
        """

        return object.__new__(Browser)

    def test_fingerprint_returns_none_when_feature_is_disabled(self):
        """
        Browser.fingerprint() should do nothing when the flag is disabled.

        :return: None
        """

        browser = self.make_browser()
        setattr(browser, '_Browser__config', SimpleNamespace(is_fingerprint=False))
        self.assertIsNone(browser.fingerprint())

    def test_fingerprint_collects_result_and_logs_evidence(self):
        """
        Browser.fingerprint() should save the result and log evidence.

        :return: None
        """

        browser = self.make_browser()
        setattr(browser, '_Browser__config', SimpleNamespace(is_fingerprint=True, host='example.com'))
        setattr(browser, '_Browser__client', 'client')
        setattr(browser, '_Browser__result', {})

        fingerprint_result = {
            'category': 'framework',
            'name': 'Next.js',
            'confidence': 96,
            'signals': [
                {'type': 'asset', 'value': '/_next/static/', 'weight': 7},
                {'type': 'script', 'value': '__NEXT_DATA__', 'weight': 7},
            ],
            'runtime': {'name': 'Node.js', 'confidence': 95},
            'infrastructure': {'provider': 'Vercel', 'confidence': 98},
            'security_headers': {
                'hsts': {'grade': 'strong'},
            },
        }

        fingerprint_instance = MagicMock()
        fingerprint_instance.detect.return_value = fingerprint_result

        with patch('src.lib.browser.browser.Fingerprint', return_value=fingerprint_instance), \
                patch('src.lib.browser.browser.tpl.info') as info_mock:
            result = browser.fingerprint()

        self.assertEqual(result, fingerprint_result)
        self.assertEqual(getattr(browser, '_Browser__result')['fingerprint'], fingerprint_result)
        messages = [call.kwargs.get('msg') for call in info_mock.call_args_list]
        self.assertIn('Web stack: Next.js | Node.js | Vercel', messages)
        self.assertIn('Security posture: HSTS strong', messages)
        self.assertGreaterEqual(info_mock.call_count, 4)

    def test_fingerprint_evidence_output_deduplicates_values_only(self):
        """
        Browser.fingerprint() should not repeat identical evidence values in stdout.

        :return: None
        """

        browser = self.make_browser()
        setattr(browser, '_Browser__config', SimpleNamespace(is_fingerprint=True, host='example.com'))
        setattr(browser, '_Browser__client', 'client')
        setattr(browser, '_Browser__result', {})

        fingerprint_result = {
            'category': 'cms',
            'name': 'WordPress',
            'confidence': 98,
            'signals': [
                {'type': 'markup', 'value': '/wp-content/', 'weight': 6},
                {'type': 'markup', 'value': '/wp-includes/', 'weight': 5},
                {'type': 'endpoint', 'value': '/wp-content/', 'weight': 6},
                {'type': 'endpoint', 'value': '/wp-includes/', 'weight': 5},
                {'type': 'endpoint', 'value': '/wp-json/', 'weight': 5},
            ],
            'runtime': {'name': 'PHP', 'confidence': 90},
            'infrastructure': {'provider': 'Apache HTTP Server', 'confidence': 90},
            'security_headers': {},
        }

        fingerprint_instance = MagicMock()
        fingerprint_instance.detect.return_value = fingerprint_result

        with patch('src.lib.browser.browser.Fingerprint', return_value=fingerprint_instance), \
                patch('src.lib.browser.browser.tpl.info') as info_mock:
            result = browser.fingerprint()

        self.assertEqual(result['signals'], fingerprint_result['signals'])
        messages = [call.kwargs.get('msg') for call in info_mock.call_args_list]
        self.assertIn('Fingerprint evidence: /wp-content/, /wp-includes/, /wp-json/', messages)
        self.assertNotIn(
            'Fingerprint evidence: /wp-content/, /wp-includes/, /wp-content/, /wp-includes/',
            messages,
        )

    def test_fingerprint_starts_request_provider_when_client_is_missing(self):
        """
        Browser.fingerprint() should initialize the request provider lazily.

        :return: None
        """

        browser = self.make_browser()
        setattr(browser, '_Browser__config', SimpleNamespace(is_fingerprint=True, host='example.com'))
        setattr(browser, '_Browser__client', None)
        setattr(browser, '_Browser__result', {})

        def provider():
            """
            Fake provider initializer.

            :return: None
            """

            setattr(browser, '_Browser__client', 'bootstrapped-client')

        setattr(browser, '_Browser__start_request_provider', provider)

        fingerprint_instance = MagicMock()
        fingerprint_instance.detect.return_value = {
            'category': 'cms',
            'name': 'WordPress',
            'confidence': 95,
            'signals': [],
            'infrastructure': {'provider': 'AWS CloudFront', 'confidence': 98},
        }

        with patch('src.lib.browser.browser.Fingerprint', return_value=fingerprint_instance):
            result = browser.fingerprint()

        self.assertEqual(result['name'], 'WordPress')
        self.assertEqual(getattr(browser, '_Browser__client'), 'bootstrapped-client')

    def test_fingerprint_falls_back_to_default_result_on_error(self):
        """
        Browser.fingerprint() should return DEFAULT_RESULT on provider failures.

        :return: None
        """

        browser = self.make_browser()
        setattr(browser, '_Browser__config', SimpleNamespace(is_fingerprint=True, host='example.com'))
        setattr(browser, '_Browser__client', 'client')
        setattr(browser, '_Browser__result', {})

        with patch('src.lib.browser.browser.Fingerprint', StableFingerprintFailure), \
                patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            result = browser.fingerprint()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['infrastructure']['provider'], 'unknown')
        warning_mock.assert_called_once()
