# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

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


class MultiHeaders(object):
    """Fake multi-value HTTP headers object."""

    def __init__(self, items):
        self._items = list(items)

    def items(self):
        return list(self._items)

    def getlist(self, name):
        name_lower = str(name).lower()
        return [value for key, value in self._items if str(key).lower() == name_lower]


class FakeClient(object):
    """Fake request client keyed by (method, url)."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def request(self, url):
        method = getattr(self, 'config_method_getter', lambda: 'HEAD')()
        self.calls.append((method, url))
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

    def test_detects_wordpress_from_corroborated_static_endpoint_probes(self):
        """Fingerprint should use restricted WordPress endpoints only with root evidence."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><link href="/wp-content/themes/test/style.css"></body></html>',
                {},
            ),
            ('HEAD', 'http://example.com/wp-content/'): FakeResponse(403, '', {}),
            ('HEAD', 'http://example.com/wp-includes/'): FakeResponse(403, '', {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'WordPress')
        self.assertIn('/wp-content/', [signal['value'] for signal in result['signals']])
        self.assertIn('/wp-includes/', [signal['value'] for signal in result['signals']])

    def test_does_not_promote_wordpress_from_weak_login_and_xmlrpc_only(self):
        """Fingerprint should keep login/xmlrpc-only WordPress evidence as weak candidates."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', {}),
            ('HEAD', 'http://example.com/wp-login.php'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/xmlrpc.php'): FakeResponse(405, '', {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertEqual(result['candidates'][0]['name'], 'WordPress')
        self.assertLess(result['candidates'][0]['score'], 7)

    def test_does_not_count_wordpress_probes_when_they_match_soft404_baseline(self):
        """Fingerprint should not count WordPress probes that match a catch-all 200 baseline."""

        config = FakeConfig()
        base = 'http://example.com/'
        catch_all_body = '<html><body>same catch-all page</body></html>'
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', {}),
            ('HEAD', 'http://example.com/wp-content/'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/wp-includes/'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/wp-login.php'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/xmlrpc.php'): FakeResponse(200, '', {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                200,
                catch_all_body,
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertFalse(any(candidate['name'] == 'WordPress' for candidate in result['candidates']))

    def test_distinct_probe_status_handles_invalid_and_zero_values(self):
        """Fingerprint probe-baseline comparison should reject invalid probe statuses safely."""

        self.assertFalse(Fingerprint._is_distinct_probe_status('bad-status', 404))
        self.assertFalse(Fingerprint._is_distinct_probe_status(0, 404))
        self.assertTrue(Fingerprint._is_distinct_probe_status(200, 'bad-baseline'))
        self.assertFalse(Fingerprint._is_distinct_probe_up({'/wp-content/': 200}, '/wp-content/', [403], 404))


    def test_detects_datalife_engine_from_runtime_globals_and_assets(self):
        """Fingerprint should detect DLE from stable runtime globals and engine assets."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head>'
                '<script>var dle_root = "/"; var dle_admin = "admin.php"; '
                'var dle_login_hash = ""; var dle_group = 5; var dle_skin = "Default";</script>'
                '<script src="/engine/classes/min/index.php?charset=utf-8&amp;f='
                'engine/classes/js/jquery.js,engine/classes/js/dle_js.js&amp;v=19"></script>'
                '</head><body>News site</body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'DataLife Engine')
        self.assertEqual(result['runtime']['name'], 'PHP')
        self.assertIn('engine/classes/js/dle_js.js', [signal['value'] for signal in result['signals']])


    def test_detects_datalife_engine_from_search_runtime_globals(self):
        """Fingerprint should detect DLE from inline search globals used on real homepages."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><script><!--\n'
                'var allow_dle_delete_news = false;\n'
                'var dle_search_delay = false;\n'
                "var dle_search_value = '';\n"
                '$(function(){ FastSearch(); });\n'
                '//--></script></head><body>News</body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'DataLife Engine')
        self.assertEqual(result['runtime']['name'], 'PHP')
        self.assertTrue(
            any('dle_search_delay' in signal['value'] for signal in result['signals'])
        )

    def test_detects_datalife_engine_from_explicit_generator(self):
        """Fingerprint should keep explicit DataLife Engine generator support."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><meta name="generator" content="DataLife Engine (http://dle-news.ru)"></head></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['name'], 'DataLife Engine')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_does_not_promote_datalife_engine_from_weak_dle_text_only(self):
        """Fingerprint should not classify generic DLE text or one isolated global as DLE."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>DLE can mean distance learning environment. '
                '<script>var dle_root = "/";</script></body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertNotEqual(result['name'], 'DataLife Engine')
        self.assertEqual(result['name'], 'Unknown custom stack')

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

    def test_detects_webflow_hosted_site_and_ignores_wordpress_endpoint_artifacts(self):
        """Fingerprint should prefer Webflow hosting/header signals over endpoint-only WordPress artifacts."""

        config = FakeConfig(host='carrotdev.webflow.io', scheme='https://', port=443)
        base = 'https://carrotdev.webflow.io/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><title>CarrotDevs</title></head><body>Web design</body></html>',
                {
                    'Server': 'cloudflare',
                    'X-WF-Region': 'us-east-1',
                    'Surrogate-Key': 'carrotdev.webflow.io pageId:abc',
                    'Content-Security-Policy': (
                        "frame-ancestors 'self' https://*.webflow.com "
                        'http://*.webflow.io https://webflow.com'
                    ),
                },
            ),
            ('HEAD', 'https://carrotdev.webflow.io/wp-content/'): FakeResponse(403, '', {}),
            ('HEAD', 'https://carrotdev.webflow.io/wp-includes/'): FakeResponse(403, '', {}),
            ('HEAD', 'https://carrotdev.webflow.io/wp-content/plugins/'): FakeResponse(403, '', {}),
            ('HEAD', 'https://carrotdev.webflow.io/wp-content/themes/'): FakeResponse(403, '', {}),
            ('GET', 'https://carrotdev.webflow.io{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {'X-WF-Region': 'us-east-1'},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'sitebuilder')
        self.assertEqual(result['name'], 'Webflow')
        self.assertFalse(any(candidate['name'] == 'WordPress' for candidate in result['candidates']))
        self.assertIn('host=*.webflow.io', [signal['value'] for signal in result['signals']])

    def test_detects_cms_s3_from_root_builder_runtime_markers(self):
        """Fingerprint should detect CMS.S3 without relying on WordPress endpoint probes."""

        config = FakeConfig(host='evroavtofurgon.ru', scheme='https://', port=443)
        base = 'https://evroavtofurgon.ru/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><link rel="stylesheet" href="/shared/s3/css/calendar.css">'
                '<script src="/shared/s3/js/widgets.js?v=8"></script>'
                '<script src="/g/s3/misc/form/1.0.0/s3.form.js"></script>'
                '<script src="/my/s3/js/site.min.js?1549533888"></script></head>'
                '<body><div class="widget-8 wm-widget-menu widget-type-menu_horizontal '
                'editorElement layer-type-widget"></div>'
                '<a data-api-type="popup-form" '
                'data-api-url="/my/s3/xapi/public/?method=form/postform"></a>'
                '<span class="copyright">Изготовление сайтов: megagroup.ru</span>'
                '<script>$ite.start({"sid":510324,"vid":1500293});</script></body></html>',
                {'Server': 'nginx'},
            ),
            ('HEAD', 'https://evroavtofurgon.ru/wp-content/'): FakeResponse(403, '', {}),
            ('HEAD', 'https://evroavtofurgon.ru/wp-includes/'): FakeResponse(403, '', {}),
            ('HEAD', 'https://evroavtofurgon.ru/wp-content/plugins/'): FakeResponse(403, '', {}),
            ('HEAD', 'https://evroavtofurgon.ru/wp-content/themes/'): FakeResponse(403, '', {}),
            ('GET', 'https://evroavtofurgon.ru{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'CMS.S3 / Megagroup')
        self.assertEqual(result['runtime']['name'], 'PHP')
        self.assertFalse(any(candidate['name'] == 'WordPress' for candidate in result['candidates']))
        self.assertIn(
            '/shared/s3/',
            ''.join(signal['value'] for signal in result['signals']),
        )

    def test_weak_cms_s3_vendor_text_stays_below_detection_threshold(self):
        """A single Megagroup footer/link should not classify an unrelated site as CMS.S3."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><a href="https://megagroup.ru">vendor portfolio link</a></body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertEqual(result['candidates'][0]['name'], 'CMS.S3 / Megagroup')
        self.assertLess(result['candidates'][0]['score'], 7)


    def test_detects_melbis_shop_from_powered_footer(self):
        """Fingerprint should detect Melbis Shop from an explicit product footer."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<footer>© 2026 Melbis. Powered by Melbis Shop v6.5.0.279</footer>'
                '<a href="/goods.php?id=1666">Product</a>'
                '</body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'ecommerce')
        self.assertEqual(result['name'], 'Melbis Shop Platform')
        self.assertEqual(result['runtime']['name'], 'PHP')
        self.assertIn('Powered by Melbis Shop', [signal['value'] for signal in result['signals']])

    def test_detects_melbis_shop_from_legacy_russian_footer_and_cookie(self):
        """Fingerprint should detect legacy Melbis Shop storefront markers."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>'
                '<a href="/dir.php?id=372">Каталог</a>'
                '<a href="/goods.php?id=1666">Товар</a>'
                '<footer>Магазин создан на базе Melbis Shop v5.4.0. '
                'Последнее обновление магазина: 25-06-2025 11:00</footer>'
                '</body></html>',
                MultiHeaders([('Set-Cookie', 'MS_MSS=abc123; path=/')]),
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'ecommerce')
        self.assertEqual(result['name'], 'Melbis Shop Platform')
        self.assertIn('MS_MSS', [signal['value'] for signal in result['signals']])

    def test_detects_melbis_shop_from_default_template_assets(self):
        """Fingerprint should detect Melbis Shop from default template assets."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head>'
                '<link rel="stylesheet" href="/templates/default/melbis.css">'
                '<script src="/templates/default/melbis.js"></script>'
                '</head><body><a href="/dir.php?id=1">Catalog</a></body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'ecommerce')
        self.assertEqual(result['name'], 'Melbis Shop Platform')

    def test_does_not_detect_melbis_shop_from_ms_mss_cookie_alone(self):
        """MS_MSS is a weak corroborating cookie and should not classify alone."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><h1>Generic PHP storefront</h1></body></html>',
                MultiHeaders([('Set-Cookie', 'MS_MSS=abc123; path=/')]),
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertNotEqual(result['name'], 'Melbis Shop Platform')
        self.assertFalse(any(candidate['name'] == 'Melbis Shop Platform' for candidate in result['candidates']))

    def test_does_not_detect_melbis_shop_from_generic_article_text(self):
        """Generic Melbis Shop mentions should not become a storefront fingerprint."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><article>Review of Melbis Shop and other e-commerce platforms.</article></body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertFalse(any(candidate['name'] == 'Melbis Shop Platform' for candidate in result['candidates']))


    def test_detects_camaleon_cms_from_official_site_runtime_markers(self):
        """Fingerprint should detect Camaleon CMS from brand context plus Rails CSRF."""

        config = FakeConfig(host='camaleon.website', scheme='https://', port=443)
        base = 'https://camaleon.website/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head>'
                '<meta name="csrf-param" content="authenticity_token">'
                '<meta name="csrf-token" content="token">'
                '</head><body>'
                '<h1>CAMALEON CMS</h1>'
                '<p>Camaleon CMS is an advanced Content Management System.</p>'
                '<p>Wordpress Alternative. Built with Ruby-on-Rails.</p>'
                '<a href="https://camaleon.website/store/plugins">Plugins Store</a>'
                '<footer>Copyright © 2015 - 2018 CamaleonCMS. All rights reserved.</footer>'
                '</body></html>',
                {},
            ),
            ('GET', 'https://camaleon.website{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'Camaleon CMS')
        self.assertEqual(result['runtime']['name'], 'Ruby')
        self.assertIn('Camaleon CMS+Rails CSRF', [signal['value'] for signal in result['signals']])

    def test_detects_camaleon_cms_from_admin_assets_and_cookies(self):
        """Fingerprint should detect Camaleon CMS from strong admin asset markers."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head>'
                '<link rel="stylesheet" href="/assets/camaleon_cms/admin/admin-basic-manifest.css">'
                '<script src="/assets/camaleon_cms/admin/admin-basic-manifest.js"></script>'
                '</head><body><img src="/assets/camaleon_cms/camaleon.png"></body></html>',
                MultiHeaders([
                    ('Set-Cookie', 'auth_token=abc; Path=/'),
                    ('Set-Cookie', '_cms_session=xyz; Path=/; HttpOnly'),
                ]),
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'Camaleon CMS')
        self.assertEqual(result['runtime']['name'], 'Ruby')
        self.assertIn('auth_token+_cms_session', [signal['value'] for signal in result['signals']])

    def test_does_not_detect_camaleon_cms_from_brand_text_without_rails_context(self):
        """Generic Camaleon CMS text should not become a fingerprint by itself."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><article>Review of Camaleon CMS for Rails developers.</article></body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertFalse(any(candidate['name'] == 'Camaleon CMS' for candidate in result['candidates']))


    def test_does_not_detect_wordpress_from_generic_restricted_static_probes(self):
        """Fingerprint should not treat generic 403/405 WordPress path denies as WordPress."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><head><title>CMS.S3-like site</title></head>'
                '<body><script src="/my/s3/js/site.min.js"></script></body></html>',
                {'Server': 'nginx'},
            ),
            ('HEAD', 'http://example.com/wp-content/'): FakeResponse(403, '', {}),
            ('HEAD', 'http://example.com/wp-includes/'): FakeResponse(403, '', {}),
            ('HEAD', 'http://example.com/wp-content/plugins/'): FakeResponse(403, '', {}),
            ('HEAD', 'http://example.com/wp-content/themes/'): FakeResponse(403, '', {}),
            ('HEAD', 'http://example.com/wp-json/'): FakeResponse(403, '', {}),
            ('HEAD', 'http://example.com/wp-login.php'): FakeResponse(403, '', {}),
            ('HEAD', 'http://example.com/xmlrpc.php'): FakeResponse(405, '', {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertFalse(any(candidate['name'] == 'WordPress' for candidate in result['candidates']))

    def test_does_not_detect_wordpress_from_404_static_probes(self):
        """Fingerprint should not treat 404 WordPress static paths as reachable endpoints."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', {}),
            ('HEAD', 'http://example.com/wp-content/'): FakeResponse(404, '', {}),
            ('HEAD', 'http://example.com/wp-includes/'): FakeResponse(404, '', {}),
            ('HEAD', 'http://example.com/wp-content/plugins/'): FakeResponse(404, '', {}),
            ('HEAD', 'http://example.com/wp-content/themes/'): FakeResponse(404, '', {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertFalse(any(candidate['name'] == 'WordPress' for candidate in result['candidates']))

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
                'Evolution CMS',
                'cms',
                '<html><head><meta name="generator" content="Evolution CMS 3.5"></head>'
                '<body><footer>Powered by Evolution CMS</footer></body></html>',
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
                'DiafanCMS',
                'cms',
                '<html><head><meta content="DIAFAN.CMS https://www.diafan.ru/" name="author"></head>'
                '<body><form><input type="hidden" name="module" value="shop"></form>'
                '<script src="/cache/js/theme.js"></script></body></html>',
                {},
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

    def test_detects_evolution_cms_from_not_installed_core_template(self):
        """Fingerprint should detect Evolution CMS from its own install fallback text."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                503,
                'Evolution CMS is not currently installed or the configuration file cannot be found. '
                'Do you want to install now?',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'Evolution CMS')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_detects_evolution_cms_from_modx_evolution_body_and_manager_endpoint(self):
        """Fingerprint should use MODX Evolution body text and /manager/ as corroborating evidence."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>MODX Evolution manager login powered by Evolution CMS.</body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
            ('HEAD', 'http://example.com/manager/'): FakeResponse(200, '', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'Evolution CMS')
        self.assertIn('modx evolution', [item['value'] for item in result['signals']])
        self.assertIn('/manager/', [item['value'] for item in result['signals']])

    def test_does_not_detect_evolution_cms_from_generic_evo_word_only(self):
        """Fingerprint should not classify generic EVO wording as Evolution CMS."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><p>Our product follows an evolutionary design process.</p></body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertFalse(any(candidate['name'] == 'Evolution CMS' for candidate in result['candidates']))

    def test_does_not_promote_generic_diafan_link_without_meta_author(self):
        """Fingerprint should not promote DiafanCMS from a generic body mention only."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body><p>We can migrate legacy DIAFAN.CMS sites.</p></body></html>',
                {},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertFalse(any(signal.get('type') == 'meta' for signal in result['signals']))

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

    def test_request_reuses_exact_method_url_response_inside_detection(self):
        """Fingerprint should reuse exact duplicate method+URL probes within one detect run."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', {}),
            ('HEAD', 'http://example.com/admin/init'): FakeResponse(
                302,
                '',
                {'Location': '/dotAdmin/#/public/login?r=123'},
            ),
            ('HEAD', 'http://example.com/admin/init/'): FakeResponse(
                302,
                '',
                {'Location': '/dotAdmin/#/public/login?r=123'},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }
        client = self._make_client(config, responses)
        detector = Fingerprint(config=config, client=client)

        detector.detect()

        self.assertEqual(client.calls.count(('HEAD', 'http://example.com/admin/init')), 1)
        self.assertEqual(client.calls.count(('HEAD', 'http://example.com/admin/init/')), 1)

    def test_request_does_not_share_cache_between_methods(self):
        """Fingerprint request cache should keep different HTTP methods isolated."""

        config = FakeConfig()
        responses = {
            ('HEAD', 'http://example.com/admin/init'): FakeResponse(204, '', {}),
            ('GET', 'http://example.com/admin/init'): FakeResponse(200, 'ok', {}),
        }
        client = self._make_client(config, responses)
        detector = Fingerprint(config=config, client=client)

        head_response = detector._request('http://example.com/admin/init', method='HEAD')
        get_response = detector._request('http://example.com/admin/init', method='GET')

        self.assertEqual(head_response.status, 204)
        self.assertEqual(get_response.status, 200)
        self.assertEqual(client.calls, [
            ('HEAD', 'http://example.com/admin/init'),
            ('GET', 'http://example.com/admin/init'),
        ])

    def test_detect_resets_request_cache_between_runs(self):
        """Fingerprint request cache should be scoped to one detect run only."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', {}),
            ('HEAD', 'http://example.com/admin/init'): FakeResponse(404, 'Not Found', {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(
                404,
                'Not Found',
                {},
            ),
        }
        client = self._make_client(config, responses)
        detector = Fingerprint(config=config, client=client)

        detector.detect()
        detector.detect()

        self.assertEqual(client.calls.count(('HEAD', 'http://example.com/admin/init')), 2)

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


    def test_should_detect_dotcms_from_x_dot_server_header(self):
        """Fingerprint should detect dotCMS from the x-dot-server header."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>plain site</body></html>',
                {'X-Dot-Server': 'dotcms-duncan-prod-1-0|5be9a51e39'},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'dotCMS')
        self.assertGreaterEqual(result['confidence'], 70)
        self.assertEqual(result['runtime']['name'], 'Java/JVM')
        self.assertIn('x-dot-server', result['signals'][0]['value'])


    def test_should_detect_dotcms_from_x_dot_server_with_cookie(self):
        """Fingerprint should detect dotCMS from x-dot-server plus a dotCMS cookie."""

        config = FakeConfig()
        base = 'http://example.com/'
        headers = MultiHeaders([
            ('X-Dot-Server', 'node-1|5be9a51e39'),
            ('Set-Cookie', 'opvc=1; Path=/'),
        ])
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', headers),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['name'], 'dotCMS')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_should_detect_dotcms_from_dot_request_headers(self):
        """Fingerprint should detect dotCMS from paired x-dot request/rate-limit headers."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(
                200,
                '<html><body>plain site</body></html>',
                {
                    'X-DotRequest-Cost': '2.00',
                    'X-DotRateLimit-Toks-Max': '10000/10000',
                },
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['name'], 'dotCMS')
        self.assertGreaterEqual(result['confidence'], 70)

    def test_should_detect_dotcms_from_cookie_pair(self):
        """Fingerprint should detect dotCMS from a conservative dotCMS cookie pair."""

        config = FakeConfig()
        base = 'http://example.com/'
        headers = MultiHeaders([
            ('Set-Cookie', 'opvc=1; Path=/'),
            ('Set-Cookie', 'dmid=abc; Path=/'),
        ])
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', headers),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['name'], 'dotCMS')
        self.assertGreaterEqual(result['confidence'], 60)

    def test_should_detect_dotcms_from_multiple_body_markers(self):
        """Fingerprint should detect dotCMS from multiple dotCMS body/API markers."""

        config = FakeConfig()
        base = 'http://example.com/'
        body = (
            '<html><body>'
            '<div data-dot-object="container" data-dot-identifier="abc"></div>'
            '<script src="/api/v1/page/json/home"></script>'
            '</body></html>'
        )
        responses = {
            ('GET', base): FakeResponse(200, body, {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['name'], 'dotCMS')
        self.assertGreaterEqual(result['confidence'], 60)

    def test_should_not_detect_dotcms_from_awsalb_or_jsessionid(self):
        """Fingerprint should not treat AWS ALB or generic Java cookies as dotCMS evidence."""

        config = FakeConfig()
        base = 'http://example.com/'
        headers = MultiHeaders([
            ('Set-Cookie', 'AWSALB=abc; Path=/'),
            ('Set-Cookie', 'AWSALBCORS=abc; Path=/; SameSite=None; Secure'),
            ('Set-Cookie', 'JSESSIONID=abc; Path=/'),
        ])
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain Java site</body></html>', headers),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertNotIn('dotCMS', [candidate['name'] for candidate in result['candidates']])

    def test_should_not_detect_dotcms_from_single_body_marker(self):
        """Fingerprint should ignore a single weak dotCMS body marker."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(200, '<html><body><a href="/dotAdmin">Admin</a></body></html>', {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')


    def test_should_detect_dotcms_from_admin_init_redirect_to_dotadmin(self):
        """Fingerprint should detect dotCMS when /admin/init redirects to /dotAdmin."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', {}),
            ('HEAD', 'http://example.com/admin/init'): FakeResponse(302, '', {'Location': '/dotAdmin/#/public/login?r=123'}),
            ('HEAD', 'http://example.com/admin/init/'): FakeResponse(302, '', {'Location': '/dotAdmin/#/public/login?r=123'}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'dotCMS')
        self.assertGreaterEqual(result['confidence'], 70)
        self.assertEqual(result['runtime']['name'], 'Java/JVM')
        self.assertIn('endpoint-redirect', [signal['type'] for signal in result['signals']])
        self.assertNotIn('Strapi', [candidate['name'] for candidate in result['candidates']])

    def test_should_not_detect_strapi_from_admin_init_redirect_to_dotadmin(self):
        """Fingerprint should not classify dotCMS admin redirects as Strapi."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', {}),
            ('HEAD', 'http://example.com/admin'): FakeResponse(302, '', {'Location': '/dotAdmin/#/public/login?r=123'}),
            ('HEAD', 'http://example.com/admin/init'): FakeResponse(302, '', {'Location': '/dotAdmin/#/public/login?r=123'}),
            ('HEAD', 'http://example.com/admin/init/'): FakeResponse(302, '', {'Location': '/dotAdmin/#/public/login?r=123'}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['name'], 'dotCMS')
        self.assertNotIn('Strapi', [candidate['name'] for candidate in result['candidates']])

    def test_should_still_detect_strapi_from_distinct_admin_init_json_endpoint(self):
        """Fingerprint should still detect Strapi from the real /admin/init JSON endpoint."""

        config = FakeConfig()
        base = 'http://example.com/'
        responses = {
            ('GET', base): FakeResponse(200, '<html><body>plain site</body></html>', {}),
            ('HEAD', 'http://example.com/admin/init'): FakeResponse(200, '{"data":{"uuid":"abc"}}', {}),
            ('HEAD', 'http://example.com/admin'): FakeResponse(200, '', {}),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }

        detector = Fingerprint(config=config, client=self._make_client(config, responses))
        result = detector.detect()

        self.assertEqual(result['name'], 'Strapi')
        self.assertIn('Strapi', [candidate['name'] for candidate in result['candidates']])




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


class TestFingerprintCoverageGapBranches(unittest.TestCase):
    """Targeted branch coverage for stable fingerprint helper gaps."""

    def _make_client(self, config, responses):
        client = FakeClient(responses)
        client.config_method_getter = lambda: getattr(config, '_method', 'HEAD')
        return client

    def test_should_cover_privacy_helper_edge_branches(self):
        """Fingerprint privacy helpers should handle edge values deterministically."""

        self.assertEqual(Fingerprint._privacy_score_to_risk(60), 'high')
        self.assertFalse(Fingerprint._has_long_cache_lifetime('no-store, max-age=31536000'))
        self.assertTrue(Fingerprint._has_long_cache_lifetime('public, max-age=2592000'))

        class BadMatch(object):
            def group(self, _index):
                raise TypeError('bad max-age')

        with patch('src.lib.browser.fingerprint.re.search', return_value=BadMatch()):
            self.assertFalse(Fingerprint._has_long_cache_lifetime('max-age=31536000'))
            self.assertIsNone(Fingerprint._extract_cookie_max_age('max-age=31536000'))

        privacy = Fingerprint._build_privacy_risks(
            headers={},
            body='',
            body_size=0,
            final_root_url='https://example.com/',
            security_headers={'hsts': 'invalid'},
        )
        self.assertEqual(privacy['supercookie']['risk'], 'none')

    def test_should_ignore_persistent_cookie_when_required_attrs_are_present(self):
        """Persistent-cookie helper should not flag cookies that include required attributes."""

        signals = Fingerprint._detect_persistent_cookie_surface({
            'set-cookie': 'uid=abc; Max-Age=31536000; HttpOnly; SameSite=Lax; Secure',
        })

        self.assertEqual(signals, [])

    def test_should_cover_first_party_subdomain_helper_edge_branches(self):
        """First-party helper functions should cover empty, root and public-suffix branches."""

        self.assertEqual(Fingerprint._normalize_host(' Example.COM. '), 'example.com')
        self.assertEqual(Fingerprint._site_domain('localhost'), '')
        self.assertEqual(Fingerprint._site_domain('www.example.co.uk'), 'example.co.uk')
        self.assertEqual(
            Fingerprint._extract_first_party_subdomains(
                'https://www.example.com/root https://cdn.example.com/app.js https://api.example.com/v1',
                'https://www.example.com/',
            ),
            ['api.example.com', 'cdn.example.com'],
        )
        self.assertEqual(Fingerprint._extract_first_party_subdomains('https://cdn.example.com/app.js', 'http:///'), [])

    def test_should_probe_dotcms_endpoint_header_signals_without_duplicates(self):
        """dotCMS endpoint probes should emit unique vendor header signals."""

        config = FakeConfig()
        responses = {
            ('HEAD', 'http://example.com/admin/init'): FakeResponse(
                200,
                '',
                {
                    'X-Dot-Server': 'dotcms-prod-1',
                    'X-DotRequest-Cost': '1',
                    'X-DotRateLimit-Limit': '100',
                },
            ),
            ('HEAD', 'http://example.com/admin/init/'): FakeResponse(
                200,
                '',
                {
                    'X-Dot-Server': 'dotcms-prod-1',
                    'X-DotRequest-Cost': '1',
                    'X-DotRateLimit-Limit': '100',
                },
            ),
        }
        detector = Fingerprint(config=config, client=self._make_client(config, responses))

        signals = detector._probe_dotcms_endpoint_signals('http://example.com/')

        self.assertEqual(
            signals,
            [
                {'type': 'header', 'value': 'x-dot-server=dotcms-prod-1', 'weight': 10},
                {'type': 'header', 'value': 'x-dotrequest-cost+x-dotratelimit-*', 'weight': 9},
            ],
        )

    def test_should_cover_qrator_supporting_edge_branches(self):
        """QRATOR detection should include partial server and 404 header branches."""

        detector = Fingerprint(config=FakeConfig(), client=self._make_client(FakeConfig(), {}))
        detector._apply_detection_rules(
            body='',
            body_lower='',
            headers={'server': 'nginx + qrator edge'},
            cookies=[],
            generator='',
            probe_statuses={},
            final_root_url='http://example.com/',
            not_found_status=404,
            not_found_body='',
            not_found_headers={
                'server': 'nginx + qrator fallback',
                'x-qrator-requestid': 'abcdef',
            },
        )

        infra_result = detector._build_infrastructure_result(detector._build_infrastructure_candidates())
        values = [signal['value'] for signal in infra_result['signals']]

        self.assertIn('server=nginx + qrator edge', values)
        self.assertIn('server=nginx + qrator fallback', values)
        self.assertIn('x-qrator-requestid', values)

    def test_should_detect_dotcms_from_single_marker_with_cookie(self):
        """dotCMS should be detected from one body marker when supported by a dotCMS cookie."""

        config = FakeConfig()
        responses = {
            ('GET', 'http://example.com/'): FakeResponse(
                200,
                '<html><body><a href="/dotAdmin">Admin</a></body></html>',
                {'Set-Cookie': 'dmid=abc; Path=/'},
            ),
            ('GET', 'http://example.com{0}'.format(Fingerprint.NOT_FOUND_PROBE_PATH)): FakeResponse(404, 'Not Found', {}),
        }
        detector = Fingerprint(config=config, client=self._make_client(config, responses))

        result = detector.detect()

        self.assertEqual(result['name'], 'dotCMS')
        self.assertIn('dotCMS', [candidate['name'] for candidate in result['candidates']])
