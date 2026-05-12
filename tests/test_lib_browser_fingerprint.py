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

    def test_should_use_neutral_not_found_probe_path(self):
        """Fingerprint 404-baseline probe path should not expose a branded scanner marker."""

        probe_path = Fingerprint.NOT_FOUND_PROBE_PATH.lower()

        self.assertNotIn('opendoor', probe_path)
        self.assertTrue(probe_path.startswith('/.well-known/'))
        self.assertTrue(probe_path.endswith('.txt'))


    def test_default_result_returns_isolated_nested_state(self):
        """Fingerprint default fallback should not share nested mutable state."""

        first = Fingerprint._default_result()
        second = Fingerprint._default_result()

        first['security_headers']['hsts']['warnings'].append('mutated')
        first['runtime']['signals'].append('runtime-mutated')
        first['infrastructure']['candidates'].append({'name': 'infra-mutated'})

        self.assertNotIn('mutated', second['security_headers']['hsts']['warnings'])
        self.assertNotIn('runtime-mutated', second['runtime']['signals'])
        self.assertEqual(second['infrastructure']['candidates'], [])

    def test_detect_returns_isolated_default_when_root_response_is_missing(self):
        """Fingerprint root-miss fallback should not mutate DEFAULT_RESULT."""

        config = FakeConfig()
        detector = Fingerprint(config=config, client=self._make_client(config, {}))
        result = detector.detect()

        result['security_headers']['hsts']['warnings'].append('mutated')

        self.assertNotIn('mutated', Fingerprint.DEFAULT_RESULT['security_headers']['hsts']['warnings'])

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

    def test_detects_mobirise_from_generator_and_assets(self):
        """Fingerprint should detect Mobirise landing-page builder output."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="Mobirise Website Builder v5.9.18">'
                '<link rel="stylesheet" href="assets/web/assets/mobirise-icons/mobirise-icons.css">'
                '<link rel="stylesheet" href="assets/mobirise/css/mbr-additional.css"></head>'
                '<body><section class="mbr-section-title mbr-fonts-style">Landing</section>'
                '<div class="mbr-section-btn"></div></body></html>',
                {}
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'sitebuilder')
        self.assertEqual(result['name'], 'Mobirise')
        self.assertGreaterEqual(result['confidence'], 80)

    def test_does_not_detect_mobirise_from_plain_text_only(self):
        """Fingerprint should not classify pages that only mention Mobirise as text."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><p>We can rebuild landing pages made with Mobirise.</p></body></html>',
                {}
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')

    def test_detects_5145_regional_cms_and_sitebuilder_catalog(self):
        """Fingerprint should detect regional CMS and site-builder catalog additions."""

        cases = [
            (
                'InstantCMS',
                'cms',
                '<html><head><meta name="generator" content="InstantCMS"></head>'
                '<body><script src="/templates/default/js/icms.js"></script></body></html>',
                {},
            ),
            (
                'Duda',
                'sitebuilder',
                '<html><head><meta name="generator" content="Duda"></head>'
                '<body><script src="https://static-cdn.multiscreensite.com/site.js"></script>'
                '<div data-cmsid="abc"></div></body></html>',
                {},
            ),
            (
                'Hostinger Website Builder',
                'sitebuilder',
                '<html><head><meta name="generator" content="Hostinger Website Builder"></head>'
                '<body><script src="https://assets.zyrosite.com/app.js"></script></body></html>',
                {},
            ),
            (
                'CMS.S3 / Megagroup',
                'cms',
                '<html><head><meta name="generator" content="CMS.S3"></head>'
                '<body><footer>Создание сайта — Мегагрупп.ру</footer>'
                '<a href="https://megagroup.ru">Логотип Мегагрупп</a></body></html>',
                {},
            ),
            (
                'Webasyst / Shop-Script',
                'ecommerce',
                '<html><head><meta name="generator" content="Webasyst"></head>'
                '<body><script src="/wa-apps/shop/js/shop-script.js"></script>'
                '<link href="/wa-content/css/site.css"></body></html>',
                {'Set-Cookie': 'shop-script=1; Path=/'},
            ),
            (
                'Discuz!',
                'cms',
                '<html><head><meta name="generator" content="Discuz!"></head>'
                '<body><script>var discuz_uid = 1;</script>'
                '<img src="static/image/common/logo.png"></body></html>',
                {'Set-Cookie': 'discuz_test=1; Path=/'},
            ),
            (
                'NetCat',
                'cms',
                '<html><head><meta name="generator" content="NetCat CMS"></head>'
                '<body><script src="/netcat/modules/default.js"></script>'
                '<div class="netcat_template"></div></body></html>',
                {},
            ),
        ]

        for expected_name, expected_category, body, headers in cases:
            with self.subTest(expected_name=expected_name):
                config = FakeConfig()
                base = 'http://example.com/'
                responses = {
                    ('GET', base): FakeResponse(200, body, headers),
                    ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
                }

                detector = Fingerprint(config=config, client=self._make_client(config, responses))
                result = detector.detect()

                self.assertEqual(result['category'], expected_category)
                self.assertEqual(result['name'], expected_name)
                self.assertGreaterEqual(result['confidence'], 70)

    def test_detects_5145_infrastructure_catalog_additions(self):
        """Fingerprint should detect strong HTTP-visible infrastructure additions."""

        cases = [
            (
                'Hostinger',
                {
                    'Server': 'hcdn',
                    'X-Hcdn-Cache-Status': 'HIT',
                    'Platform': 'hostinger',
                },
            ),
            (
                'DDoS-Guard',
                {
                    'Server': 'ddos-guard',
                    'X-DDoS-Guard-Request-Id': 'abc',
                },
            ),
            (
                'Tencent Cloud',
                {
                    'Server': 'tencent-cos',
                    'X-Cos-Request-Id': 'abc',
                    'X-Cos-Hash-Crc64ecma': '123',
                },
            ),
        ]

        for expected_provider, headers in cases:
            with self.subTest(expected_provider=expected_provider):
                config = FakeConfig()
                base = 'http://example.com/'
                responses = {
                    ('GET', base): FakeResponse(200, '<html><body>plain app</body></html>', headers),
                    ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
                }

                detector = Fingerprint(config=config, client=self._make_client(config, responses))
                result = detector.detect()

                self.assertEqual(result['category'], 'custom')
                self.assertEqual(result['infrastructure']['provider'], expected_provider)
                self.assertGreaterEqual(result['infrastructure']['confidence'], 70)

    def test_detects_server_header_infrastructure_without_overwriting_runtime(self):
        """Fingerprint should keep server software in infrastructure and PHP in runtime."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><a href="/contacts.php">Contacts</a></body></html>',
                {
                    'Server': 'nginx/1.20.2',
                    'X-Powered-By': 'PHP/5.3.27',
                },
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['runtime']['name'], 'PHP')
        self.assertEqual(result['infrastructure']['provider'], 'Nginx')
        self.assertGreaterEqual(result['infrastructure']['confidence'], 70)
        self.assertIn('nginx/1.20.2', result['infrastructure']['signals'][0]['value'])

    def test_detects_server_header_infrastructure_catalog(self):
        """Fingerprint should detect common HTTP Server header infrastructure engines."""

        cases = [
            ('Apache HTTP Server', 'Apache/2.4.58'),
            ('Microsoft IIS', 'Microsoft-IIS/10.0'),
            ('Caddy', 'Caddy'),
            ('LiteSpeed', 'LiteSpeed'),
            ('lighttpd', 'lighttpd/1.4.73'),
            ('Tornado', 'TornadoServer/6.4'),
            ('Gunicorn', 'gunicorn'),
            ('Uvicorn', 'uvicorn'),
            ('Hypercorn', 'hypercorn'),
            ('Waitress', 'waitress'),
            ('Apache Tomcat', 'Apache-Coyote/1.1'),
            ('Eclipse Jetty', 'Jetty'),
            ('Envoy', 'envoy'),
            ('Traefik', 'traefik'),
        ]

        for expected_provider, server_header in cases:
            with self.subTest(server_header=server_header):
                config = FakeConfig()
                base = 'http://example.com/'
                responses = {
                    ('GET', base): FakeResponse(
                        200,
                        '<html><body>plain app</body></html>',
                        {'Server': server_header},
                    ),
                    ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
                }

                detector = Fingerprint(config=config, client=self._make_client(config, responses))
                result = detector.detect()

                self.assertEqual(result['category'], 'custom')
                self.assertEqual(result['infrastructure']['provider'], expected_provider)
                self.assertGreaterEqual(result['infrastructure']['confidence'], 70)

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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Bolt CMS', [candidate['name'] for candidate in result['candidates']])

    def test_detects_bitrix_from_x_powered_cms_header(self):
        """Fingerprint should detect Bitrix from X-Powered-CMS header."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>ok</body></html>',
                {'X-Powered-CMS': 'Bitrix Site Manager (084338cf6147abbfca438bf6bb2b3337)'}
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'Bitrix')
        self.assertGreaterEqual(result['confidence'], 70)
        self.assertIn('PHP', result['runtime']['name'])

    def test_does_not_false_positive_strapi_from_generic_admin_and_uploads_routes(self):
        """Fingerprint should not classify generic /admin and /uploads routes as Strapi."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><a href="/admin">Admin</a><img src="/uploads/logo.png"></body></html>',
                {}
            ),
            ('HEAD', 'http://example.com/admin/init'): FakeResponse(404, 'Not Found', {}),
            ('HEAD', 'http://example.com/admin'): FakeResponse(302, '', {'Location': '/login'}),
            ('HEAD', 'http://example.com/uploads/'): FakeResponse(200, '', {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Strapi', [candidate['name'] for candidate in result['candidates']])

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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
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
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('Neos', [candidate['name'] for candidate in result['candidates']])

    def test_should_restore_request_method_after_request_call(self):
        """Fingerprint._request() should restore original config method after request."""

        config = FakeConfig()
        client = self._make_client(config, {
            ('GET', 'http://example.com/'): FakeResponse(200, 'ok', {}),
        })

        detector = Fingerprint(config=config, client=client)

        actual = detector._request('http://example.com/', method='GET')

        self.assertEqual(actual.status, 200)
        self.assertEqual(config._method, 'HEAD')

    def test_should_follow_redirects_stop_after_max_hops(self):
        """Fingerprint._follow_redirects() should stop after max_hops is reached."""

        config = FakeConfig()
        client = self._make_client(config, {
            ('GET', 'http://example.com/next'): FakeResponse(
                302,
                '',
                {'Location': '/final'}
            ),
        })

        detector = Fingerprint(config=config, client=client)

        response = FakeResponse(
            302,
            '',
            {'Location': '/next'}
        )

        actual_response, actual_url = detector._follow_redirects(
            response,
            'http://example.com/',
            method='GET',
            max_hops=1
        )

        self.assertEqual(actual_response.status, 302)
        self.assertEqual(actual_url, 'http://example.com/next')

    def test_should_follow_redirects_stop_when_location_header_is_missing(self):
        """Fingerprint._follow_redirects() should stop when redirect has no Location header."""

        config = FakeConfig()
        detector = Fingerprint(config=config, client=self._make_client(config, {}))

        response = FakeResponse(302, '', {})

        actual_response, actual_url = detector._follow_redirects(
            response,
            'http://example.com/',
            method='GET'
        )

        self.assertIs(actual_response, response)
        self.assertEqual(actual_url, 'http://example.com/')

    def test_should_follow_redirects_stop_when_next_response_is_none(self):
        """Fingerprint._follow_redirects() should stop when redirected request returns None."""

        class NoneClient(object):
            def request(self, _url):
                return None

        config = FakeConfig()
        detector = Fingerprint(config=config, client=NoneClient())

        response = FakeResponse(
            302,
            '',
            {'Location': '/login'}
        )

        actual_response, actual_url = detector._follow_redirects(
            response,
            'http://example.com/',
            method='GET'
        )

        self.assertIsNone(actual_response)
        self.assertEqual(actual_url, 'http://example.com/login')

    def test_should_extract_headers_return_empty_dict_for_unsupported_headers_object(self):
        """Fingerprint._extract_headers() should return empty dict for unsupported headers object."""

        config = FakeConfig()
        detector = Fingerprint(config=config, client=self._make_client(config, {}))

        response = FakeResponse(200, 'ok', object())

        actual = detector._extract_headers(response)

        self.assertEqual(actual, {})

    def test_should_extract_body_return_empty_string_for_none_body(self):
        """Fingerprint._extract_body() should return empty string for None body."""

        response = FakeResponse(200, None, {})

        actual = Fingerprint._extract_body(response)

        self.assertEqual(actual, '')

    def test_should_extract_body_stringify_non_bytes_body(self):
        """Fingerprint._extract_body() should stringify non-bytes body."""

        response = FakeResponse(200, '', {})
        response.data = {'ok': True}

        actual = Fingerprint._extract_body(response)

        self.assertEqual(actual, "{'ok': True}")

    def test_should_extract_cookies_return_empty_list_when_getlist_fails(self):
        """Fingerprint._extract_cookies() should return empty list when getlist raises."""

        class BrokenHeaders(object):
            def getlist(self, _name):
                raise RuntimeError('broken headers')

        config = FakeConfig()
        detector = Fingerprint(config=config, client=self._make_client(config, {}))

        response = FakeResponse(200, 'ok', BrokenHeaders())

        actual = detector._extract_cookies(response)

        self.assertEqual(actual, [])

    def test_should_extract_cookies_skip_invalid_cookie_pairs(self):
        """Fingerprint._extract_cookies() should skip invalid and empty cookie pairs."""

        config = FakeConfig()
        detector = Fingerprint(config=config, client=self._make_client(config, {}))

        response = FakeResponse(
            200,
            'ok',
            {
                'Set-Cookie': 'valid=1; Path=/',
                'set-cookie': '=bad; Path=/',
                'X-Test': 'ignored=1',
            }
        )

        actual = detector._extract_cookies(response)

        self.assertEqual(actual, ['valid'])

    def test_should_extract_generator_return_empty_string_without_generator_meta(self):
        """Fingerprint._extract_generator() should return empty string without generator meta."""

        actual = Fingerprint._extract_generator('<html><body>ok</body></html>')

        self.assertEqual(actual, '')

    def test_should_probe_endpoints_ignore_none_and_response_without_status(self):
        """Fingerprint._probe_endpoints() should ignore None responses and responses without status."""

        class MixedClient(object):
            def __init__(self):
                self.index = 0

            def request(self, _url):
                self.index += 1
                if self.index == 1:
                    return None
                if self.index == 2:
                    return object()
                return FakeResponse(403, '', {})

        config = FakeConfig()
        detector = Fingerprint(config=config, client=MixedClient())

        original_probes = Fingerprint.PROBES
        try:
            Fingerprint.PROBES = ('/first', '/second', '/third')
            actual = detector._probe_endpoints('http://example.com/')
        finally:
            Fingerprint.PROBES = original_probes

        self.assertEqual(actual, {'/third': 403})

    def test_should_probe_not_found_signature_return_empty_when_probe_returns_none(self):
        """Fingerprint._probe_not_found_signature() should return empty signature when probe fails."""

        class NoneClient(object):
            def request(self, _url):
                return None

        config = FakeConfig()
        detector = Fingerprint(config=config, client=NoneClient())

        actual = detector._probe_not_found_signature('http://example.com/')

        self.assertEqual(actual, (0, '', {}))

    def test_should_probe_not_found_signature_return_empty_when_redirect_chain_returns_none(self):
        """Fingerprint._probe_not_found_signature() should return empty signature when redirects fail."""

        config = FakeConfig()
        detector = Fingerprint(
            config=config,
            client=self._make_client(config, {
                ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                    302,
                    '',
                    {'Location': '/404'}
                ),
            })
        )

        original_follow_redirects = detector._follow_redirects
        try:
            detector._follow_redirects = lambda *_args, **_kwargs: (None, 'http://example.com/404')
            actual = detector._probe_not_found_signature('http://example.com/')
        finally:
            detector._follow_redirects = original_follow_redirects

        self.assertEqual(actual, (0, '', {}))

    def test_should_probe_not_found_signature_return_status_body_and_headers(self):
        """Fingerprint._probe_not_found_signature() should return status, body and headers."""

        config = FakeConfig()
        detector = Fingerprint(
            config=config,
            client=self._make_client(config, {
                ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                    404,
                    'Cannot GET /.missing',
                    {'X-Powered-By': 'Express', 'Server': 'nginx'}
                ),
            })
        )

        actual = detector._probe_not_found_signature('http://example.com/')

        self.assertEqual(actual[0], 404)
        self.assertEqual(actual[1], 'Cannot GET /.missing')
        self.assertEqual(actual[2], {
            'x-powered-by': 'Express',
            'server': 'nginx',
        })

    def test_should_apply_detection_rules_for_remaining_cms_meta_and_markup_branches(self):
        """Fingerprint._apply_detection_rules() should cover remaining CMS meta and markup branches."""

        config = FakeConfig()
        detector = Fingerprint(config=config, client=self._make_client(config, {}))

        body_lower = (
            'concrete cms gravcms '
            '/themes/pmahomme/ pma_navigation name="pma_username" '
            '/styles/prosilver/ viewtopic.php '
            'umbraco.sys.servervariables /umbraco/assets/ umb-app '
            'powered by nopcommerce '
            'pkp_structure_main pkp_page_index /plugins/themes/default /lib/pkp/ '
            '<title>directus</title> /admin/assets/index.js'
        )

        detector._apply_detection_rules(
            body='',
            body_lower=body_lower,
            headers={},
            cookies=[
                'pma_lang',
                'phpbb3_sid',
            ],
            generator='phpMyAdmin phpBB Umbraco nopCommerce Directus',
            probe_statuses={
                '/umbraco/': 200,
                '/admin': 200,
                '/api.php': 200,
                '/index.php/index/login': 200,
            },
            final_root_url='http://example.com/',
            not_found_status=0,
            not_found_body='',
            not_found_headers={},
        )

        candidates = detector._build_candidates()
        names = [candidate['name'] for candidate in candidates]

        self.assertIn('phpMyAdmin', names)
        self.assertIn('phpBB', names)
        self.assertIn('Umbraco', names)
        self.assertIn('nopCommerce', names)
        self.assertIn('Concrete CMS', names)
        self.assertIn('GravCMS', names)
        self.assertIn('Open Journal Systems', names)
        self.assertIn('Directus', names)

    def test_should_build_infrastructure_result_without_candidates(self):
        """Fingerprint._build_infrastructure_result() should return unknown infrastructure without candidates."""

        config = FakeConfig()
        detector = Fingerprint(config=config, client=self._make_client(config, {}))

        actual = detector._build_infrastructure_result([])

        self.assertEqual(actual, {
            'provider': 'unknown',
            'confidence': 0,
            'signals': [],
            'candidates': [],
        })

    def test_should_build_infrastructure_result_with_second_score_gap(self):
        """Fingerprint._build_infrastructure_result() should calculate confidence from score gap."""

        config = FakeConfig()
        detector = Fingerprint(config=config, client=self._make_client(config, {}))

        detector._add_infrastructure_signal('Cloudflare', 'header', 'cf-ray', 9)
        detector._add_infrastructure_signal('Fastly', 'header', 'x-fastly-request-id', 7)

        candidates = detector._build_infrastructure_candidates()
        actual = detector._build_infrastructure_result(candidates)

        self.assertEqual(actual['provider'], 'Cloudflare')
        self.assertGreater(actual['confidence'], 35)
        self.assertEqual(actual['signals'][0]['value'], 'cf-ray')
        self.assertEqual(actual['candidates'][:2], candidates[:2])


    def test_should_detect_runtime_stack_metadata(self):
        """Fingerprint.detect() should expose runtime stack metadata."""
        cases = [
            ('WordPress', 'PHP', {'X-Powered-By': 'PHP/8.3', 'Set-Cookie': 'PHPSESSID=abc; Path=/'}, '<meta name="generator" content="WordPress"><link href="/wp-content/x.css">'),
            ('Express', 'Node.js', {'X-Powered-By': 'Express', 'Set-Cookie': 'connect.sid=abc; Path=/'}, '<html>api</html>'),
            ('ASP.NET', '.NET', {'X-Powered-By': 'ASP.NET', 'X-AspNet-Version': '4.0', 'Set-Cookie': 'ASP.NET_SessionId=abc; Path=/'}, '<input name="__VIEWSTATE" value="x">'),
        ]
        for expected_name, expected_runtime, headers, body in cases:
            config = FakeConfig()
            base = 'http://example.com/'
            responses = {('GET', base): FakeResponse(200, body, headers), ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Cannot GET /.well-known/missing-resource.txt', headers)}
            result = Fingerprint(config=config, client=self._make_client(config, responses)).detect()
            self.assertEqual(result['name'], expected_name)
            self.assertEqual(result['runtime']['name'], expected_runtime)

    def test_should_prefer_php_route_marker_over_endpoint_only_node_hint(self):
        """Fingerprint should not infer Node.js runtime from weak endpoint-only hints."""

        config = FakeConfig(host='soldatru.ru')
        base = 'http://soldatru.ru/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><a href="/read.php?tid=945">article</a></body></html>',
                {},
            ),
            ('HEAD', 'http://soldatru.ru/swagger'): FakeResponse(403, '', {}),
            ('GET', 'http://soldatru.ru{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                '<html><body>regular missing page</body></html>',
                {},
            ),
        }

        result = Fingerprint(config=config, client=self._make_client(config, responses)).detect()

        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertEqual(result['runtime']['name'], 'PHP')
        self.assertEqual(result['runtime']['signals'][0]['type'], 'route')

    def test_should_keep_node_runtime_when_strong_node_signals_exist(self):
        """Fingerprint should keep Node.js runtime when explicit Node markers are present."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><a href="/legacy.php">legacy</a></body></html>',
                {'X-Powered-By': 'Express', 'Set-Cookie': 'connect.sid=abc; Path=/'},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                '<pre>Cannot GET /.well-known/missing-resource.txt</pre>',
                {'X-Powered-By': 'Express'},
            ),
        }

        result = Fingerprint(config=config, client=self._make_client(config, responses)).detect()

        self.assertEqual(result['name'], 'Express')
        self.assertEqual(result['runtime']['name'], 'Node.js')

    def test_should_not_infer_node_runtime_from_generic_cannot_get_text(self):
        """Fingerprint should ignore non-canonical long pages mentioning Cannot GET."""

        config = FakeConfig()
        base = 'http://example.com/'
        generic_body = '<html><body>' + ('content ' * 220) + 'Cannot GET /example' + '</body></html>'
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                generic_body,
                {},
            ),
        }

        result = Fingerprint(config=config, client=self._make_client(config, responses)).detect()

        self.assertEqual(result['runtime']['name'], 'unknown')

    def test_should_build_runtime_result_without_candidates(self):
        """Fingerprint._build_runtime_result() should return unknown runtime without candidates."""
        detector = Fingerprint(config=FakeConfig(), client=self._make_client(FakeConfig(), {}))
        self.assertEqual(detector._build_runtime_result([]), {'name': 'unknown', 'category': 'runtime', 'confidence': 0, 'signals': [], 'candidates': []})

    def test_should_calculate_confidence_with_lower_and_upper_caps(self):
        """Fingerprint._calculate_confidence() should clamp confidence to 35..98."""

        self.assertEqual(Fingerprint._calculate_confidence(0, 0), 35)
        self.assertEqual(Fingerprint._calculate_confidence(100, 100), 98)


    def test_should_build_base_url_with_custom_port(self):
        """Fingerprint._build_base_url() should include non-default ports."""

        config = FakeConfig(scheme='https://', port=8443)
        detector = Fingerprint(config=config, client=self._make_client(config, {}))

        self.assertEqual(detector._build_base_url(), 'https://example.com:8443/')

    def test_should_extract_cookies_skip_header_without_name_value_pair(self):
        """Fingerprint._extract_cookies() should skip Set-Cookie headers without name/value separator."""

        config = FakeConfig()
        detector = Fingerprint(config=config, client=self._make_client(config, {}))
        response = FakeResponse(200, 'ok', {'Set-Cookie': 'HttpOnly; Path=/'})

        self.assertEqual(detector._extract_cookies(response), [])

    def test_should_apply_extended_header_signature_match_and_mismatch(self):
        """Fingerprint extended header rules should cover required header value matching."""

        mismatch = Fingerprint(config=FakeConfig(), client=self._make_client(FakeConfig(), {}))
        mismatch._apply_extended_cms_catalog_rules(
            body_lower='',
            headers={'x-generator': 'drupal'},
            cookies=[],
            generator='',
        )
        self.assertNotIn('Sitecore', [candidate['name'] for candidate in mismatch._build_candidates()])

        matched = Fingerprint(config=FakeConfig(), client=self._make_client(FakeConfig(), {}))
        matched._apply_extended_cms_catalog_rules(
            body_lower='',
            headers={'x-generator': 'sitecore xp'},
            cookies=[],
            generator='',
        )
        self.assertIn('Sitecore', [candidate['name'] for candidate in matched._build_candidates()])


    def test_should_ignore_progress_callback_errors(self):
        """Fingerprint._emit_progress() should ignore callback type errors."""

        def broken_callback(_current, _total, _label):
            raise TypeError('bad callback')

        detector = Fingerprint(
            config=FakeConfig(),
            client=self._make_client(FakeConfig(), {}),
            progress_callback=broken_callback,
        )

        self.assertIsNone(detector._emit_progress(1, 2, 'root'))

    def test_should_return_default_when_root_request_fails_with_progress_callback(self):
        """Fingerprint.detect() should finish progress and return default on missing root response."""

        events = []
        class NoneClient(object):
            def request(self, _url):
                return None

        config = FakeConfig()
        detector = Fingerprint(
            config=config,
            client=NoneClient(),
            progress_callback=lambda current, total, label: events.append((current, total, label)),
        )

        result = detector.detect()

        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertEqual(result['runtime']['name'], 'unknown')
        self.assertEqual(events[-1][2], 'done')

    def test_should_cover_remaining_hsts_grades(self):
        """Fingerprint._build_hsts_result() should cover invalid, disabled, moderate and good HSTS grades."""

        cases = [
            ({'strict-transport-security': 'includeSubDomains'}, 'invalid', 'missing_max_age'),
            ({'strict-transport-security': 'max-age=0; includeSubDomains'}, 'disabled', 'disabled'),
            ({'strict-transport-security': 'max-age=16000000; includeSubDomains'}, 'moderate', 'max_age_below_preload_minimum'),
            ({'strict-transport-security': 'max-age=31536000'}, 'good', 'missing_include_subdomains'),
        ]

        for headers, expected_grade, expected_warning in cases:
            with self.subTest(expected_grade=expected_grade):
                result = Fingerprint._build_hsts_result(
                    headers=headers,
                    base_url='https://example.com/',
                    final_root_url='https://example.com/',
                )

                self.assertEqual(result['grade'], expected_grade)
                self.assertIn(expected_warning, result['warnings'])

    def test_should_parse_hsts_max_age_invalid_values_as_none(self):
        """Fingerprint._parse_hsts_max_age() should reject invalid and negative max-age values."""

        self.assertIsNone(Fingerprint._parse_hsts_max_age('invalid'))
        self.assertIsNone(Fingerprint._parse_hsts_max_age('-1'))

    def test_should_skip_extended_header_signature_when_value_mismatches(self):
        """Fingerprint extended header rules should ignore headers with mismatched required values."""

        detector = Fingerprint(config=FakeConfig(), client=self._make_client(FakeConfig(), {}))

        detector._apply_extended_cms_catalog_rules(
            body_lower='',
            headers={'x-powered-cms': 'not-bitrix'},
            cookies=[],
            generator='',
        )

        self.assertNotIn('Bitrix', [candidate['name'] for candidate in detector._build_candidates()])

    def test_should_detect_php_runtime_from_final_url_route_marker(self):
        """Fingerprint._has_php_route_marker() should detect PHP markers in the final URL."""

        self.assertTrue(Fingerprint._has_php_route_marker('', 'https://example.com/read.php?id=1'))


class TestFingerprintHstsSecurityHeaders(unittest.TestCase):
    """HSTS security-header fingerprint coverage."""

    def _make_client(self, config, responses):
        client = FakeClient(responses)
        client.config_method_getter = lambda: getattr(config, '_method', 'HEAD')
        return client

    def test_detects_hsts_preload_ready_after_https_redirect(self):
        """Fingerprint should preserve preload-ready HSTS posture from final HTTPS root response."""

        config = FakeConfig()
        responses = {
            ('GET', 'http://example.com/'): FakeResponse(301, '', {'Location': 'https://example.com/'}),
            ('GET', 'https://example.com/'): FakeResponse(
                200,
                '<html><body>custom</body></html>',
                {'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload'},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()
        hsts = result['security_headers']['hsts']

        self.assertTrue(hsts['present'])
        self.assertEqual(hsts['max_age'], 31536000)
        self.assertTrue(hsts['include_subdomains'])
        self.assertTrue(hsts['preload'])
        self.assertTrue(hsts['preload_ready'])
        self.assertTrue(hsts['http_to_https_redirect'])
        self.assertEqual(hsts['grade'], 'preload-ready')
        self.assertEqual(hsts['warnings'], [])

    def test_marks_preload_directive_as_not_ready_when_max_age_is_too_low(self):
        """Fingerprint should warn when preload is present but preload requirements are not met."""

        result = Fingerprint._build_hsts_result(
            headers={'strict-transport-security': 'max-age=300; preload'},
            base_url='https://example.com/',
            final_root_url='https://example.com/',
        )

        self.assertTrue(result['present'])
        self.assertEqual(result['grade'], 'weak')
        self.assertFalse(result['preload_ready'])
        self.assertIn('max_age_too_low', result['warnings'])
        self.assertIn('preload_not_ready', result['warnings'])

    def test_ignores_hsts_header_observed_on_plain_http(self):
        """Fingerprint should not mark HSTS as present when the final root response is plain HTTP."""

        result = Fingerprint._build_hsts_result(
            headers={'strict-transport-security': 'max-age=31536000; includeSubDomains; preload'},
            base_url='http://example.com/',
            final_root_url='http://example.com/',
        )

        self.assertFalse(result['present'])
        self.assertEqual(result['grade'], 'missing')
        self.assertIn('not_https', result['warnings'])
        self.assertIn('missing_hsts', result['warnings'])
