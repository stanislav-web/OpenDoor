# -*- coding: utf-8 -*-

import unittest

from src.lib.browser.fingerprint import Fingerprint


class FakeConfig(object):
    """Minimal config stub for Fingerprint tests."""

    DEFAULT_SCHEME = 'http://'
    DEFAULT_HTTP_PORT = 80
    DEFAULT_SSL_PORT = 443

    def __init__(self, host='example.com', scheme='http://', port=80):
        self.host = host
        self.scheme = scheme
        self.port = port
        self._method = 'HEAD'


class FakeResponse(object):
    """Fake HTTP response object."""

    def __init__(self, status=200, data='', headers=None):
        self.status = status
        self.data = data.encode('utf-8') if isinstance(data, str) else data
        self.headers = {} if headers is None else headers


class FakeClient(object):
    """Fake request client keyed by (method, url)."""

    def __init__(self, responses):
        self.responses = responses

    def request(self, url):
        method = getattr(self, 'config_method_getter', lambda: 'HEAD')()
        return self.responses.get((method, url), FakeResponse(status=404))


class TestFingerprint(unittest.TestCase):
    """TestFingerprint class."""

    def _make_client(self, config, responses):
        client = FakeClient(responses)
        client.config_method_getter = lambda: getattr(config, '_method', 'HEAD')
        return client

    def test_detects_wordpress(self):
        """Fingerprint should detect WordPress from markup and probe signals."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="WordPress 6.8"></head>'
                '<body><link href="/wp-content/themes/test/style.css">'
                '<script src="/wp-includes/js/jquery.js"></script></body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/wp-json/'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/wp-login.php'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/xmlrpc.php'): FakeResponse(405, '', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'WordPress')
        self.assertGreaterEqual(result['confidence'], 90)

    def test_detects_nextjs(self):
        """Fingerprint should detect Next.js from __NEXT_DATA__ and _next assets."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><div id="__next"></div>'
                '<script id="__NEXT_DATA__" type="application/json">{}</script>'
                '<script src="/_next/static/chunks/main.js"></script></body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/_next/static/'): FakeResponse(403, '', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'framework')
        self.assertEqual(result['name'], 'Next.js')

    def test_detects_shopify(self):
        """Fingerprint should detect Shopify from CDN and cookie markers."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<script src="https://cdn.shopify.com/s/files/1/test.js"></script>'
                '<script>Shopify.theme = {};</script>'
                '</body></html>',
                {
                    'Set-Cookie': '_shopify_y=test; Path=/',
                    'X-ShopId': '123456'
                }
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'ecommerce')
        self.assertEqual(result['name'], 'Shopify')

    def test_detects_webflow(self):
        """Fingerprint should detect Webflow from generator and wf markers."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="Webflow"></head>'
                '<body data-wf-page="abc" data-wf-site="xyz">'
                '<link href="/css/webflow.css" rel="stylesheet"></body></html>',
                {}
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'sitebuilder')
        self.assertEqual(result['name'], 'Webflow')

    def test_detects_aws_cloudfront_as_infrastructure(self):
        """Fingerprint should detect AWS CloudFront as infrastructure."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><div id="root"></div></body></html>',
                {
                    'Server': 'CloudFront',
                    'Via': '1.1 abc.cloudfront.net (CloudFront)',
                    'X-Amz-Cf-Id': 'test',
                    'X-Amz-Cf-Pop': 'WAW50-C1',
                }
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['infrastructure']['provider'], 'AWS CloudFront')
        self.assertGreaterEqual(result['infrastructure']['confidence'], 90)

    def test_detects_cloudflare_as_infrastructure(self):
        """Fingerprint should detect Cloudflare from cf-ray and server headers."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>plain app</body></html>',
                {
                    'Server': 'cloudflare',
                    'CF-Ray': 'abc-waw',
                    'CF-Cache-Status': 'HIT',
                }
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['infrastructure']['provider'], 'Cloudflare')
        self.assertGreaterEqual(result['infrastructure']['confidence'], 90)

    def test_returns_custom_when_signal_is_too_weak(self):
        """Fingerprint should fall back to custom when no strong app signature exists."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><div id="root"></div></body></html>',
                {'Server': 'nginx'}
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')