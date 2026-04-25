# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development Team: Brain Storm Team
"""

import re
from collections import defaultdict
from urllib.parse import urljoin

from src.core import helper


class Fingerprint(object):

    """Heuristic technology fingerprint detector."""

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

    PROBES = (
        '/wp-json/',
        '/wp-login.php',
        '/xmlrpc.php',
        '/sites/default/files/',
        '/user/login',
        '/administrator/',
        '/bitrix/',
        '/ghost/api/content/',
        '/_next/static/',
        '/_nuxt/',
        '/build/',
        '/swagger',
        '/swagger/',
        '/swagger-json',
        '/api-json',
        '/openapi.json',
        '/docs',
        '/redoc',
        '/admin',
        '/admin/init',
        '/uploads/',
        '/catalog/view/theme/',
        '/typo3/',
        '/typo3conf/',
        '/typo3temp/',
        '/status.php',
        '/remote.php/dav/',
        '/ocs/v1.php/cloud/capabilities?format=json',
        '/umbraco/',
        '/backend',
        '/contao/',
        '/api.php',
        '/login/index.php',
        '/manager/',
        '/bolt',
    )

    NOT_FOUND_PROBE_PATH = '/.opendoor-fingerprint-not-found-probe'

    CMS_CATEGORY = 'cms'
    FRAMEWORK_CATEGORY = 'framework'
    CUSTOM_CATEGORY = 'custom'
    ECOMMERCE_CATEGORY = 'ecommerce'
    SITE_BUILDER_CATEGORY = 'sitebuilder'
    STATIC_CATEGORY = 'static'

    def __init__(self, config, client):
        """
        Init fingerprint detector.

        :param config: browser config
        :param client: prepared HTTP client
        """

        self.__config = config
        self.__client = client
        self.__scores = defaultdict(float)
        self.__signals = defaultdict(list)
        self.__categories = {}
        self.__infra_scores = defaultdict(float)
        self.__infra_signals = defaultdict(list)

    def detect(self):
        """
        Detect probable target technology.

        :return: dict
        """

        self.__scores = defaultdict(float)
        self.__signals = defaultdict(list)
        self.__categories = {}
        self.__infra_scores = defaultdict(float)
        self.__infra_signals = defaultdict(list)

        base_url = self._build_base_url()
        root_response = self._request(base_url, method='GET')
        if root_response is None:
            return dict(self.DEFAULT_RESULT)

        root_response, final_root_url = self._follow_redirects(root_response, base_url, method='GET')
        body = self._extract_body(root_response)
        body_lower = body.lower()
        headers = self._extract_headers(root_response)
        cookies = self._extract_cookies(root_response)
        generator = self._extract_generator(body)
        probe_statuses = self._probe_endpoints(final_root_url)
        not_found_status, not_found_body, not_found_headers = self._probe_not_found_signature(final_root_url)

        self._apply_detection_rules(
            body=body,
            body_lower=body_lower,
            headers=headers,
            cookies=cookies,
            generator=generator,
            probe_statuses=probe_statuses,
            final_root_url=final_root_url,
            not_found_status=not_found_status,
            not_found_body=not_found_body,
            not_found_headers=not_found_headers,
        )

        app_candidates = self._build_candidates()
        infra_candidates = self._build_infrastructure_candidates()

        if len(app_candidates) <= 0:
            result = dict(self.DEFAULT_RESULT)
            result['infrastructure'] = self._build_infrastructure_result(infra_candidates)
            return result

        top_candidate = app_candidates[0]
        second_score = 0
        if len(app_candidates) > 1:
            second_score = app_candidates[1]['score']

        top_score = top_candidate['score']
        if top_score < 7:
            return {
                'category': self.CUSTOM_CATEGORY,
                'name': 'Unknown custom stack',
                'confidence': 45,
                'score': round(top_score, 2),
                'signals': [],
                'candidates': app_candidates[:5],
                'infrastructure': self._build_infrastructure_result(infra_candidates),
            }

        confidence = self._calculate_confidence(top_score, top_score - second_score)
        return {
            'category': top_candidate['category'],
            'name': top_candidate['name'],
            'confidence': confidence,
            'score': top_candidate['score'],
            'signals': self.__signals.get(top_candidate['name'], [])[:10],
            'candidates': app_candidates[:5],
            'infrastructure': self._build_infrastructure_result(infra_candidates),
        }

    def _build_base_url(self):
        """
        Build target base URL.

        :return: str
        """

        scheme = self.__config.scheme or self.__config.DEFAULT_SCHEME
        host = self.__config.host
        port = self.__config.port

        if (scheme == 'http://' and port == self.__config.DEFAULT_HTTP_PORT) \
                or (scheme == 'https://' and port == self.__config.DEFAULT_SSL_PORT):
            return '{0}{1}/'.format(scheme, host)
        return '{0}{1}:{2}/'.format(scheme, host, port)

    def _request(self, url, method='HEAD'):
        """
        Execute an HTTP request with a temporary method override.

        :param str url: target URL
        :param str method: request method
        :return: mixed
        """

        previous_method = getattr(self.__config, '_method', None)

        try:
            setattr(self.__config, '_method', method)
            return self.__client.request(url)
        finally:
            setattr(self.__config, '_method', previous_method)

    def _follow_redirects(self, response, url, method='GET', max_hops=3):
        """
        Follow redirects for the root request.

        :param response:
        :param str url:
        :param str method:
        :param int max_hops:
        :return: tuple
        """

        current_response = response
        current_url = url

        for _ in range(max_hops):
            status = getattr(current_response, 'status', 0)
            if int(status) not in [301, 302, 303, 307, 308]:
                break

            headers = self._extract_headers(current_response)
            location = headers.get('location')
            if not location:
                break

            current_url = urljoin(current_url, location)
            current_response = self._request(current_url, method=method)
            if current_response is None:
                break

        return current_response, current_url

    def _extract_headers(self, response):
        """
        Normalize response headers.

        :param response:
        :return: dict
        """

        headers = {}
        raw_headers = getattr(response, 'headers', {})

        if hasattr(raw_headers, 'items'):
            items = list(raw_headers.items())
        elif isinstance(raw_headers, dict):
            items = list(raw_headers.items())
        else:
            items = []

        for key, value in items:
            headers[str(key).lower()] = str(value)

        return headers

    @staticmethod
    def _extract_body(response):
        """
        Decode response body.

        :param response:
        :return: str
        """

        body = getattr(response, 'data', b'')
        if body is None:
            return ''
        if isinstance(body, bytes):
            return helper.decode(body, errors='ignore')
        return str(body)

    def _extract_cookies(self, response):
        """
        Extract cookie names from response headers.

        :param response:
        :return: list[str]
        """

        raw_headers = getattr(response, 'headers', {})
        if hasattr(raw_headers, 'getlist'):
            try:
                header_values = raw_headers.getlist('Set-Cookie')
            except Exception:
                header_values = []
        else:
            header_values = [
                value for key, value in getattr(raw_headers, 'items', lambda: [])()
                if str(key).lower() == 'set-cookie'
            ]

        cookies = []
        for raw_cookie in header_values:
            cookie_pair = str(raw_cookie).split(';', 1)[0].strip()
            if '=' not in cookie_pair:
                continue
            cookie_name = cookie_pair.split('=', 1)[0].strip().lower()
            if cookie_name:
                cookies.append(cookie_name)

        return cookies

    @staticmethod
    def _extract_generator(body):
        """
        Extract generator meta value from HTML.

        :param str body:
        :return: str
        """

        match = re.search(
            r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']',
            body,
            re.IGNORECASE,
        )
        if match is None:
            return ''
        return match.group(1).strip()

    def _probe_endpoints(self, base_url):
        """
        Probe lightweight technology endpoints.

        :param str base_url:
        :return: dict
        """

        statuses = {}
        for probe_path in self.PROBES:
            response = self._request(urljoin(base_url, probe_path.lstrip('/')), method='HEAD')
            if response is not None and hasattr(response, 'status'):
                statuses[probe_path] = int(getattr(response, 'status', 0))
        return statuses


    def _probe_not_found_signature(self, base_url):
        """
        Request a guaranteed-missing path to capture framework-specific 404 signatures.

        :param str base_url:
        :return: tuple[int, str, dict]
        """

        probe_url = urljoin(base_url, self.NOT_FOUND_PROBE_PATH.lstrip('/'))
        response = self._request(probe_url, method='GET')
        if response is None:
            return 0, '', {}

        response, _ = self._follow_redirects(response, probe_url, method='GET')
        if response is None:
            return 0, '', {}

        return (
            int(getattr(response, 'status', 0)),
            self._extract_body(response),
            self._extract_headers(response),
        )

    def _register(self, technology, category):
        """
        Register category for a technology.

        :param str technology:
        :param str category:
        :return: None
        """

        self.__categories[technology] = category

    def _add_signal(self, technology, category, signal_type, value, weight):
        """
        Add weighted application signal.

        :param str technology:
        :param str category:
        :param str signal_type:
        :param str value:
        :param float weight:
        :return: None
        """

        self._register(technology, category)
        self.__scores[technology] += float(weight)
        self.__signals[technology].append({
            'type': str(signal_type),
            'value': str(value),
            'weight': round(float(weight), 2),
        })

    def _add_infrastructure_signal(self, provider, signal_type, value, weight):
        """
        Add weighted infrastructure signal.

        :param str provider:
        :param str signal_type:
        :param str value:
        :param float weight:
        :return: None
        """

        self.__infra_scores[provider] += float(weight)
        self.__infra_signals[provider].append({
            'type': str(signal_type),
            'value': str(value),
            'weight': round(float(weight), 2),
        })

    @staticmethod
    def _header_contains(headers, name, needle):
        """
        Case-insensitive header contains check.

        :param dict headers:
        :param str name:
        :param str needle:
        :return: bool
        """

        return needle in str(headers.get(name, '')).lower()

    def _apply_detection_rules(
        self,
        body,
        body_lower,
        headers,
        cookies,
        generator,
        probe_statuses,
        final_root_url,
        not_found_status=0,
        not_found_body='',
        not_found_headers=None,
    ):
        """
        Apply heuristic rules.

        :param str body:
        :param str body_lower:
        :param dict headers:
        :param list cookies:
        :param str generator:
        :param dict probe_statuses:
        :param str final_root_url:
        :param int not_found_status:
        :param str not_found_body:
        :param dict not_found_headers:
        :return: None
        """

        del body

        not_found_headers = not_found_headers or {}
        generator_lower = str(generator).lower()
        x_powered_by = str(headers.get('x-powered-by', '')).lower()
        server = str(headers.get('server', '')).lower()
        via = str(headers.get('via', '')).lower()
        x_cache = str(headers.get('x-cache', '')).lower()
        x_served_by = str(headers.get('x-served-by', '')).lower()
        x_amz_cf_id = str(headers.get('x-amz-cf-id', '')).lower()
        x_amz_request_id = str(headers.get('x-amz-request-id', '')).lower()
        x_amz_id_2 = str(headers.get('x-amz-id-2', '')).lower()
        final_root_lower = str(final_root_url).lower()
        not_found_body_lower = str(not_found_body).lower()
        not_found_powered_by = str(not_found_headers.get('x-powered-by', '')).lower()
        not_found_server = str(not_found_headers.get('server', '')).lower()
        swagger_probe_up = any(probe_statuses.get(path) in [200, 301, 302, 401, 403] for path in [
            '/swagger',
            '/swagger/',
            '/swagger-json',
            '/api-json',
            '/openapi.json',
        ])
        docs_probe_up = any(probe_statuses.get(path) in [200, 301, 302, 401, 403] for path in ['/docs', '/redoc'])

        # WordPress
        if 'wordpress' in generator_lower:
            self._add_signal('WordPress', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if '/wp-content/' in body_lower:
            self._add_signal('WordPress', self.CMS_CATEGORY, 'markup', '/wp-content/', 6)
        if '/wp-includes/' in body_lower:
            self._add_signal('WordPress', self.CMS_CATEGORY, 'markup', '/wp-includes/', 5)
        if probe_statuses.get('/wp-json/') in [200, 401, 403]:
            self._add_signal('WordPress', self.CMS_CATEGORY, 'endpoint', '/wp-json/', 5)
        if probe_statuses.get('/wp-login.php') in [200, 301, 302, 401, 403]:
            self._add_signal('WordPress', self.CMS_CATEGORY, 'endpoint', '/wp-login.php', 4)
        if probe_statuses.get('/xmlrpc.php') in [200, 301, 302, 401, 403, 405]:
            self._add_signal('WordPress', self.CMS_CATEGORY, 'endpoint', '/xmlrpc.php', 3)
        if any(cookie.startswith('wordpress_') or cookie.startswith('wp-settings-') for cookie in cookies):
            self._add_signal('WordPress', self.CMS_CATEGORY, 'cookie', 'wordpress_*', 5)

        # Drupal
        if 'drupal' in generator_lower:
            self._add_signal('Drupal', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'drupalsettings' in body_lower or 'drupal-settings-json' in body_lower:
            self._add_signal('Drupal', self.CMS_CATEGORY, 'markup', 'drupalSettings', 6)
        if '/sites/default/files/' in body_lower:
            self._add_signal('Drupal', self.CMS_CATEGORY, 'markup', '/sites/default/files/', 5)
        if probe_statuses.get('/user/login') in [200, 301, 302, 401, 403] and '/sites/default/files/' in body_lower:
            self._add_signal('Drupal', self.CMS_CATEGORY, 'endpoint', '/user/login', 3)

        # Joomla
        if 'joomla' in generator_lower:
            self._add_signal('Joomla', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'option=com_' in body_lower:
            self._add_signal('Joomla', self.CMS_CATEGORY, 'markup', 'option=com_', 4)
        if '/media/system/js/' in body_lower:
            self._add_signal('Joomla', self.CMS_CATEGORY, 'markup', '/media/system/js/', 5)
        if probe_statuses.get('/administrator/') in [200, 301, 302, 401, 403]:
            self._add_signal('Joomla', self.CMS_CATEGORY, 'endpoint', '/administrator/', 3)

        # Magento / Adobe Commerce
        if '/static/version' in body_lower:
            self._add_signal('Magento', self.ECOMMERCE_CATEGORY, 'markup', '/static/version', 6)
        if '/skin/frontend/' in body_lower:
            self._add_signal('Magento', self.ECOMMERCE_CATEGORY, 'markup', '/skin/frontend/', 5)
        if 'magento_ui/js' in body_lower or 'mage/cookies' in body_lower:
            self._add_signal('Magento', self.ECOMMERCE_CATEGORY, 'script', 'Magento_Ui/js|mage/cookies', 5)
        if 'form_key' in body_lower:
            self._add_signal('Magento', self.ECOMMERCE_CATEGORY, 'markup', 'form_key', 3)

        # Shopify
        if 'cdn.shopify.com' in body_lower:
            self._add_signal('Shopify', self.ECOMMERCE_CATEGORY, 'asset', 'cdn.shopify.com', 7)
        if 'shopify.theme' in body_lower or 'shopify-section' in body_lower or 'shopify-payment-button' in body_lower:
            self._add_signal('Shopify', self.ECOMMERCE_CATEGORY, 'script', 'Shopify.theme|shopify-section', 6)
        if any(cookie.startswith('_shopify') for cookie in cookies):
            self._add_signal('Shopify', self.ECOMMERCE_CATEGORY, 'cookie', '_shopify*', 6)
        if 'x-shopid' in headers or 'shopify' in server:
            self._add_signal('Shopify', self.ECOMMERCE_CATEGORY, 'header', 'x-shopid|server', 6)

        # Bitrix
        if '/bitrix/' in body_lower:
            self._add_signal('Bitrix', self.CMS_CATEGORY, 'markup', '/bitrix/', 6)
        if 'window.bx' in body_lower or 'bx.message' in body_lower or 'bx.setcsslist' in body_lower:
            self._add_signal('Bitrix', self.CMS_CATEGORY, 'script', 'BX.*', 6)
        if any(cookie.startswith('bitrix') for cookie in cookies):
            self._add_signal('Bitrix', self.CMS_CATEGORY, 'cookie', 'bitrix*', 6)
        if probe_statuses.get('/bitrix/') in [200, 301, 302, 401, 403]:
            self._add_signal('Bitrix', self.CMS_CATEGORY, 'endpoint', '/bitrix/', 4)

        # Wix
        if 'static.parastorage.com' in body_lower or 'wixstatic.com' in body_lower:
            self._add_signal('Wix', self.SITE_BUILDER_CATEGORY, 'asset', 'static.parastorage.com|wixstatic.com', 7)
        if 'x-wix-request-id' in headers:
            self._add_signal('Wix', self.SITE_BUILDER_CATEGORY, 'header', 'x-wix-request-id', 6)
        if 'wix-code-sdk' in body_lower or 'wix-image' in body_lower:
            self._add_signal('Wix', self.SITE_BUILDER_CATEGORY, 'markup', 'wix-code-sdk|wix-image', 5)

        # Tilda
        if 'tilda-blocks-' in body_lower or 'tilda-page' in body_lower:
            self._add_signal('Tilda', self.SITE_BUILDER_CATEGORY, 'markup', 'tilda-blocks-|tilda-page', 7)
        if 'static.tildacdn.' in body_lower:
            self._add_signal('Tilda', self.SITE_BUILDER_CATEGORY, 'asset', 'static.tildacdn.', 7)
        if 'tilda-pub-' in body_lower:
            self._add_signal('Tilda', self.SITE_BUILDER_CATEGORY, 'markup', 'tilda-pub-', 4)

        # Webflow
        if 'webflow' in generator_lower:
            self._add_signal('Webflow', self.SITE_BUILDER_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'webflow.css' in body_lower or 'w-webflow-' in body_lower:
            self._add_signal('Webflow', self.SITE_BUILDER_CATEGORY, 'asset', 'webflow.css|w-webflow-*', 7)
        if 'data-wf-page=' in body_lower or 'data-wf-site=' in body_lower:
            self._add_signal('Webflow', self.SITE_BUILDER_CATEGORY, 'markup', 'data-wf-page|data-wf-site', 6)

        # Squarespace
        if 'squarespace' in generator_lower:
            self._add_signal('Squarespace', self.SITE_BUILDER_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'static1.squarespace.com' in body_lower or 'squarespace-cdn.com' in body_lower:
            self._add_signal('Squarespace', self.SITE_BUILDER_CATEGORY, 'asset', 'static1.squarespace.com|squarespace-cdn.com', 7)
        if 'sqs-block-content' in body_lower or 'squarespace-announcement-bar-dropzone' in body_lower:
            self._add_signal('Squarespace', self.SITE_BUILDER_CATEGORY, 'markup', 'sqs-block-content', 6)

        # Ghost
        if 'ghost' in generator_lower:
            self._add_signal('Ghost', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if '/ghost/api/content/' in body_lower:
            self._add_signal('Ghost', self.CMS_CATEGORY, 'asset', '/ghost/api/content/', 7)
        if probe_statuses.get('/ghost/api/content/') in [200, 401, 403]:
            self._add_signal('Ghost', self.CMS_CATEGORY, 'endpoint', '/ghost/api/content/', 5)
        if 'ghost-content' in body_lower or 'casper' in body_lower:
            self._add_signal('Ghost', self.CMS_CATEGORY, 'markup', 'ghost-content|casper', 4)

        # WooCommerce
        if '/wp-content/plugins/woocommerce/' in body_lower:
            self._add_signal('WooCommerce', self.ECOMMERCE_CATEGORY, 'asset', '/wp-content/plugins/woocommerce/', 7)
        if 'wc-ajax=' in body_lower:
            self._add_signal('WooCommerce', self.ECOMMERCE_CATEGORY, 'markup', 'wc-ajax=', 6)
        if 'woocommerce-notices-wrapper' in body_lower or 'add_to_cart_button' in body_lower:
            self._add_signal('WooCommerce', self.ECOMMERCE_CATEGORY, 'markup', 'woocommerce-notices-wrapper|add_to_cart_button', 5)
        if any(cookie.startswith('woocommerce_') or cookie.startswith('wp_woocommerce_session_') for cookie in cookies):
            self._add_signal('WooCommerce', self.ECOMMERCE_CATEGORY, 'cookie', 'woocommerce_*', 7)

        # OpenCart
        if 'index.php?route=' in body_lower or 'route=common/home' in body_lower:
            self._add_signal('OpenCart', self.ECOMMERCE_CATEGORY, 'markup', 'index.php?route=|route=common/home', 7)
        if '/catalog/view/theme/' in body_lower:
            self._add_signal('OpenCart', self.ECOMMERCE_CATEGORY, 'asset', '/catalog/view/theme/', 6)
        if 'ocsessid' in cookies:
            self._add_signal('OpenCart', self.ECOMMERCE_CATEGORY, 'cookie', 'OCSESSID', 7)
        if probe_statuses.get('/catalog/view/theme/') in [200, 301, 302, 401, 403]:
            self._add_signal('OpenCart', self.ECOMMERCE_CATEGORY, 'endpoint', '/catalog/view/theme/', 4)

        # PrestaShop
        if 'prestashop' in body_lower:
            self._add_signal('PrestaShop', self.ECOMMERCE_CATEGORY, 'markup', 'prestashop', 7)
        if any(cookie.startswith('prestashop-') for cookie in cookies):
            self._add_signal('PrestaShop', self.ECOMMERCE_CATEGORY, 'cookie', 'PrestaShop-*', 7)
        if ('/modules/' in body_lower or '/themes/' in body_lower) and 'prestashop' in body_lower:
            self._add_signal('PrestaShop', self.ECOMMERCE_CATEGORY, 'asset', '/modules/|/themes/', 4)

        # TYPO3
        if 'typo3.settings' in body_lower:
            self._add_signal('TYPO3', self.CMS_CATEGORY, 'script', 'TYPO3.settings', 7)
        if '/typo3/' in body_lower or '/typo3conf/' in body_lower or '/typo3temp/' in body_lower:
            self._add_signal('TYPO3', self.CMS_CATEGORY, 'asset', '/typo3/|/typo3conf/|/typo3temp/', 6)
        if any(probe_statuses.get(path) in [200, 301, 302, 401, 403] for path in ['/typo3/', '/typo3conf/', '/typo3temp/']):
            self._add_signal('TYPO3', self.CMS_CATEGORY, 'endpoint', '/typo3/*', 4)

        # Nextcloud
        if 'nextcloud' in generator_lower:
            self._add_signal('Nextcloud', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'nextcloud' in body_lower:
            self._add_signal('Nextcloud', self.CMS_CATEGORY, 'markup', 'nextcloud', 6)
        if '/apps/files/' in body_lower or '/ocs-provider/' in body_lower:
            self._add_signal('Nextcloud', self.CMS_CATEGORY, 'asset', '/apps/files/|/ocs-provider/', 5)
        if probe_statuses.get('/status.php') in [200, 401, 403]:
            self._add_signal('Nextcloud', self.CMS_CATEGORY, 'endpoint', '/status.php', 2)
        if probe_statuses.get('/remote.php/dav/') in [200, 401, 403, 405]:
            self._add_signal('Nextcloud', self.CMS_CATEGORY, 'endpoint', '/remote.php/dav/', 2)

        # ownCloud
        if 'owncloud' in generator_lower:
            self._add_signal('ownCloud', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'owncloud' in body_lower:
            self._add_signal('ownCloud', self.CMS_CATEGORY, 'markup', 'owncloud', 6)
        if '/core/js/oc.js' in body_lower or '/core/img/actions/' in body_lower:
            self._add_signal('ownCloud', self.CMS_CATEGORY, 'asset', '/core/js/oc.js|/core/img/actions/', 5)
        if probe_statuses.get('/ocs/v1.php/cloud/capabilities?format=json') in [200, 401, 403]:
            self._add_signal('ownCloud', self.CMS_CATEGORY, 'endpoint', '/ocs/v1.php/cloud/capabilities?format=json', 4)
        if probe_statuses.get('/status.php') in [200, 401, 403] and 'owncloud' in body_lower:
            self._add_signal('ownCloud', self.CMS_CATEGORY, 'endpoint', '/status.php + owncloud', 2)

        # phpMyAdmin
        if 'phpmyadmin' in generator_lower:
            self._add_signal('phpMyAdmin', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'phpmyadmin' in body_lower:
            self._add_signal('phpMyAdmin', self.CMS_CATEGORY, 'markup', 'phpmyadmin', 7)
        if '/themes/pmahomme/' in body_lower or 'pma_navigation' in body_lower or 'name="pma_username"' in body_lower:
            self._add_signal('phpMyAdmin', self.CMS_CATEGORY, 'markup', '/themes/pmahomme/|pma_navigation|pma_username', 5)
        if any(cookie in ['pma_lang', 'pma_collation_connection', 'pma_charset'] for cookie in cookies):
            self._add_signal('phpMyAdmin', self.CMS_CATEGORY, 'cookie', 'pma_lang|pma_collation_connection|pma_charset', 6)

        # phpBB
        if 'phpbb' in generator_lower:
            self._add_signal('phpBB', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'phpbb' in body_lower:
            self._add_signal('phpBB', self.CMS_CATEGORY, 'markup', 'phpbb', 6)
        if '/styles/prosilver/' in body_lower or 'prosilver' in body_lower:
            self._add_signal('phpBB', self.CMS_CATEGORY, 'asset', '/styles/prosilver/|prosilver', 6)
        if 'viewtopic.php' in body_lower or 'viewforum.php' in body_lower:
            self._add_signal('phpBB', self.CMS_CATEGORY, 'markup', 'viewtopic.php|viewforum.php', 3)
        if any(cookie.startswith('phpbb3_') or cookie.startswith('phpbb_') for cookie in cookies):
            self._add_signal('phpBB', self.CMS_CATEGORY, 'cookie', 'phpbb3_*|phpbb_*', 7)

        # Umbraco
        if 'umbraco' in generator_lower:
            self._add_signal('Umbraco', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'umbraco.sys.servervariables' in body_lower or '/umbraco/assets/' in body_lower or 'umb-app' in body_lower:
            self._add_signal('Umbraco', self.CMS_CATEGORY, 'markup', 'Umbraco.Sys.ServerVariables|/umbraco/assets/|umb-app', 7)
        if probe_statuses.get('/umbraco/') in [200, 301, 302, 401, 403]:
            self._add_signal('Umbraco', self.CMS_CATEGORY, 'endpoint', '/umbraco/', 4)

        # nopCommerce
        if 'nopcommerce' in generator_lower:
            self._add_signal('nopCommerce', self.ECOMMERCE_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'nopcommerce' in body_lower or 'powered by nopcommerce' in body_lower:
            self._add_signal('nopCommerce', self.ECOMMERCE_CATEGORY, 'markup', 'nopcommerce|Powered by nopCommerce', 7)
        if probe_statuses.get('/admin') in [200, 301, 302, 401, 403] and 'nopcommerce' in body_lower:
            self._add_signal('nopCommerce', self.ECOMMERCE_CATEGORY, 'endpoint', '/admin + nopcommerce', 4)

        # Shopware
        shopware_hint = 'shopware' in generator_lower or 'shopware' in body_lower

        if 'shopware' in generator_lower:
            self._add_signal('Shopware', self.ECOMMERCE_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'shopware' in body_lower:
            self._add_signal('Shopware', self.ECOMMERCE_CATEGORY, 'markup', 'shopware', 6)
        if '/theme/' in body_lower and '/widgets/' in body_lower and shopware_hint:
            self._add_signal('Shopware', self.ECOMMERCE_CATEGORY, 'asset', '/theme/ + /widgets/', 5)
        if 'csrf-token' in body_lower and 'shopware' in body_lower:
            self._add_signal('Shopware', self.ECOMMERCE_CATEGORY, 'markup', 'csrf-token + shopware', 3)
        if probe_statuses.get('/backend') in [200, 301, 302, 401, 403] and shopware_hint:
            self._add_signal('Shopware', self.ECOMMERCE_CATEGORY, 'endpoint', '/backend', 4)

        # OctoberCMS
        october_cookie_hint = any(cookie in ['october_session', 'october_session_cookie'] for cookie in cookies)
        october_hint = (
            'octobercms' in generator_lower
            or 'october cms' in generator_lower
            or 'octobercms' in body_lower
            or 'october cms' in body_lower
            or october_cookie_hint
        )

        if 'octobercms' in generator_lower or 'october cms' in generator_lower:
            self._add_signal('OctoberCMS', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'octobercms' in body_lower or 'october cms' in body_lower:
            self._add_signal('OctoberCMS', self.CMS_CATEGORY, 'markup', 'OctoberCMS|October CMS', 6)
        if '/themes/' in body_lower and '/modules/system/' in body_lower and october_hint:
            self._add_signal('OctoberCMS', self.CMS_CATEGORY, 'asset', '/themes/ + /modules/system/', 5)
        if october_cookie_hint:
            self._add_signal('OctoberCMS', self.CMS_CATEGORY, 'cookie', 'october_session*', 6)
        if probe_statuses.get('/backend') in [200, 301, 302, 401, 403] and october_hint:
            self._add_signal('OctoberCMS', self.CMS_CATEGORY, 'endpoint', '/backend', 3)

        # Concrete CMS
        if 'concrete cms' in generator_lower or 'concrete5' in generator_lower:
            self._add_signal('Concrete CMS', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'concrete cms' in body_lower or 'concrete5' in body_lower:
            self._add_signal('Concrete CMS', self.CMS_CATEGORY, 'markup', 'Concrete CMS|concrete5', 6)
        if '/concrete/css/' in body_lower or '/concrete/js/' in body_lower:
            self._add_signal('Concrete CMS', self.CMS_CATEGORY, 'asset', '/concrete/css/|/concrete/js/', 6)
        if 'ccm-page' in body_lower or 'ccm-block-' in body_lower:
            self._add_signal('Concrete CMS', self.CMS_CATEGORY, 'markup', 'ccm-page|ccm-block-*', 4)

        # Contao
        if 'contao' in generator_lower:
            self._add_signal('Contao', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if '/bundles/contaocore/' in body_lower or '/files/contao' in body_lower:
            self._add_signal('Contao', self.CMS_CATEGORY, 'asset', '/bundles/contaocore/|/files/contao', 6)
        if 'contao' in body_lower:
            self._add_signal('Contao', self.CMS_CATEGORY, 'markup', 'contao', 4)
        if probe_statuses.get('/contao/') in [200, 301, 302, 401, 403]:
            self._add_signal('Contao', self.CMS_CATEGORY, 'endpoint', '/contao/', 4)

        # GravCMS
        if 'gravcms' in generator_lower or 'grav cms' in generator_lower or 'grav' in generator_lower:
            self._add_signal('GravCMS', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if '/user/themes/' in body_lower and '/system/assets/' in body_lower:
            self._add_signal('GravCMS', self.CMS_CATEGORY, 'asset', '/user/themes/ + /system/assets/', 6)
        if 'grav-' in body_lower or 'grav-language-select' in body_lower:
            self._add_signal('GravCMS', self.CMS_CATEGORY, 'markup', 'grav-*', 4)
        if 'gravcms' in body_lower or 'grav cms' in body_lower:
            self._add_signal('GravCMS', self.CMS_CATEGORY, 'markup', 'GravCMS|Grav CMS', 5)

        # MediaWiki
        if 'mediawiki' in generator_lower:
            self._add_signal('MediaWiki', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'mediawiki' in body_lower:
            self._add_signal('MediaWiki', self.CMS_CATEGORY, 'markup', 'mediawiki', 5)
        if '/w/resources/' in body_lower or 'mw-body' in body_lower or 'mw-page-title-main' in body_lower:
            self._add_signal('MediaWiki', self.CMS_CATEGORY, 'asset', '/w/resources/|mw-body|mw-page-title-main', 6)
        if probe_statuses.get('/api.php') in [200, 301, 302, 401, 403]:
            self._add_signal('MediaWiki', self.CMS_CATEGORY, 'endpoint', '/api.php', 2)

        # Moodle
        if 'moodle' in generator_lower:
            self._add_signal('Moodle', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'moodle' in body_lower:
            self._add_signal('Moodle', self.CMS_CATEGORY, 'markup', 'moodle', 4)
        if '/theme/image.php/' in body_lower or '/lib/javascript.php/' in body_lower:
            self._add_signal('Moodle', self.CMS_CATEGORY, 'asset', '/theme/image.php/|/lib/javascript.php/', 6)
        if any(cookie.startswith('moodlesession') for cookie in cookies):
            self._add_signal('Moodle', self.CMS_CATEGORY, 'cookie', 'MoodleSession*', 7)
        if probe_statuses.get('/login/index.php') in [200, 301, 302, 401, 403] and ('moodle' in body_lower or any(cookie.startswith('moodlesession') for cookie in cookies)):
            self._add_signal('Moodle', self.CMS_CATEGORY, 'endpoint', '/login/index.php', 3)

        # Pimcore
        pimcore_text_hint = (
            'pimcore' in generator_lower
            or '>pimcore<' in body_lower
            or ' content="pimcore' in body_lower
            or " content='pimcore" in body_lower
        )

        if 'pimcore' in generator_lower:
            self._add_signal('Pimcore', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if '>pimcore<' in body_lower:
            self._add_signal('Pimcore', self.CMS_CATEGORY, 'markup', 'pimcore', 5)
        if ('/bundles/pimcoreadmin/' in body_lower or '/bundles/pimcorestatic6/' in body_lower) and pimcore_text_hint:
            self._add_signal('Pimcore', self.CMS_CATEGORY, 'asset', '/bundles/pimcoreadmin/|/bundles/pimcorestatic6/', 7)
        if '/admin/login' in body_lower and pimcore_text_hint:
            self._add_signal('Pimcore', self.CMS_CATEGORY, 'markup', '/admin/login', 3)
        if probe_statuses.get('/admin') in [200, 301, 302, 401, 403] and pimcore_text_hint:
            self._add_signal('Pimcore', self.CMS_CATEGORY, 'endpoint', '/admin + pimcore', 3)

        # Discourse
        discourse_marker_hint = (
            'discourse' in generator_lower
            or 'discourse-topic' in body_lower
            or 'discourse-post' in body_lower
            or 'data-discourse-setup' in body_lower
        )
        discourse_cookie_hint = any(cookie in ['_forum_session', 'discourse_sid'] for cookie in cookies)

        if 'discourse' in generator_lower:
            self._add_signal('Discourse', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'discourse-topic' in body_lower or 'discourse-post' in body_lower or 'data-discourse-setup' in body_lower:
            self._add_signal('Discourse', self.CMS_CATEGORY, 'markup', 'discourse-topic|discourse-post|data-discourse-setup', 7)
        if discourse_cookie_hint and discourse_marker_hint:
            self._add_signal('Discourse', self.CMS_CATEGORY, 'cookie', '_forum_session|discourse_sid', 7)
        if '/uploads/default/' in body_lower and (discourse_marker_hint or discourse_cookie_hint):
            self._add_signal('Discourse', self.CMS_CATEGORY, 'asset', '/uploads/default/', 4)

        # Matomo
        matomo_cookie_hint = any(cookie in ['pk_id', 'pk_ses'] or cookie.startswith('_pk_') for cookie in cookies)
        matomo_tracker_hint = (
            'matomo' in generator_lower
            or '_paq.push' in body_lower
            or 'var _paq =' in body_lower
        )

        if 'matomo' in generator_lower:
            self._add_signal('Matomo', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if '_paq.push' in body_lower or 'var _paq =' in body_lower:
            self._add_signal('Matomo', self.CMS_CATEGORY, 'script', '_paq.push|var _paq', 7)
        if ('matomo.js' in body_lower or 'matomo.php' in body_lower) and (matomo_tracker_hint or matomo_cookie_hint):
            self._add_signal('Matomo', self.CMS_CATEGORY, 'asset', 'matomo.js|matomo.php', 7)
        if matomo_cookie_hint and (matomo_tracker_hint or 'matomo.js' in body_lower or 'matomo.php' in body_lower):
            self._add_signal('Matomo', self.CMS_CATEGORY, 'cookie', 'pk_id|pk_ses|_pk_*', 6)

        # Bludit
        if 'bludit' in generator_lower:
            self._add_signal('Bludit', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if '/bl-themes/' in body_lower or '/bl-content/' in body_lower:
            self._add_signal('Bludit', self.CMS_CATEGORY, 'asset', '/bl-themes/|/bl-content/', 7)
        if 'bludit' in body_lower:
            self._add_signal('Bludit', self.CMS_CATEGORY, 'markup', 'bludit', 4)
        if probe_statuses.get('/admin') in [200, 301, 302, 401, 403] and '/bl-themes/' in body_lower:
            self._add_signal('Bludit', self.CMS_CATEGORY, 'endpoint', '/admin + /bl-themes/', 3)

        # MODX
        modx_hint = (
            'modx' in generator_lower
            or 'modx revolution' in body_lower
            or '>modx<' in body_lower
        )

        if 'modx' in generator_lower:
            self._add_signal('MODX', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if '/assets/components/' in body_lower and modx_hint:
            self._add_signal('MODX', self.CMS_CATEGORY, 'asset', '/assets/components/', 7)
        if ('/manager/' in body_lower or 'modx revolution' in body_lower or '>modx<' in body_lower) and modx_hint:
            self._add_signal('MODX', self.CMS_CATEGORY, 'markup', '/manager/|MODX Revolution|modx', 4)
        if probe_statuses.get('/manager/') in [200, 301, 302, 401, 403] and modx_hint:
            self._add_signal('MODX', self.CMS_CATEGORY, 'endpoint', '/manager/', 4)

        # Neos
        neos_text_hint = (
            'neos' in generator_lower
            or 'typo3 neos' in generator_lower
            or 'neos-contentcollection' in body_lower
            or 'typo3 neos' in body_lower
        )

        if 'neos' in generator_lower or 'typo3 neos' in generator_lower:
            self._add_signal('Neos', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if '/_resources/static/packages/' in body_lower and neos_text_hint:
            self._add_signal('Neos', self.CMS_CATEGORY, 'asset', '/_Resources/Static/Packages/', 7)
        if 'neos-contentcollection' in body_lower or 'typo3 neos' in body_lower:
            self._add_signal('Neos', self.CMS_CATEGORY, 'markup', 'neos-contentcollection|TYPO3 Neos', 4)

        # Craft CMS
        craft_cookie_hint = any(cookie in ['craftsessionid', 'craft_csrf_token'] for cookie in cookies)
        craft_text_hint = (
            'craft cms' in generator_lower
            or 'craftcms' in generator_lower
            or 'craft cms' in body_lower
            or 'craftcms' in body_lower
        )
        craft_asset_hint = '/cpresources/' in body_lower

        if 'craft cms' in generator_lower or 'craftcms' in generator_lower:
            self._add_signal('Craft CMS', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'craft cms' in body_lower or 'craftcms' in body_lower:
            self._add_signal('Craft CMS', self.CMS_CATEGORY, 'markup', 'Craft CMS|craftcms', 4)
        if craft_asset_hint and (craft_text_hint or craft_cookie_hint):
            self._add_signal('Craft CMS', self.CMS_CATEGORY, 'asset', '/cpresources/', 7)
        if craft_cookie_hint and (craft_text_hint or craft_asset_hint):
            self._add_signal('Craft CMS', self.CMS_CATEGORY, 'cookie', 'CraftSessionId|CRAFT_CSRF_TOKEN', 6)
        if probe_statuses.get('/admin') in [200, 301, 302, 401, 403] and craft_asset_hint and (craft_text_hint or craft_cookie_hint):
            self._add_signal('Craft CMS', self.CMS_CATEGORY, 'endpoint', '/admin + /cpresources/', 3)

        # Bolt CMS
        bolt_hint = 'bolt' in generator_lower or 'bolt' in x_powered_by

        if 'bolt' in generator_lower or 'bolt cms' in generator_lower:
            self._add_signal('Bolt CMS', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'bolt' in x_powered_by:
            self._add_signal('Bolt CMS', self.CMS_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by')), 6)
        if ('/bolt/' in body_lower or 'href="/bolt"' in body_lower or "href='/bolt'" in body_lower) and bolt_hint:
            self._add_signal('Bolt CMS', self.CMS_CATEGORY, 'markup', '/bolt', 2)
        if probe_statuses.get('/bolt') in [200, 301, 302, 401, 403] and bolt_hint:
            self._add_signal('Bolt CMS', self.CMS_CATEGORY, 'endpoint', '/bolt', 4)

        # Directus
        directus_title_hint = '<title>directus' in body_lower
        directus_hint = 'directus' in generator_lower or directus_title_hint

        if 'directus' in generator_lower:
            self._add_signal('Directus', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if directus_title_hint:
            self._add_signal('Directus', self.CMS_CATEGORY, 'markup', '<title>Directus', 4)
        if '/admin/assets/' in body_lower and directus_hint:
            self._add_signal('Directus', self.CMS_CATEGORY, 'asset', '/admin/assets/', 6)
        if probe_statuses.get('/admin') in [200, 301, 302, 401, 403] and '/admin/assets/' in body_lower and directus_hint:
            self._add_signal('Directus', self.CMS_CATEGORY, 'endpoint', '/admin + /admin/assets/', 4)

        # Strapi
        if 'strapi' in x_powered_by:
            self._add_signal('Strapi', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by')), 8)
        if '/admin/init' in body_lower or ('strapi' in body_lower and '/uploads/' in body_lower):
            self._add_signal('Strapi', self.FRAMEWORK_CATEGORY, 'markup', '/admin/init|strapi + /uploads/', 7)
        if probe_statuses.get('/admin/init') in [200, 301, 302, 401, 403]:
            self._add_signal('Strapi', self.FRAMEWORK_CATEGORY, 'endpoint', '/admin/init', 7)
        if probe_statuses.get('/admin') in [200, 301, 302, 401, 403]:
            self._add_signal('Strapi', self.FRAMEWORK_CATEGORY, 'endpoint', '/admin', 4)
        if probe_statuses.get('/uploads/') in [200, 301, 302, 401, 403]:
            self._add_signal('Strapi', self.FRAMEWORK_CATEGORY, 'endpoint', '/uploads/', 4)

        # MkDocs / Jekyll / Hugo / VitePress
        if 'mkdocs' in generator_lower:
            self._add_signal('MkDocs', self.STATIC_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'mkdocs_page_name' in body_lower or 'mkdocs_page_input_path' in body_lower:
            self._add_signal('MkDocs', self.STATIC_CATEGORY, 'markup', 'mkdocs_page_name|mkdocs_page_input_path', 6)
        if 'jekyll' in generator_lower:
            self._add_signal('Jekyll', self.STATIC_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'begin jekyll seo tag' in body_lower:
            self._add_signal('Jekyll', self.STATIC_CATEGORY, 'markup', 'Begin Jekyll SEO tag', 6)
        if 'hugo' in generator_lower:
            self._add_signal('Hugo', self.STATIC_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'vitepress' in body_lower or 'vpcontent' in body_lower or 'vpnav' in body_lower:
            self._add_signal('VitePress', self.STATIC_CATEGORY, 'markup', 'vitepress|VPContent|VPNav', 7)

        # Docusaurus
        if 'docusaurus' in generator_lower:
            self._add_signal('Docusaurus', self.STATIC_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
        if 'docusaurus' in body_lower and '/assets/js/runtime~main' in body_lower:
            self._add_signal('Docusaurus', self.STATIC_CATEGORY, 'asset', 'docusaurus runtime', 6)
        if 'data-rh="true"' in body_lower and 'docusaurus' in body_lower:
            self._add_signal('Docusaurus', self.STATIC_CATEGORY, 'markup', 'data-rh + docusaurus', 5)

        # Next.js
        if '/_next/static/' in body_lower:
            self._add_signal('Next.js', self.FRAMEWORK_CATEGORY, 'asset', '/_next/static/', 7)
        if '__next_data__' in body_lower:
            self._add_signal('Next.js', self.FRAMEWORK_CATEGORY, 'script', '__NEXT_DATA__', 7)
        if 'next-head-count' in body_lower or '__next' in body_lower:
            self._add_signal('Next.js', self.FRAMEWORK_CATEGORY, 'markup', 'next-head-count|__next', 4)
        if probe_statuses.get('/_next/static/') in [200, 301, 302, 401, 403]:
            self._add_signal('Next.js', self.FRAMEWORK_CATEGORY, 'endpoint', '/_next/static/', 4)

        # Nuxt
        if '/_nuxt/' in body_lower:
            self._add_signal('Nuxt', self.FRAMEWORK_CATEGORY, 'asset', '/_nuxt/', 7)
        if '__nuxt__' in body_lower or '__nuxt_data__' in body_lower:
            self._add_signal('Nuxt', self.FRAMEWORK_CATEGORY, 'script', '__NUXT__', 7)
        if probe_statuses.get('/_nuxt/') in [200, 301, 302, 401, 403]:
            self._add_signal('Nuxt', self.FRAMEWORK_CATEGORY, 'endpoint', '/_nuxt/', 4)

        # Gatsby
        if '/page-data/' in body_lower and 'webpack-runtime' in body_lower:
            self._add_signal('Gatsby', self.FRAMEWORK_CATEGORY, 'asset', '/page-data/ + webpack-runtime', 7)
        if '___gatsby' in body_lower or 'gatsby-script-loader' in body_lower:
            self._add_signal('Gatsby', self.FRAMEWORK_CATEGORY, 'script', '___gatsby|gatsby-script-loader', 6)

        # Astro
        if 'astro-island' in body_lower:
            self._add_signal('Astro', self.FRAMEWORK_CATEGORY, 'markup', 'astro-island', 8)
        if '/_astro/' in body_lower:
            self._add_signal('Astro', self.FRAMEWORK_CATEGORY, 'asset', '/_astro/', 7)

        # Remix
        if 'window.__remixcontext' in body_lower or 'window.__remixroute' in body_lower:
            self._add_signal('Remix', self.FRAMEWORK_CATEGORY, 'script', '__remixContext', 8)
        if '/build/' in body_lower and probe_statuses.get('/build/') in [200, 301, 302, 401, 403]:
            self._add_signal('Remix', self.FRAMEWORK_CATEGORY, 'asset', '/build/', 4)

        # Angular / React / Vue / SvelteKit
        if 'ng-version=' in body_lower or '<app-root' in body_lower:
            self._add_signal('Angular', self.FRAMEWORK_CATEGORY, 'markup', 'ng-version|app-root', 7)
        if 'data-reactroot' in body_lower or 'id="root"' in body_lower or "id='root'" in body_lower:
            self._add_signal('React', self.FRAMEWORK_CATEGORY, 'markup', 'data-reactroot|#root', 4)
        if 'data-server-rendered="true"' in body_lower:
            self._add_signal('Vue', self.FRAMEWORK_CATEGORY, 'markup', 'data-server-rendered=true', 5)
        if 'sveltekit' in body_lower or 'data-sveltekit' in body_lower:
            self._add_signal('SvelteKit', self.FRAMEWORK_CATEGORY, 'markup', 'sveltekit', 7)

        # Laravel
        if 'laravel_session' in cookies:
            self._add_signal('Laravel', self.FRAMEWORK_CATEGORY, 'cookie', 'laravel_session', 7)
        if 'xsrf-token' in cookies:
            self._add_signal('Laravel', self.FRAMEWORK_CATEGORY, 'cookie', 'XSRF-TOKEN', 2)
        if 'csrf-token' in body_lower and 'laravel' in body_lower:
            self._add_signal('Laravel', self.FRAMEWORK_CATEGORY, 'markup', 'csrf-token + laravel', 4)

        # Django
        if 'csrftoken' in cookies:
            self._add_signal('Django', self.FRAMEWORK_CATEGORY, 'cookie', 'csrftoken', 5)
        if 'csrfmiddlewaretoken' in body_lower:
            self._add_signal('Django', self.FRAMEWORK_CATEGORY, 'markup', 'csrfmiddlewaretoken', 7)
        if 'sessionid' in cookies and 'csrftoken' in cookies:
            self._add_signal('Django', self.FRAMEWORK_CATEGORY, 'cookie', 'sessionid', 2)

        # Flask
        if 'flask' in x_powered_by:
            self._add_signal('Flask', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by')), 8)
        if 'werkzeug' in server:
            self._add_signal('Flask', self.FRAMEWORK_CATEGORY, 'header', 'server={0}'.format(headers.get('server')), 7)

        # Ruby on Rails
        if '_rails_session' in cookies:
            self._add_signal('Ruby on Rails', self.FRAMEWORK_CATEGORY, 'cookie', '_rails_session', 8)
        if 'csrf-param' in body_lower and 'csrf-token' in body_lower:
            self._add_signal('Ruby on Rails', self.FRAMEWORK_CATEGORY, 'markup', 'csrf-param|csrf-token', 5)

        # Express / NestJS / Fastify / FastAPI / Koa / Hapi
        if 'express' in x_powered_by or 'express' in not_found_powered_by:
            self._add_signal('Express', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by') or not_found_headers.get('x-powered-by')), 8)
        if 'connect.sid' in cookies:
            self._add_signal('Express', self.FRAMEWORK_CATEGORY, 'cookie', 'connect.sid', 6)
        if not_found_status == 404 and ('cannot get /' in not_found_body_lower or 'cannot post /' in not_found_body_lower):
            self._add_signal('Express', self.FRAMEWORK_CATEGORY, '404', 'Cannot GET/POST', 7)

        if 'nest' in x_powered_by or 'nest' in not_found_powered_by:
            self._add_signal('NestJS', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by') or not_found_headers.get('x-powered-by')), 8)
        if not_found_status == 404 and 'statuscode' in not_found_body_lower and 'cannot get /' in not_found_body_lower and 'not found' in not_found_body_lower:
            self._add_signal('NestJS', self.FRAMEWORK_CATEGORY, '404', 'statusCode + Cannot GET + Not Found', 9)
        if swagger_probe_up:
            self._add_signal('NestJS', self.FRAMEWORK_CATEGORY, 'endpoint', 'swagger/openapi', 4)

        if 'fastify' in x_powered_by or 'fastify' in server or 'fastify' in not_found_powered_by or 'fastify' in not_found_server:
            self._add_signal('Fastify', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by|server=fastify', 8)
        if not_found_status == 404 and 'route get:' in not_found_body_lower and 'not found' in not_found_body_lower:
            self._add_signal('Fastify', self.FRAMEWORK_CATEGORY, '404', 'Route GET:* not found', 9)

        if 'uvicorn' in server or 'hypercorn' in server or 'uvicorn' in not_found_server or 'hypercorn' in not_found_server:
            self._add_signal('FastAPI', self.FRAMEWORK_CATEGORY, 'header', 'server=uvicorn|hypercorn', 6)
        if not_found_status == 404 and '"detail"' in not_found_body_lower and 'not found' in not_found_body_lower:
            self._add_signal('FastAPI', self.FRAMEWORK_CATEGORY, '404', '{"detail":"Not Found"}', 8)
        if probe_statuses.get('/openapi.json') in [200, 301, 302, 401, 403] or docs_probe_up:
            self._add_signal('FastAPI', self.FRAMEWORK_CATEGORY, 'endpoint', '/openapi.json|/docs|/redoc', 5)

        if 'koa' in x_powered_by or 'koa' in not_found_powered_by:
            self._add_signal('Koa', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by') or not_found_headers.get('x-powered-by')), 8)
        if 'koa:sess' in cookies or 'koa.sess' in cookies:
            self._add_signal('Koa', self.FRAMEWORK_CATEGORY, 'cookie', 'koa:sess|koa.sess', 7)

        if 'hapi' in x_powered_by or 'hapi' in not_found_powered_by:
            self._add_signal('Hapi', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by') or not_found_headers.get('x-powered-by')), 8)
        if not_found_status == 404 and '"statuscode":404' in not_found_body_lower and '"error":"not found"' in not_found_body_lower and '"message":"not found"' in not_found_body_lower:
            self._add_signal('Hapi', self.FRAMEWORK_CATEGORY, '404', 'statusCode/error/message Not Found', 7)

        # Symfony
        if 'symfony' in x_powered_by:
            self._add_signal('Symfony', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by')), 8)
        if 'sf_redirect' in cookies or 'sf_site' in cookies:
            self._add_signal('Symfony', self.FRAMEWORK_CATEGORY, 'cookie', 'sf_*', 6)

        # ASP.NET
        if 'asp.net' in x_powered_by:
            self._add_signal('ASP.NET', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by')), 8)
        if 'x-aspnet-version' in headers:
            self._add_signal('ASP.NET', self.FRAMEWORK_CATEGORY, 'header', 'x-aspnet-version', 8)
        if 'asp.net_sessionid' in cookies:
            self._add_signal('ASP.NET', self.FRAMEWORK_CATEGORY, 'cookie', 'ASP.NET_SessionId', 6)
        if '__viewstate' in body_lower or '__eventvalidation' in body_lower:
            self._add_signal('ASP.NET', self.FRAMEWORK_CATEGORY, 'markup', '__VIEWSTATE|__EVENTVALIDATION', 7)

        # Spring
        if 'jsessionid' in cookies and ('spring' in body_lower or 'thymeleaf' in body_lower):
            self._add_signal('Spring', self.FRAMEWORK_CATEGORY, 'cookie', 'JSESSIONID + spring/thymeleaf', 6)
        if 'thymeleaf' in body_lower:
            self._add_signal('Spring', self.FRAMEWORK_CATEGORY, 'markup', 'thymeleaf', 7)

        # Phoenix
        if '_csrf_token' in body_lower and ('phoenix' in body_lower or '_buildinfo' in body_lower):
            self._add_signal('Phoenix', self.FRAMEWORK_CATEGORY, 'markup', '_csrf_token + phoenix', 7)
        if '_app_key' in cookies:
            self._add_signal('Phoenix', self.FRAMEWORK_CATEGORY, 'cookie', '_app_key', 5)

        # Infrastructure: AWS family
        if x_amz_cf_id or 'cloudfront' in via or 'cloudfront' in x_cache or 'cloudfront' in server:
            self._add_infrastructure_signal('AWS CloudFront', 'header', 'x-amz-cf-id|via|x-cache', 9)
        if 'x-amz-cf-pop' in headers:
            self._add_infrastructure_signal('AWS CloudFront', 'header', 'x-amz-cf-pop', 8)
        if x_amz_request_id or x_amz_id_2:
            self._add_infrastructure_signal('AWS S3', 'header', 'x-amz-request-id|x-amz-id-2', 8)
        if self._header_contains(headers, 'server', 'amazons3'):
            self._add_infrastructure_signal('AWS S3', 'header', 'server=AmazonS3', 9)
        if '.s3.' in final_root_lower or '.amazonaws.com' in final_root_lower:
            self._add_infrastructure_signal('AWS', 'url', 'amazonaws.com', 4)
        if self._header_contains(headers, 'server', 'awselb/2.0') or 'x-amzn-trace-id' in headers:
            self._add_infrastructure_signal('AWS ELB / ALB', 'header', 'awselb/2.0|x-amzn-trace-id', 8)
        if 'x-amz-apigw-id' in headers:
            self._add_infrastructure_signal('AWS API Gateway', 'header', 'x-amz-apigw-id', 9)
        if 'x-amplify-id' in headers or 'x-amz-meta-amplify-app-id' in headers:
            self._add_infrastructure_signal('AWS Amplify', 'header', 'x-amplify-id', 9)

        # Cloudflare
        if 'cf-ray' in headers or 'cloudflare' in server:
            self._add_infrastructure_signal('Cloudflare', 'header', 'cf-ray|server=cloudflare', 9)
        if 'cf-cache-status' in headers:
            self._add_infrastructure_signal('Cloudflare', 'header', 'cf-cache-status', 8)

        # Vercel
        if 'x-vercel-id' in headers or 'x-vercel-cache' in headers:
            self._add_infrastructure_signal('Vercel', 'header', 'x-vercel-id|x-vercel-cache', 9)
        if self._header_contains(headers, 'server', 'vercel'):
            self._add_infrastructure_signal('Vercel', 'header', 'server=Vercel', 8)

        # Netlify
        if 'x-nf-request-id' in headers or 'netlify' in server:
            self._add_infrastructure_signal('Netlify', 'header', 'x-nf-request-id|server=Netlify', 9)

        # GitHub Pages
        if 'github-pages' in server or 'x-github-request-id' in headers:
            self._add_infrastructure_signal('GitHub Pages', 'header', 'server=GitHub-Pages|x-github-request-id', 9)

        # GitLab Pages
        if 'gitlab-pages' in server or 'gitlab pages' in server:
            self._add_infrastructure_signal('GitLab Pages', 'header', 'server=GitLab Pages', 9)

        # Heroku
        if 'x-request-id' in headers and 'via' in headers and 'heroku' in via:
            self._add_infrastructure_signal('Heroku', 'header', 'via=heroku', 9)
        if 'x-heroku-queue-wait-time' in headers or 'x-heroku-dynos-in-use' in headers:
            self._add_infrastructure_signal('Heroku', 'header', 'x-heroku-*', 9)

        # Azure
        if 'x-azure-ref' in headers or 'x-ms-request-id' in headers:
            self._add_infrastructure_signal('Microsoft Azure', 'header', 'x-azure-ref|x-ms-request-id', 9)
        if '.azurewebsites.net' in final_root_lower:
            self._add_infrastructure_signal('Microsoft Azure App Service', 'url', 'azurewebsites.net', 8)

        # GCP
        if 'x-cloud-trace-context' in headers:
            self._add_infrastructure_signal('Google Cloud', 'header', 'x-cloud-trace-context', 9)
        if self._header_contains(headers, 'server', 'gse'):
            self._add_infrastructure_signal('Google Cloud / Google Frontend', 'header', 'server=gse', 8)
        if '.run.app' in final_root_lower:
            self._add_infrastructure_signal('Google Cloud Run', 'url', 'run.app', 8)
        if '.appspot.com' in final_root_lower:
            self._add_infrastructure_signal('Google App Engine', 'url', 'appspot.com', 8)

        # Fastly / Akamai / OpenResty
        if 'fastly' in x_served_by or 'x-fastly-request-id' in headers:
            self._add_infrastructure_signal('Fastly', 'header', 'x-served-by|x-fastly-request-id', 9)
        if 'akamai' in server or 'akamai-grn' in headers:
            self._add_infrastructure_signal('Akamai', 'header', 'server=akamai|akamai-grn', 9)
        if 'openresty' in server:
            self._add_infrastructure_signal('OpenResty', 'header', 'server=openresty', 5)

    def _build_candidates(self):
        """
        Build sorted application candidate list.

        :return: list[dict]
        """

        candidates = []
        for technology, score in self.__scores.items():
            candidates.append({
                'name': technology,
                'category': self.__categories.get(technology, self.CUSTOM_CATEGORY),
                'score': round(float(score), 2),
            })

        candidates.sort(key=lambda item: (-item['score'], item['name']))
        return candidates

    def _build_infrastructure_candidates(self):
        """
        Build sorted infrastructure candidate list.

        :return: list[dict]
        """

        candidates = []
        for provider, score in self.__infra_scores.items():
            candidates.append({
                'provider': provider,
                'score': round(float(score), 2),
            })

        candidates.sort(key=lambda item: (-item['score'], item['provider']))
        return candidates

    def _build_infrastructure_result(self, infra_candidates):
        """
        Build infrastructure result payload.

        :param list infra_candidates:
        :return: dict
        """

        if len(infra_candidates) <= 0:
            return {
                'provider': 'unknown',
                'confidence': 0,
                'signals': [],
                'candidates': [],
            }

        top = infra_candidates[0]
        second_score = 0
        if len(infra_candidates) > 1:
            second_score = infra_candidates[1]['score']

        return {
            'provider': top['provider'],
            'confidence': self._calculate_confidence(top['score'], top['score'] - second_score),
            'signals': self.__infra_signals.get(top['provider'], [])[:8],
            'candidates': infra_candidates[:5],
        }

    @staticmethod
    def _calculate_confidence(top_score, gap):
        """
        Convert score and score gap into a readable confidence.

        :param float top_score:
        :param float gap:
        :return: int
        """

        confidence = 25 + int(float(top_score) * 4) + int(max(float(gap), 0) * 2)
        return max(35, min(98, confidence))