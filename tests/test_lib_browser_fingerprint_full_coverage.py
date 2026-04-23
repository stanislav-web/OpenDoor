# -*- coding: utf-8 -*-

import unittest


from src.lib.browser.fingerprint import Fingerprint


class HeaderBag(dict):
    """Header bag with getlist support for cookie extraction tests."""

    def getlist(self, key):
        """
        Return header values as a list.

        :param str key: header name
        :return: list
        """

        value = self.get(key)
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]


class FakeConfig(object):
    """Minimal config stub for Fingerprint tests."""

    DEFAULT_SCHEME = 'http://'
    DEFAULT_HTTP_PORT = 80
    DEFAULT_SSL_PORT = 443

    def __init__(self, host='example.com', scheme='http://', port=80):
        """
        Init config.

        :param str host: target host
        :param str scheme: scheme
        :param int port: port
        """

        self.host = host
        self.scheme = scheme
        self.port = port
        self._method = 'HEAD'


class FakeResponse(object):
    """Fake response object."""

    def __init__(self, status=200, data='', headers=None):
        """
        Init response.

        :param int status: status code
        :param str|bytes data: response body
        :param dict headers: response headers
        """

        self.status = status
        self.data = data.encode('utf-8') if isinstance(data, str) else data
        self.headers = HeaderBag(headers or {})


class FakeClient(object):
    """Fake HTTP client keyed by (method, url)."""

    def __init__(self, config, responses=None):
        """
        Init fake client.

        :param FakeConfig config: config instance
        :param dict responses: response mapping
        """

        self.config = config
        self.responses = responses or {}
        self.calls = []

    def request(self, url):
        """
        Return fake response for the current config method and URL.

        :param str url: target URL
        :return: FakeResponse | None
        """

        method = getattr(self.config, '_method', 'HEAD')
        self.calls.append((method, url))
        return self.responses.get((method, url))


class TestFingerprintFullCoverage(unittest.TestCase):
    """High-coverage tests for Fingerprint."""

    def make_detector(self, responses=None, host='example.com', scheme='http://', port=80):
        """
        Build a detector with fake config and client.

        :param dict responses: fake response mapping
        :param str host: target host
        :param str scheme: scheme
        :param int port: port
        :return: tuple[Fingerprint, FakeConfig, FakeClient]
        """

        config = FakeConfig(host=host, scheme=scheme, port=port)
        client = FakeClient(config=config, responses=responses or {})
        detector = Fingerprint(config=config, client=client)
        return detector, config, client

    def apply_case(
        self,
        body='',
        headers=None,
        cookies=None,
        generator='',
        probes=None,
        final_root_url='http://example.com/',
        not_found_status=0,
        not_found_body='',
        not_found_headers=None,
    ):
        """
        Apply detection rules once and return sorted candidates.

        :param str body: response body
        :param dict headers: response headers
        :param list cookies: cookie names
        :param str generator: generator meta
        :param dict probes: probe status mapping
        :param str final_root_url: final root URL
        :param int not_found_status: 404 probe status
        :param str not_found_body: 404 probe body
        :param dict not_found_headers: 404 probe headers
        :return: tuple[list, list]
        """

        detector, _, _ = self.make_detector()
        headers = headers or {}
        cookies = cookies or []
        probes = probes or {}
        not_found_headers = not_found_headers or {}

        detector._apply_detection_rules(
            body=body,
            body_lower=body.lower(),
            headers=headers,
            cookies=cookies,
            generator=generator,
            probe_statuses=probes,
            final_root_url=final_root_url,
            not_found_status=not_found_status,
            not_found_body=not_found_body,
            not_found_headers=not_found_headers,
        )

        return detector._build_candidates(), detector._build_infrastructure_candidates()

    def test_build_base_url_handles_default_and_custom_ports(self):
        """
        Fingerprint._build_base_url() should format URLs for default and custom ports.

        :return: None
        """

        detector, _, _ = self.make_detector()
        self.assertEqual(detector._build_base_url(), 'http://example.com/')

        detector_ssl, _, _ = self.make_detector(scheme='https://', port=443)
        self.assertEqual(detector_ssl._build_base_url(), 'https://example.com/')

        detector_custom, _, _ = self.make_detector(port=8080)
        self.assertEqual(detector_custom._build_base_url(), 'http://example.com:8080/')

    def test_request_restores_original_method_after_override(self):
        """
        Fingerprint._request() should temporarily override config._method and restore it.

        :return: None
        """

        responses = {
            ('GET', 'http://example.com/'): FakeResponse(status=200, data='ok', headers={})
        }
        detector, config, client = self.make_detector(responses=responses)

        self.assertEqual(config._method, 'HEAD')
        response = detector._request('http://example.com/', method='GET')

        self.assertEqual(response.status, 200)
        self.assertEqual(client.calls, [('GET', 'http://example.com/')])
        self.assertEqual(config._method, 'HEAD')

    def test_follow_redirects_handles_chains_and_missing_location(self):
        """
        Fingerprint._follow_redirects() should follow redirect chains and stop without Location.

        :return: None
        """

        responses = {
            ('GET', 'http://example.com/'): FakeResponse(301, '', {'Location': '/home'}),
            ('GET', 'http://example.com/home'): FakeResponse(302, '', {'Location': '/final'}),
            ('GET', 'http://example.com/final'): FakeResponse(200, 'done', {}),
        }
        detector, _, _ = self.make_detector(responses=responses)

        initial = responses[('GET', 'http://example.com/')]
        response, final_url = detector._follow_redirects(initial, 'http://example.com/', method='GET', max_hops=3)

        self.assertEqual(response.status, 200)
        self.assertEqual(final_url, 'http://example.com/final')

        no_location = FakeResponse(301, '', {})
        response, final_url = detector._follow_redirects(no_location, 'http://example.com/', method='GET', max_hops=2)
        self.assertEqual(response.status, 301)
        self.assertEqual(final_url, 'http://example.com/')

    def test_extract_helpers_cover_headers_body_generator_and_cookies(self):
        """
        Fingerprint helper extractors should normalize headers, body, generator and cookies.

        :return: None
        """

        detector, _, _ = self.make_detector()
        response = FakeResponse(
            status=200,
            data='<meta name="generator" content="WordPress 6.8"><html></html>',
            headers={
                'Server': 'nginx',
                'Set-Cookie': ['a=1; Path=/', 'b=2; HttpOnly'],
            }
        )

        headers = detector._extract_headers(response)
        cookies = detector._extract_cookies(response)
        body = detector._extract_body(response)
        generator = detector._extract_generator(body)

        self.assertEqual(headers['server'], 'nginx')
        self.assertEqual(cookies, ['a', 'b'])
        self.assertIn('generator', body)
        self.assertEqual(generator, 'WordPress 6.8')

        plain_response = FakeResponse(status=200, data=b'bytes')
        self.assertEqual(detector._extract_body(plain_response), 'bytes')
        self.assertEqual(detector._extract_generator('<html></html>'), '')

    def test_probe_endpoints_collects_only_existing_probe_statuses(self):
        """
        Fingerprint._probe_endpoints() should collect statuses for existing fake responses.

        :return: None
        """

        responses = {
            ('HEAD', 'http://example.com/wp-json/'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/_next/static/'): FakeResponse(403, '', {}),
        }
        detector, _, _ = self.make_detector(responses=responses)

        probes = detector._probe_endpoints('http://example.com/')
        self.assertEqual(probes['/wp-json/'], 200)
        self.assertEqual(probes['/_next/static/'], 403)
        self.assertNotIn('/bitrix/', probes)


    def test_probe_not_found_signature_collects_framework_404_response(self):
        """
        Fingerprint._probe_not_found_signature() should return status, body and headers for a missing route.

        :return: None
        """

        responses = {
            ('GET', 'http://example.com/.opendoor-fingerprint-not-found-probe'): FakeResponse(
                404,
                '{"message":"Cannot GET /.opendoor-fingerprint-not-found-probe","error":"Not Found","statusCode":404}',
                {'X-Powered-By': 'NestJS'},
            ),
        }
        detector, _, _ = self.make_detector(responses=responses)

        status, body, headers = detector._probe_not_found_signature('http://example.com/')

        self.assertEqual(status, 404)
        self.assertIn('Cannot GET', body)
        self.assertEqual(headers['x-powered-by'], 'NestJS')

    def test_detect_returns_default_when_root_response_is_missing(self):
        """
        Fingerprint.detect() should return DEFAULT_RESULT when root response is unavailable.

        :return: None
        """

        detector, _, _ = self.make_detector(responses={})
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertEqual(result['infrastructure']['provider'], 'unknown')

    def test_detect_returns_custom_for_weak_application_signal(self):
        """
        Fingerprint.detect() should return custom for weak app-only signals.

        :return: None
        """

        responses = {
            ('GET', 'http://example.com/'): FakeResponse(
                200,
                '<html><body><div id="root"></div></body></html>',
                {'Server': 'nginx'}
            )
        }
        detector, _, _ = self.make_detector(responses=responses)
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['name'], 'Unknown custom stack')
        self.assertGreaterEqual(len(result['candidates']), 1)

    def test_detect_returns_infrastructure_when_application_is_unknown(self):
        """
        Fingerprint.detect() should preserve infrastructure signals even when app is unknown.

        :return: None
        """

        responses = {
            ('GET', 'http://example.com/'): FakeResponse(
                200,
                '<html><body>plain site</body></html>',
                {
                    'Server': 'cloudflare',
                    'CF-Ray': 'abc123',
                    'CF-Cache-Status': 'HIT',
                }
            )
        }
        detector, _, _ = self.make_detector(responses=responses)
        result = detector.detect()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(result['infrastructure']['provider'], 'Cloudflare')
        self.assertGreaterEqual(result['infrastructure']['confidence'], 90)

    def test_detect_strong_wordpress_on_aws_cloudfront(self):
        """
        Fingerprint.detect() should detect both strong application and infrastructure signatures.

        :return: None
        """

        responses = {
            ('GET', 'http://example.com/'): FakeResponse(
                301,
                '',
                {'Location': '/home'}
            ),
            ('GET', 'http://example.com/home'): FakeResponse(
                200,
                (
                    '<html><head><meta name="generator" content="WordPress 6.8"></head>'
                    '<body>'
                    '<link href="/wp-content/themes/x/style.css">'
                    '<script src="/wp-includes/js/jquery.js"></script>'
                    '</body></html>'
                ),
                {
                    'Server': 'CloudFront',
                    'Via': '1.1 edge.cloudfront.net (CloudFront)',
                    'X-Amz-Cf-Id': 'cf-id',
                    'X-Amz-Cf-Pop': 'WAW50-C1',
                }
            ),
            ('HEAD', 'http://example.com/home/wp-json/'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/home/wp-login.php'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/home/xmlrpc.php'): FakeResponse(405, '', {}),
        }

        detector, _, _ = self.make_detector(responses=responses)
        result = detector.detect()

        self.assertEqual(result['category'], 'cms')
        self.assertEqual(result['name'], 'WordPress')
        self.assertEqual(result['infrastructure']['provider'], 'AWS CloudFront')
        self.assertGreaterEqual(result['confidence'], 90)

    def test_build_infrastructure_result_and_confidence_clamps(self):
        """
        Fingerprint infrastructure result builder and confidence clamp should behave predictably.

        :return: None
        """

        detector, _, _ = self.make_detector()

        unknown = detector._build_infrastructure_result([])
        self.assertEqual(unknown['provider'], 'unknown')
        self.assertEqual(unknown['confidence'], 0)

        self.assertEqual(detector._calculate_confidence(0, 0), 35)
        self.assertEqual(detector._calculate_confidence(100, 50), 98)


    def test_helper_edge_cases_cover_fallback_branches(self):
        """
        Fingerprint helper methods should handle secondary candidates and fallback parsing branches.

        :return: None
        """

        class DictWithoutItems(dict):
            """Dictionary that hides items() to exercise the isinstance(dict) branch."""

            def __getattribute__(self, name):
                if name == 'items':
                    raise AttributeError(name)
                return dict.__getattribute__(self, name)

        class HeadersWithoutItems(object):
            """Header object without items() to exercise the empty fallback branch."""

            pass

        class BrokenHeaderBag(object):
            """Cookie bag with a failing getlist() implementation."""

            def getlist(self, key):
                raise RuntimeError(key)

        detector, _, _ = self.make_detector()

        headers = detector._extract_headers(FakeResponse(status=200, headers=DictWithoutItems({'Server': 'nginx'})))
        self.assertEqual(headers['server'], 'nginx')

        response_without_items = type('ResponseNoItems', (), {'status': 200, 'data': b'', 'headers': HeadersWithoutItems()})()
        headers = detector._extract_headers(response_without_items)
        self.assertEqual(headers, {})

        self.assertEqual(detector._extract_body(FakeResponse(status=200, data=None)), '')
        self.assertEqual(detector._extract_body(FakeResponse(status=200, data='plain-string')), 'plain-string')

        broken_cookie_response = type('BrokenCookieResponse', (), {'status': 200, 'data': b'', 'headers': BrokenHeaderBag()})()
        cookies = detector._extract_cookies(broken_cookie_response)
        self.assertEqual(cookies, [])

        cookies = detector._extract_cookies(FakeResponse(status=200, headers=HeaderBag({'Set-Cookie': ['flagonly; Path=/', '=empty; Path=/', 'real=1; Path=/']})))
        self.assertEqual(cookies, ['real'])

        redirect_detector, _, _ = self.make_detector()
        response, final_url = redirect_detector._follow_redirects(
            FakeResponse(status=302, headers={'Location': '/lost'}),
            'http://example.com/',
            method='GET',
            max_hops=1,
        )
        self.assertIsNone(response)
        self.assertEqual(final_url, 'http://example.com/lost')

        responses = {
            ('GET', 'http://example.com/'): FakeResponse(
                200,
                '<html><head><meta name="generator" content="WordPress 6.8"></head>'
                '<body><link href="/wp-content/plugins/woocommerce/assets/app.css">'
                '<script src="/wp-includes/js/jquery.js"></script>woocommerce-notices-wrapper</body></html>',
                {'Server': 'cloudflare', 'CF-Ray': 'abc', 'CF-Cache-Status': 'HIT', 'X-Served-By': 'cache-fra', 'X-Fastly-Request-Id': 'fastly'}
            ),
            ('HEAD', 'http://example.com/wp-json/'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/wp-login.php'): FakeResponse(200, '', {}),
            ('HEAD', 'http://example.com/xmlrpc.php'): FakeResponse(405, '', {}),
        }
        detect_detector, _, _ = self.make_detector(responses=responses)
        result = detect_detector.detect()

        self.assertEqual(result['name'], 'WordPress')
        self.assertGreater(len(result['candidates']), 1)
        self.assertGreater(len(result['infrastructure']['candidates']), 1)

        top_two = detect_detector._build_infrastructure_candidates()[:2]
        built = detect_detector._build_infrastructure_result(top_two)
        self.assertEqual(built['provider'], top_two[0]['provider'])
        self.assertGreaterEqual(built['confidence'], 35)

    def test_application_matrix_hits_popular_cms_framework_and_builder_rules(self):
        """
        Fingerprint._apply_detection_rules() should classify a wide matrix of application signatures.

        :return: None
        """

        cases = [
            {
                'name': 'WordPress',
                'category': 'cms',
                'generator': 'WordPress 6.8',
                'body': '<link href="/wp-content/themes/x.css"><script src="/wp-includes/js/jquery.js"></script>',
                'cookies': ['wordpress_logged_in_123', 'wp-settings-1'],
                'probes': {'/wp-json/': 200, '/wp-login.php': 200, '/xmlrpc.php': 405},
            },
            {
                'name': 'Drupal',
                'category': 'cms',
                'generator': 'Drupal 10',
                'body': '<script>var drupalSettings={};</script><img src="/sites/default/files/a.png">',
                'probes': {'/user/login': 200},
            },
            {
                'name': 'Joomla',
                'category': 'cms',
                'generator': 'Joomla! - Open Source Content Management',
                'body': '<script src="/media/system/js/core.js"></script><a href="/index.php?option=com_users">x</a>',
                'probes': {'/administrator/': 403},
            },
            {
                'name': 'Magento',
                'category': 'ecommerce',
                'body': '<script src="/static/version1/frontend.js"></script><script src="/skin/frontend/base.js"></script>magento_ui/js mage/cookies <input name="form_key">',
            },
            {
                'name': 'Shopify',
                'category': 'ecommerce',
                'body': '<script src="https://cdn.shopify.com/s/files/a.js"></script><script>Shopify.theme={};</script><div class="shopify-section"></div>',
                'headers': {'x-shopid': '123'},
                'cookies': ['_shopify_y'],
            },
            {
                'name': 'Bitrix',
                'category': 'cms',
                'body': '<script src="/bitrix/cache/main.js"></script><script>window.BX={}; BX.message({}); BX.setCssList([]);</script>',
                'cookies': ['bitrix_sessid'],
                'probes': {'/bitrix/': 200},
            },
            {
                'name': 'Wix',
                'category': 'sitebuilder',
                'body': '<script src="https://static.parastorage.com/x.js"></script><img src="https://static.wixstatic.com/media/x.png">wix-code-sdk wix-image',
                'headers': {'x-wix-request-id': 'req'},
            },
            {
                'name': 'Tilda',
                'category': 'sitebuilder',
                'body': '<div class="tilda-page tilda-blocks-123 tilda-pub-456"></div><script src="https://static.tildacdn.com/js/tilda.js"></script>',
            },
            {
                'name': 'Webflow',
                'category': 'sitebuilder',
                'generator': 'Webflow',
                'body': '<html data-wf-page="abc" data-wf-site="xyz"><link href="/css/webflow.css"><div class="w-webflow-badge"></div>',
            },
            {
                'name': 'Squarespace',
                'category': 'sitebuilder',
                'generator': 'Squarespace',
                'body': '<script src="https://static1.squarespace.com/x.js"></script><div class="sqs-block-content"></div>',
            },
            {
                'name': 'Ghost',
                'category': 'cms',
                'generator': 'Ghost 5.0',
                'body': '<script src="/ghost/api/content/posts/"></script><div class="ghost-content casper"></div>',
                'probes': {'/ghost/api/content/': 403},
            },
            {
                'name': 'WooCommerce',
                'category': 'ecommerce',
                'body': '<script src="/wp-content/plugins/woocommerce/assets/js/frontend/add-to-cart.js"></script>?wc-ajax=get_refreshed_fragments<div class="woocommerce-notices-wrapper"></div><a class="add_to_cart_button">Buy</a>',
                'cookies': ['woocommerce_cart_hash', 'wp_woocommerce_session_abc'],
            },
            {
                'name': 'OpenCart',
                'category': 'ecommerce',
                'body': '<link href="/catalog/view/theme/default/stylesheet/stylesheet.css"><a href="index.php?route=common/home">Home</a>',
                'cookies': ['ocsessid'],
                'probes': {'/catalog/view/theme/': 403},
            },
            {
                'name': 'PrestaShop',
                'category': 'ecommerce',
                'body': '<script>var prestashop = {};</script><link href="/themes/classic/assets/theme.css"><script src="/modules/ps_shoppingcart/cart.js"></script>',
                'cookies': ['prestashop-abc'],
            },
            {
                'name': 'TYPO3',
                'category': 'cms',
                'body': '<script>TYPO3.settings = {};</script><link href="/typo3conf/ext/site.css"><script src="/typo3temp/assets/app.js"></script>',
                'probes': {'/typo3/': 403},
            },
            {
                'name': 'Strapi',
                'category': 'framework',
                'body': '<script>window.strapi = true;</script><script src="/admin/init"></script><img src="/uploads/logo.png">',
                'headers': {'x-powered-by': 'Strapi'},
                'probes': {'/admin/init': 200, '/admin': 302, '/uploads/': 200},
            },
            {
                'name': 'MkDocs',
                'category': 'static',
                'generator': 'MkDocs 1.6',
                'body': '<script>var mkdocs_page_name = "Home"; var mkdocs_page_input_path = "index.md";</script>',
            },
            {
                'name': 'Jekyll',
                'category': 'static',
                'generator': 'Jekyll v4.4.1',
                'body': '<!-- Begin Jekyll SEO tag v2.8.0 -->',
            },
            {
                'name': 'Hugo',
                'category': 'static',
                'generator': 'Hugo 0.145.0',
            },
            {
                'name': 'VitePress',
                'category': 'static',
                'body': '<div class="vitepress-theme"><div class="VPContent"></div><nav class="VPNav"></nav></div>',
            },
            {
                'name': 'Docusaurus',
                'category': 'static',
                'generator': 'Docusaurus v3',
                'body': '<div data-rh="true"></div><script src="/assets/js/runtime~main.js"></script>docusaurus',
            },
            {
                'name': 'Next.js',
                'category': 'framework',
                'body': '<div id="__next"></div><span next-head-count="3"></span><script id="__NEXT_DATA__">{}</script><script src="/_next/static/chunks/main.js"></script>',
                'probes': {'/_next/static/': 403},
            },
            {
                'name': 'Nuxt',
                'category': 'framework',
                'body': '<div id="__nuxt"></div><script>window.__NUXT__={};</script><script src="/_nuxt/app.js"></script>',
                'probes': {'/_nuxt/': 403},
            },
            {
                'name': 'Gatsby',
                'category': 'framework',
                'body': '<script src="/page-data/sq/d/123.json"></script><script src="/webpack-runtime.js"></script><script>window.___gatsby={};</script>gatsby-script-loader',
            },
            {
                'name': 'Astro',
                'category': 'framework',
                'body': '<astro-island></astro-island><script src="/_astro/index.js"></script>',
            },
            {
                'name': 'Remix',
                'category': 'framework',
                'body': '<script>window.__remixContext={}; window.__remixRoute=true;</script><script src="/build/entry.client.js"></script>',
                'probes': {'/build/': 200},
            },
            {
                'name': 'Angular',
                'category': 'framework',
                'body': '<app-root ng-version="17.0.0"></app-root>',
            },
            {
                'name': 'React',
                'category': 'framework',
                'body': '<div id="root" data-reactroot=""></div>',
            },
            {
                'name': 'Vue',
                'category': 'framework',
                'body': '<div data-server-rendered="true"></div>',
            },
            {
                'name': 'SvelteKit',
                'category': 'framework',
                'body': '<div data-sveltekit-preload-data="hover">sveltekit</div>',
            },
            {
                'name': 'Laravel',
                'category': 'framework',
                'body': '<meta name="csrf-token" content="x">laravel',
                'cookies': ['laravel_session', 'xsrf-token'],
            },
            {
                'name': 'Django',
                'category': 'framework',
                'body': '<input type="hidden" name="csrfmiddlewaretoken" value="x">',
                'cookies': ['csrftoken', 'sessionid'],
            },
            {
                'name': 'Flask',
                'category': 'framework',
                'headers': {'x-powered-by': 'Flask', 'server': 'Werkzeug/3.0'},
            },
            {
                'name': 'Ruby on Rails',
                'category': 'framework',
                'body': '<meta name="csrf-param" content="authenticity_token"><meta name="csrf-token" content="x">',
                'cookies': ['_rails_session'],
            },
            {
                'name': 'Express',
                'category': 'framework',
                'headers': {'x-powered-by': 'Express'},
                'cookies': ['connect.sid'],
                'not_found_status': 404,
                'not_found_body': 'Cannot GET /.opendoor-fingerprint-not-found-probe',
            },
            {
                'name': 'NestJS',
                'category': 'framework',
                'probes': {'/swagger': 200, '/openapi.json': 200},
                'not_found_status': 404,
                'not_found_body': '{"message":"Cannot GET /.opendoor-fingerprint-not-found-probe","error":"Not Found","statusCode":404}',
                'not_found_headers': {'x-powered-by': 'NestJS'},
            },
            {
                'name': 'Fastify',
                'category': 'framework',
                'headers': {'server': 'fastify'},
                'not_found_status': 404,
                'not_found_body': 'Route GET:/.opendoor-fingerprint-not-found-probe not found',
            },
            {
                'name': 'FastAPI',
                'category': 'framework',
                'headers': {'server': 'uvicorn'},
                'probes': {'/openapi.json': 200, '/docs': 200, '/redoc': 200},
                'not_found_status': 404,
                'not_found_body': '{"detail":"Not Found"}',
            },
            {
                'name': 'Koa',
                'category': 'framework',
                'headers': {'x-powered-by': 'Koa'},
                'cookies': ['koa:sess'],
            },
            {
                'name': 'Hapi',
                'category': 'framework',
                'headers': {'x-powered-by': 'hapi'},
                'not_found_status': 404,
                'not_found_body': '{"statusCode":404,"error":"Not Found","message":"Not Found"}',
            },
            {
                'name': 'Symfony',
                'category': 'framework',
                'headers': {'x-powered-by': 'Symfony'},
                'cookies': ['sf_redirect'],
            },
            {
                'name': 'ASP.NET',
                'category': 'framework',
                'body': '<input type="hidden" name="__VIEWSTATE" value="x"><input type="hidden" name="__EVENTVALIDATION" value="y">',
                'headers': {'x-powered-by': 'ASP.NET', 'x-aspnet-version': '4.0'},
                'cookies': ['asp.net_sessionid'],
            },
            {
                'name': 'Spring',
                'category': 'framework',
                'body': '<meta name="generator" content="thymeleaf">thymeleaf spring',
                'cookies': ['jsessionid'],
            },
            {
                'name': 'Phoenix',
                'category': 'framework',
                'body': '<input type="hidden" name="_csrf_token" value="x">phoenix _buildinfo',
                'cookies': ['_app_key'],
            },
        ]

        for case in cases:
            with self.subTest(case=case['name']):
                candidates, _ = self.apply_case(
                    body=case.get('body', ''),
                    headers=case.get('headers', {}),
                    cookies=case.get('cookies', []),
                    generator=case.get('generator', ''),
                    probes=case.get('probes', {}),
                    not_found_status=case.get('not_found_status', 0),
                    not_found_body=case.get('not_found_body', ''),
                    not_found_headers=case.get('not_found_headers', {}),
                )

                self.assertGreater(len(candidates), 0)
                self.assertEqual(candidates[0]['name'], case['name'])
                self.assertEqual(candidates[0]['category'], case['category'])

    def test_infrastructure_matrix_hits_aws_and_other_providers(self):
        """
        Fingerprint._apply_detection_rules() should classify a broad infrastructure matrix.

        :return: None
        """

        cases = [
            {
                'provider': 'AWS CloudFront',
                'headers': {
                    'server': 'CloudFront',
                    'via': '1.1 edge.cloudfront.net (CloudFront)',
                    'x-cache': 'Miss from cloudfront',
                    'x-amz-cf-id': 'cf-id',
                    'x-amz-cf-pop': 'WAW50-C1',
                },
            },
            {
                'provider': 'AWS S3',
                'headers': {
                    'server': 'AmazonS3',
                    'x-amz-request-id': 'rid',
                    'x-amz-id-2': 'id2',
                },
                'url': 'https://bucket.s3.amazonaws.com/',
            },
            {
                'provider': 'AWS ELB / ALB',
                'headers': {
                    'server': 'awselb/2.0',
                    'x-amzn-trace-id': 'Root=1-abc',
                },
            },
            {
                'provider': 'AWS API Gateway',
                'headers': {
                    'x-amz-apigw-id': 'gw',
                },
            },
            {
                'provider': 'AWS Amplify',
                'headers': {
                    'x-amplify-id': 'amp',
                },
            },
            {
                'provider': 'Cloudflare',
                'headers': {
                    'server': 'cloudflare',
                    'cf-ray': 'abc',
                    'cf-cache-status': 'HIT',
                },
            },
            {
                'provider': 'Vercel',
                'headers': {
                    'server': 'Vercel',
                    'x-vercel-id': 'cdg1::abc',
                    'x-vercel-cache': 'HIT',
                },
            },
            {
                'provider': 'Netlify',
                'headers': {
                    'server': 'Netlify',
                    'x-nf-request-id': 'nf-id',
                },
            },
            {
                'provider': 'GitHub Pages',
                'headers': {
                    'server': 'GitHub-Pages',
                    'x-github-request-id': 'gh',
                },
            },
            {
                'provider': 'GitLab Pages',
                'headers': {
                    'server': 'GitLab Pages',
                },
            },
            {
                'provider': 'Heroku',
                'headers': {
                    'x-request-id': 'rid',
                    'via': '1.1 vegur, 1.1 heroku-router',
                    'x-heroku-dynos-in-use': '1',
                },
            },
            {
                'provider': 'Microsoft Azure',
                'headers': {
                    'x-azure-ref': 'az',
                    'x-ms-request-id': 'ms-id',
                },
                'url': 'https://example.azurewebsites.net/',
            },
            {
                'provider': 'Google Cloud',
                'headers': {
                    'x-cloud-trace-context': 'trace',
                },
            },
            {
                'provider': 'Google Cloud / Google Frontend',
                'headers': {
                    'server': 'gse',
                },
            },
            {
                'provider': 'Google Cloud Run',
                'headers': {},
                'url': 'https://demo-12345.run.app/',
            },
            {
                'provider': 'Google App Engine',
                'headers': {},
                'url': 'https://demo.appspot.com/',
            },
            {
                'provider': 'Fastly',
                'headers': {
                    'x-served-by': 'cache-fra-etou8220030-FRA',
                    'x-fastly-request-id': 'fastly-id',
                },
            },
            {
                'provider': 'Akamai',
                'headers': {
                    'server': 'AkamaiGHost',
                    'akamai-grn': '0.123',
                },
            },
            {
                'provider': 'OpenResty',
                'headers': {
                    'server': 'openresty',
                },
            },
        ]

        for case in cases:
            with self.subTest(case=case['provider']):
                _, infra_candidates = self.apply_case(
                    headers=case.get('headers', {}),
                    final_root_url=case.get('url', 'http://example.com/'),
                )

                self.assertGreater(len(infra_candidates), 0)
                self.assertEqual(infra_candidates[0]['provider'], case['provider'])