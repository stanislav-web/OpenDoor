# -*- coding: utf-8 -*-

import unittest

from src.lib.browser.fingerprint import Fingerprint


class _FingerprintConfig(object):
    """Minimal browser config for isolated Rails fingerprint tests."""

    DEFAULT_SCHEME = 'http://'
    DEFAULT_HTTP_PORT = 80
    DEFAULT_SSL_PORT = 443

    scheme = 'https://'
    host = 'example.com'
    port = 443
    prefix = ''
    _method = 'HEAD'


class _Response(object):
    """Small HTTP response stub used by the fingerprint detector."""

    def __init__(self, status=200, headers=None, data=b''):
        """
        Initialize a deterministic response object.

        :param int status: HTTP status code
        :param dict|None headers: response headers
        :param bytes data: response body
        :return: None
        """

        self.status = status
        self.headers = headers or {}
        self.data = data


class _Client(object):
    """Static client returning root and generic 404 responses."""

    def __init__(self, root_body='', root_headers=None, not_found_body='not found'):
        """
        Initialize the client fixture.

        :param str root_body: body returned for the target root URL
        :param dict|None root_headers: headers returned for the target root URL
        :param str not_found_body: body returned for non-root probes
        :return: None
        """

        self.root_body = root_body
        self.root_headers = root_headers or {}
        self.not_found_body = not_found_body

    def request(self, url):
        """
        Return root response or neutral 404 for probes.

        :param str url: requested URL
        :return: response stub
        :rtype: _Response
        """

        if str(url) == 'https://example.com/':
            return _Response(status=200, headers=self.root_headers, data=self.root_body.encode('utf-8'))

        return _Response(status=404, headers={'Server': 'nginx'}, data=self.not_found_body.encode('utf-8'))


class FingerprintRailsTestCase(unittest.TestCase):
    """Regression tests for conservative passive Ruby on Rails fingerprinting."""

    def _detect(self, root_body='', root_headers=None, not_found_body='not found'):
        """
        Run fingerprint detector against a deterministic client fixture.

        :param str root_body: root response body
        :param dict|None root_headers: root response headers
        :param str not_found_body: 404 probe response body
        :return: fingerprint result
        :rtype: dict
        """

        return Fingerprint(
            _FingerprintConfig(),
            _Client(root_body=root_body, root_headers=root_headers, not_found_body=not_found_body),
        ).detect()

    def test_keeps_rails_session_cookie_detection(self):
        result = self._detect(root_headers={'Set-Cookie': '_rails_session=abc; path=/; HttpOnly'})

        self.assertEqual('Ruby on Rails', result['name'])
        self.assertEqual('Ruby', result['runtime']['name'])

    def test_detects_exact_rails_csrf_meta(self):
        body = '''
            <html><head>
              <meta name="csrf-param" content="authenticity_token">
              <meta name="csrf-token" content="token-value">
            </head><body>hello</body></html>
        '''

        result = self._detect(root_body=body)

        self.assertEqual('Ruby on Rails', result['name'])
        self.assertIn('csrf-param=authenticity_token|csrf-token', [item['value'] for item in result['signals']])

    def test_keeps_generic_csrf_pair_as_low_confidence_rails_candidate(self):
        body = '''
            <html><head>
              <meta name="csrf-param" content="csrf_token">
              <meta name="csrf-token" content="token-value">
            </head><body>hello</body></html>
        '''
        fingerprint = Fingerprint(None, None)

        fingerprint._apply_detection_rules(
            body=body,
            body_lower=body.lower(),
            headers={},
            cookies=[],
            generator='',
            probe_statuses={},
            final_root_url='https://example.test/',
            not_found_status=404,
            not_found_body='not found',
            not_found_headers={},
        )

        signals = getattr(fingerprint, '_Fingerprint__signals')['Ruby on Rails']
        self.assertIn(
            {'type': 'markup', 'value': 'csrf-param|csrf-token', 'weight': 5.0},
            signals,
        )

    def test_detects_rails_ujs_only_with_csrf_corroboration(self):
        body = '''
            <meta name="csrf-param" content="authenticity_token">
            <meta name="csrf-token" content="token-value">
            <script src="/assets/rails-ujs.js"></script>
        '''

        result = self._detect(root_body=body)

        self.assertEqual('Ruby on Rails', result['name'])
        self.assertIn('rails-ujs|turbo-rails', [item['value'] for item in result['signals']])

    def test_detects_rails_asset_pipeline_only_with_corroboration(self):
        body = '''
            <meta name="csrf-param" content="authenticity_token">
            <meta name="csrf-token" content="token-value">
            <script src="/assets/application-4f7b2a9c1d.js"></script>
        '''

        result = self._detect(root_body=body)

        self.assertEqual('Ruby on Rails', result['name'])
        self.assertIn('rails application asset', [item['value'] for item in result['signals']])

    def test_detects_rails_exception_marker_from_root_body(self):
        result = self._detect(root_body='<h1>ActionController::RoutingError</h1><pre>Rails.root</pre>')

        self.assertEqual('Ruby on Rails', result['name'])
        self.assertIn('Rails exception marker', [item['value'] for item in result['signals']])

    def test_detects_rails_exception_marker_from_not_found_body(self):
        result = self._detect(not_found_body='<h1>ActionView::Template::Error</h1><pre>Rails.root</pre>')

        self.assertEqual('Ruby on Rails', result['name'])
        self.assertIn('Rails exception marker', [item['value'] for item in result['signals']])

    def test_does_not_detect_rails_from_rack_or_passenger_headers_alone(self):
        result = self._detect(root_headers={'X-Runtime': '0.042', 'Server': 'Phusion Passenger'})

        self.assertNotEqual('Ruby on Rails', result['name'])

    def test_does_not_detect_rails_from_ujs_or_assets_alone(self):
        body = '''
            <script src="/assets/rails-ujs.js"></script>
            <script src="/assets/application-4f7b2a9c1d.js"></script>
            <a data-method="delete" data-remote="true" href="/account">Delete</a>
        '''

        result = self._detect(root_body=body)

        self.assertNotEqual('Ruby on Rails', result['name'])


if __name__ == '__main__':
    unittest.main()
