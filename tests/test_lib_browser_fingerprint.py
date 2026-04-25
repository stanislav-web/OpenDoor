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

    def test_detects_nextcloud_from_root_and_status_probes(self):
        """Fingerprint should detect Nextcloud from root branding and status probes."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="Nextcloud"></head>'
                '<body><div class="nextcloud"></div>'
                '<img src="/apps/files/img/app.svg"><link href="/ocs-provider/"></body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/status.php'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/remote.php/dav/'): FakeResponse(401, '', {}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }
        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'Nextcloud')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_detects_nopcommerce_from_footer_and_admin_probe(self):
        """Fingerprint should detect nopCommerce from branding and admin probe."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><footer>Powered by nopCommerce</footer></body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/admin'): FakeResponse(302, '', {'Location': '/login'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }
        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'ecommerce')
        self.assertEqual(result['name'], 'nopCommerce')
        self.assertGreaterEqual(result['confidence'], 60)

    def test_detects_octobercms_from_root_cookie_and_backend_probe(self):
        """Fingerprint should detect OctoberCMS from branding, cookie and backend probe."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="OctoberCMS"></head>'
                '<body><link href="/themes/demo/assets/css/theme.css">'
                '<script src="/modules/system/assets/js/framework.js"></script>'
                '<div>October CMS</div></body></html>',
                {
                    'Set-Cookie': 'october_session=test; Path=/',
                }
            ),
            ('HEAD', 'http://example.com/backend'): FakeResponse(302, '', {'Location': '/backend/auth'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'OctoberCMS')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_detects_contao_from_generator_assets_and_backend_probe(self):
        """Fingerprint should detect Contao from generator, assets and backend probe."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="Contao Open Source CMS"></head>'
                '<body><link href="/bundles/contaocore/theme.css">'
                '<img src="/files/contao/logo.svg"><div>contao</div></body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/contao/'): FakeResponse(302, '', {'Location': '/contao/login'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'Contao')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_detects_mediawiki_from_generator_assets_and_api_probe(self):
        """Fingerprint should detect MediaWiki from generator, assets and api probe."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="MediaWiki 1.41"></head>'
                '<body><link href="/w/resources/assets/wiki.png">'
                '<div class="mw-body"><h1 class="mw-page-title-main">Main Page</h1></div>'
                '</body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/api.php'): FakeResponse(200, '', {}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'MediaWiki')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_detects_matomo_from_tracker_assets_and_cookie_markers(self):
        """Fingerprint should detect Matomo from tracker assets and cookie markers."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="Matomo"></head>'
                '<body><script>var _paq = window._paq || []; _paq.push(["trackPageView"]);</script>'
                '<script src="/matomo.js"></script>'
                '<img src="/matomo.php?idsite=1&amp;rec=1"></body></html>',
                {
                    'Set-Cookie': '_pk_id=test; Path=/',
                }
            ),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'Matomo')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_detects_bludit_from_generator_assets_and_admin_probe(self):
        """Fingerprint should detect Bludit from generator, asset paths and admin probe."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="Bludit"></head>'
                '<body><link href="/bl-themes/blog/style.css">'
                '<img src="/bl-content/uploads/logo.png"><div>bludit</div></body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/admin'): FakeResponse(302, '', {'Location': '/admin/login'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'Bludit')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_detects_boltcms_from_generator_header_and_bolt_probe(self):
        """Fingerprint should detect Bolt CMS from generator, header and backend probe."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="Bolt"></head>'
                '<body><a href="/bolt">Backend</a><div>bolt cms</div></body></html>',
                {
                    'X-Powered-By': 'Bolt',
                }
            ),
            ('HEAD', 'http://example.com/bolt'): FakeResponse(302, '', {'Location': '/bolt/login'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'Bolt CMS')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_does_not_false_positive_boltcms_from_generic_bolt_route(self):
        """Fingerprint should not misclassify a generic /bolt route as Bolt CMS."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><a href="/bolt">Backend</a></body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/bolt'): FakeResponse(302, '', {'Location': '/bolt/login'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Bolt CMS', [candidate['name'] for candidate in result['candidates']])

    def test_does_not_false_positive_directus_from_generic_admin_assets(self):
        """Fingerprint should not misclassify generic admin assets as Directus."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<script src="/admin/assets/index.js"></script>'
                '<link href="/admin/assets/index.css" rel="stylesheet">'
                '</body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/admin'): FakeResponse(302, '', {'Location': '/login'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Directus', [candidate['name'] for candidate in result['candidates']])

    def test_does_not_false_positive_shopware_from_generic_backend_theme_widgets(self):
        """Fingerprint should not misclassify generic backend/theme/widgets markup as Shopware."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<link href="/theme/frontend/default/css/all.css">'
                '<div data-url="/widgets/index/menu"></div>'
                '<meta name="csrf-token" content="x">'
                '</body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/backend'): FakeResponse(302, '', {'Location': '/login'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Shopware', [candidate['name'] for candidate in result['candidates']])

    def test_does_not_false_positive_octobercms_from_generic_theme_and_system_module_assets(self):
        """Fingerprint should not misclassify generic theme/system-module assets as OctoberCMS."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<link href="/themes/demo/assets/css/theme.css">'
                '<script src="/modules/system/assets/js/framework.js"></script>'
                '</body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/backend'): FakeResponse(302, '', {'Location': '/login'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('OctoberCMS', [candidate['name'] for candidate in result['candidates']])

    def test_does_not_false_positive_pimcore_from_generic_admin_login_and_bundles(self):
        """Fingerprint should not misclassify generic admin login plus bundles as Pimcore."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<link href="/bundles/pimcoreadmin/css/admin.css">'
                '<script src="/bundles/pimcorestatic6/js/app.js"></script>'
                '<a href="/admin/login">Admin</a>'
                '</body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/admin'): FakeResponse(302, '', {'Location': '/login'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Pimcore', [candidate['name'] for candidate in result['candidates']])

    def test_does_not_false_positive_directus_from_generic_article_and_admin_assets(self):
        """Fingerprint should not misclassify a generic directus mention plus admin assets as Directus."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<h1>How to migrate from directus to another CMS</h1>'
                '<script src="/admin/assets/index.js"></script>'
                '<link href="/admin/assets/index.css" rel="stylesheet">'
                '</body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/admin'): FakeResponse(302, '', {'Location': '/login'}),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Directus', [candidate['name'] for candidate in result['candidates']])

    def test_does_not_false_positive_craftcms_from_cookie_only(self):
        """Fingerprint should not misclassify cookie-only evidence as Craft CMS."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><div id="root"></div></body></html>',
                {
                    'Set-Cookie': 'craftsessionid=test; Path=/',
                }
            ),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Craft CMS', [candidate['name'] for candidate in result['candidates']])

    def test_does_not_false_positive_discourse_from_generic_article_and_upload_path(self):
        """Fingerprint should not misclassify a generic discourse mention and upload path as Discourse."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<h1>Discourse migration guide</h1>'
                '<img src="/uploads/default/original/1X/test.png">'
                '</body></html>',
                {}
            ),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Discourse', [candidate['name'] for candidate in result['candidates']])

    def test_does_not_false_positive_matomo_from_generic_article_and_asset_names(self):
        """Fingerprint should not misclassify a generic matomo mention and asset names as Matomo."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<h1>How to migrate from matomo</h1>'
                '<code>/matomo.js</code>'
                '<code>/matomo.php</code>'
                '</body></html>',
                {}
            ),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Matomo', [candidate['name'] for candidate in result['candidates']])

    def test_does_not_false_positive_neos_from_generic_text_and_static_packages_path(self):
        """Fingerprint should not misclassify a generic neos mention and static packages path as Neos."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<h1>Neos deployment notes</h1>'
                '<link href="/_Resources/Static/Packages/Vendor.Site/app.css">'
                '</body></html>',
                {}
            ),
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Neos', [candidate['name'] for candidate in result['candidates']])