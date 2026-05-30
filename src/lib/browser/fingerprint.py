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

    Development: Stanislav WEB
"""

import copy
import re
import uuid
from collections import defaultdict
from urllib.parse import urljoin, urlparse

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
        'runtime': {'name': 'unknown', 'category': 'runtime', 'confidence': 0, 'signals': [], 'candidates': []},
        'infrastructure': {
            'provider': 'unknown',
            'confidence': 0,
            'signals': [],
            'candidates': [],
        },
        'security_headers': {
            'hsts': {
                'present': False,
                'header': '',
                'max_age': None,
                'include_subdomains': False,
                'preload': False,
                'preload_ready': False,
                'http_to_https_redirect': False,
                'grade': 'missing',
                'warnings': ['missing_hsts'],
            }
        },
        'privacy_risks': {
            'supercookie': {
                'risk': 'none',
                'score': 0,
                'signals': [],
                'warnings': [],
                'hsts_tracking_surface': False,
                'etag_tracking_surface': False,
                'cache_tracking_surface': False,
                'persistent_cookie_surface': False,
            }
        }
    }

    @classmethod
    def _default_result(cls):
        """
        Return an isolated default fingerprint result.

        DEFAULT_RESULT contains nested lists/dicts, so shallow copies can leak
        runtime mutations between failed or empty fingerprint attempts.

        :return: dict
        """

        return copy.deepcopy(cls.DEFAULT_RESULT)

    PROBES = (
        '/wp-json/',
        '/wp-content/',
        '/wp-content/plugins/',
        '/wp-content/themes/',
        '/wp-includes/',
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
        '/index.php/index/login',
        '/index.php/index/search',
        '/index.php/index/about',
        '/manager/',
        '/bolt',
    )

    NOT_FOUND_PROBE_PATH = '/.well-known/{0}.txt'.format(uuid.uuid4().hex[:12])

    CMS_CATEGORY = 'cms'
    FRAMEWORK_CATEGORY = 'framework'
    CUSTOM_CATEGORY = 'custom'
    ECOMMERCE_CATEGORY = 'ecommerce'
    SITE_BUILDER_CATEGORY = 'sitebuilder'
    STATIC_CATEGORY = 'static'
    RUNTIME_CATEGORY = 'runtime'
    TECHNOLOGY_RUNTIME_MAP = {
        'WordPress': 'PHP', 'WooCommerce': 'PHP', 'Drupal': 'PHP', 'Joomla': 'PHP', 'Magento': 'PHP', 'Bitrix': 'PHP', 'OpenCart': 'PHP', 'PrestaShop': 'PHP', 'TYPO3': 'PHP', 'Nextcloud': 'PHP', 'ownCloud': 'PHP', 'Matomo': 'PHP', 'phpMyAdmin': 'PHP', 'phpBB': 'PHP', 'Moodle': 'PHP', 'Open Journal Systems': 'PHP', 'Evolution CMS': 'PHP', 'MogutaCMS': 'PHP', 'InstantCMS': 'PHP', 'DiafanCMS': 'PHP', 'Laravel': 'PHP', 'Symfony': 'PHP', 'Craft CMS': 'PHP', 'Bolt CMS': 'PHP', 'RoundCube Webmail': 'PHP', 'WHMCS': 'PHP', 'CS-Cart': 'PHP', 'CubeCart': 'PHP', 'DataLife Engine': 'PHP', 'Discuz!': 'PHP', 'SilverStripe': 'PHP', 'Webasyst / Shop-Script': 'PHP', 'XOOPS': 'PHP', 'Zen Cart CMS': 'PHP', 'e107': 'PHP', 'phpWind': 'PHP', 'phpCMS': 'PHP',
        'Express': 'Node.js', 'NestJS': 'Node.js', 'Fastify': 'Node.js', 'Koa': 'Node.js', 'Hapi': 'Node.js', 'Strapi': 'Node.js', 'Directus': 'Node.js', 'Ghost': 'Node.js', 'Next.js': 'Node.js', 'Nuxt': 'Node.js', 'Gatsby': 'Node.js', 'Astro': 'Node.js', 'Remix': 'Node.js', 'SvelteKit': 'Node.js', 'Docusaurus': 'Node.js', 'VitePress': 'Node.js', 'PencilBlue': 'Node.js',
        'React': 'JavaScript', 'Vue': 'JavaScript', 'Angular': 'JavaScript', 'Django': 'Python', 'Flask': 'Python', 'FastAPI': 'Python', 'Ruby on Rails': 'Ruby', 'Spree': 'Ruby', 'Spring': 'Java/JVM', 'Liferay': 'Java/JVM', 'OpenCms': 'Java/JVM', 'Hippo CMS': 'Java/JVM', 'dotCMS': 'Java/JVM', 'ASP.NET': '.NET', 'Microsoft SharePoint': '.NET', 'DNN Platform': '.NET', 'Orchard CMS': '.NET', 'Sitecore': '.NET', 'Sitefinity': '.NET', 'Umbraco': '.NET', 'Phoenix': 'Elixir', 'MkDocs': 'Static site', 'Jekyll': 'Static site', 'Hugo': 'Static site', 'AsciiDoc': 'Static site',
    }

    EXTENDED_CMS_GENERATOR_SIGNATURES = (
        ('3dCart', ECOMMERCE_CATEGORY, ('3dcart', '3d cart', 'shift4shop')),
        ('Adobe Business Catalyst', CMS_CATEGORY, ('adobe business catalyst', 'business catalyst')),
        ('AEM', CMS_CATEGORY, ('adobe experience manager',)),
        ('Ametys CMS', CMS_CATEGORY, ('ametys', 'ametys cms')),
        ('Amiro.CMS', CMS_CATEGORY, ('amiro.cms', 'amiro cms')),
        ('Apostrophe CMS', CMS_CATEGORY, ('apostrophecms', 'apostrophe cms')),
        ('AsciiDoc', STATIC_CATEGORY, ('asciidoc',)),
        ('BigCommerce', ECOMMERCE_CATEGORY, ('bigcommerce',)),
        ('BigTree CMS', CMS_CATEGORY, ('bigtree cms', 'bigtreecms')),
        ('Blogger', SITE_BUILDER_CATEGORY, ('blogger', 'blogger by google')),
        ('BrowserCMS', CMS_CATEGORY, ('browsercms', 'browser cms')),
        ('Bubble', SITE_BUILDER_CATEGORY, ('bubble', 'bubble.io')),
        ('CKAN', CMS_CATEGORY, ('ckan',)),
        ('CMS.S3 / Megagroup', CMS_CATEGORY, ('cms.s3', 'cms s3', 'megagroup cms')),
        ('CMS Made Simple', CMS_CATEGORY, ('cms made simple', 'cmsms')),
        ('CMS CONTENIDO', CMS_CATEGORY, ('contenido', 'cms contenido')),
        ('CMSimple', CMS_CATEGORY, ('cmsimple',)),
        ('CS-Cart', ECOMMERCE_CATEGORY, ('cs-cart', 'cs cart', 'cscart')),
        ('CubeCart', ECOMMERCE_CATEGORY, ('cubecart',)),
        ('DataLife Engine', CMS_CATEGORY, ('datalife engine', 'dle')),
        ('DiafanCMS', CMS_CATEGORY, ('diafan.cms', 'diafan cms')),
        ('Discuz!', CMS_CATEGORY, ('discuz!', 'discuz')),
        ('Duda', SITE_BUILDER_CATEGORY, ('duda', 'duda website builder')),
        ('DNN Platform', CMS_CATEGORY, ('dnn platform', 'dotnetnuke', 'dnn')),
        ('dotCMS', CMS_CATEGORY, ('dotcms', 'dot cms')),
        ('Dynamicweb', ECOMMERCE_CATEGORY, ('dynamicweb',)),
        ('EC-CUBE', ECOMMERCE_CATEGORY, ('ec-cube', 'eccube')),
        ('EPiServer', CMS_CATEGORY, ('episerver', 'optimizely cms')),
        ('ExpressionEngine', CMS_CATEGORY, ('expressionengine', 'expression engine')),
        ('Evolution CMS', CMS_CATEGORY, ('evolution cms', 'evolutioncms', 'modx evolution')),
        ('Fork CMS', CMS_CATEGORY, ('fork cms',)),
        ('GetSimple CMS', CMS_CATEGORY, ('getsimple cms', 'get-simple cms')),
        ('GoDaddy Website Builder', SITE_BUILDER_CATEGORY, ('godaddy website builder', 'go central')),
        ('Hippo CMS', CMS_CATEGORY, ('hippo cms', 'onehippo', 'bloomreach experience')),
        ('Hostinger Website Builder', SITE_BUILDER_CATEGORY, ('hostinger website builder', 'zyro website builder')),
        ('InstantCMS', CMS_CATEGORY, ('instantcms', 'instant cms')),
        ('ImpressPages CMS', CMS_CATEGORY, ('impresspages', 'impresspages cms')),
        ('Jimdo', SITE_BUILDER_CATEGORY, ('jimdo',)),
        ('Mobirise', SITE_BUILDER_CATEGORY, ('mobirise', 'mobirise website builder')),
        ('Kooboo CMS', CMS_CATEGORY, ('kooboo', 'kooboo cms')),
        ('Liferay', CMS_CATEGORY, ('liferay', 'liferay portal')),
        ('Microsoft SharePoint', CMS_CATEGORY, ('microsoft sharepoint', 'sharepoint')),
        ('Mura CMS', CMS_CATEGORY, ('mura cms', 'mura')),
        ('NetCat', CMS_CATEGORY, ('netcat cms', 'netcat')),
        ('Odoo', ECOMMERCE_CATEGORY, ('odoo',)),
        ('OpenCms', CMS_CATEGORY, ('opencms', 'open cms')),
        ('Orchard CMS', CMS_CATEGORY, ('orchard cms', 'orchard core')),
        ('Percussion CMS', CMS_CATEGORY, ('percussion cms', 'percussion')),
        ('phpCMS', CMS_CATEGORY, ('phpcms',)),
        ('PencilBlue', CMS_CATEGORY, ('pencilblue',)),
        ('Quick.Cms', CMS_CATEGORY, ('quick.cms', 'quick cms')),
        ('RoundCube Webmail', CMS_CATEGORY, ('roundcube webmail', 'roundcube')),
        ('Salesforce Commerce Cloud', ECOMMERCE_CATEGORY, ('salesforce commerce cloud', 'demandware')),
        ('Serendipity', CMS_CATEGORY, ('serendipity', 's9y')),
        ('ShopFA', ECOMMERCE_CATEGORY, ('shopfa',)),
        ('Shoper', ECOMMERCE_CATEGORY, ('shoper',)),
        ('Shopery', ECOMMERCE_CATEGORY, ('shopery',)),
        ('Shoptet', ECOMMERCE_CATEGORY, ('shoptet',)),
        ('SilverStripe', CMS_CATEGORY, ('silverstripe', 'silverstripe cms')),
        ('Sitecore', CMS_CATEGORY, ('sitecore',)),
        ('Sitefinity', CMS_CATEGORY, ('sitefinity', 'progress sitefinity')),
        ('Smartstore', ECOMMERCE_CATEGORY, ('smartstore',)),
        ('Spree', ECOMMERCE_CATEGORY, ('spree commerce', 'spree')),
        ('Subrion CMS', CMS_CATEGORY, ('subrion', 'subrion cms')),
        ('Sulu', CMS_CATEGORY, ('sulu cms', 'sulu')),
        ('Textpattern CMS', CMS_CATEGORY, ('textpattern', 'textpattern cms')),
        ('TiddlyWiki', CMS_CATEGORY, ('tiddlywiki',)),
        ('Tiki Wiki CMS Groupware', CMS_CATEGORY, ('tiki wiki cms groupware', 'tiki wiki', 'tikiwiki')),
        ('UMI.CMS', CMS_CATEGORY, ('umi.cms', 'umi cms')),
        ('WebsiteBaker CMS', CMS_CATEGORY, ('websitebaker', 'websitebaker cms')),
        ('Webasyst / Shop-Script', ECOMMERCE_CATEGORY, ('webasyst', 'shop-script', 'shop script')),
        ('WebGUI', CMS_CATEGORY, ('webgui',)),
        ('Weebly', SITE_BUILDER_CATEGORY, ('weebly',)),
        ('WHMCS', ECOMMERCE_CATEGORY, ('whmcs',)),
        ('Wolf CMS', CMS_CATEGORY, ('wolf cms',)),
        ('XpressEngine', CMS_CATEGORY, ('xpressengine', 'xe cms')),
        ('XOOPS', CMS_CATEGORY, ('xoops',)),
        ('Zen Cart CMS', ECOMMERCE_CATEGORY, ('zen cart', 'zencart')),
        ('e107', CMS_CATEGORY, ('e107',)),
        ('ePages', ECOMMERCE_CATEGORY, ('epages',)),
        ('eZ Publish', CMS_CATEGORY, ('ez publish', 'ezpublish')),
        ('phpWind', CMS_CATEGORY, ('phpwind',)),
        ('sNews', CMS_CATEGORY, ('snews cms', 'snews')),
    )

    EXTENDED_CMS_BODY_SIGNATURES = (
        ('3dCart', ECOMMERCE_CATEGORY, ('/3dcart/', '3dcartstores.com', 'powered by 3dcart')),
        ('AEM', CMS_CATEGORY, ('/etc.clientlibs/', '/content/dam/', 'cq-wcm-edit', 'granite.author')),
        ('Apostrophe CMS', CMS_CATEGORY, ('apos-before', 'apos-area', 'data-apos-')),
        ('BigCommerce', ECOMMERCE_CATEGORY, ('cdn11.bigcommerce.com', 'stencilutils', 'bigcommerce.com/stencil')),
        ('Blogger', SITE_BUILDER_CATEGORY, ('blogger.com/static/', 'blogger-template-style', 'blogger-js')),
        ('Bubble', SITE_BUILDER_CATEGORY, ('bubble.is/static/', 'bubble.io/static/', 'bubble-element')),
        ('CKAN', CMS_CATEGORY, ('ckanext', 'data-module="ckan-module"', "data-module='ckan-module'")),
        ('CMS.S3 / Megagroup', CMS_CATEGORY, ('cms.s3', 'megagroup.ru', 'мегагрупп', 'логотип мегагрупп')),
        ('CMS Made Simple', CMS_CATEGORY, ('cmsms_stylesheet', 'powered by cms made simple', '/modules/cms')),
        ('CS-Cart', ECOMMERCE_CATEGORY, ('var tygh', 'index.php?dispatch=', '/design/themes/')),
        ('CubeCart', ECOMMERCE_CATEGORY, ('cubecart', 'index.php?_a=', '/skins/')),
        ('DataLife Engine', CMS_CATEGORY, ('datalife engine', 'engine/ajax/', 'index.php?do=')),
        ('DiafanCMS', CMS_CATEGORY, ('diafan.cms',)),
        ('Discuz!', CMS_CATEGORY, ('discuz_uid', 'discuz_tips', 'static/image/common/', 'powered by discuz')),
        ('Duda', SITE_BUILDER_CATEGORY, ('static-cdn.multiscreensite.com', 'data-cmsid=', 'dmcdn.net')),
        ('DNN Platform', CMS_CATEGORY, ('__dnnvariable', 'dnn_', '/portals/_default/')),
        ('EC-CUBE', ECOMMERCE_CATEGORY, ('eccube', 'ec-cube', '/user_data/packages/')),
        ('ExpressionEngine', CMS_CATEGORY, ('expressionengine', 'exp:channel', 'powered by expressionengine')),
        (
            'Evolution CMS',
            CMS_CATEGORY,
            (
                'powered by evolution cms',
                'evolution cms is not currently installed',
                'please run the evolution cms install utility',
                'modx evolution',
            ),
        ),
        ('GetSimple CMS', CMS_CATEGORY, ('getsimple', 'get-simple', '/data/uploads/')),
        ('GoDaddy Website Builder', SITE_BUILDER_CATEGORY, ('wsimg.com', 'godaddy.com/websites/website-builder')),
        ('Hostinger Website Builder', SITE_BUILDER_CATEGORY, ('hostinger website builder', 'userapp.zyrosite.com', 'assets.zyrosite.com', 'zyrosite.com')),
        ('InstantCMS', CMS_CATEGORY, ('instantcms', 'icms-', '/templates/default/')),
        ('ImpressPages CMS', CMS_CATEGORY, ('impresspages', 'ip_themes/', 'ip_content')),
        ('Jimdo', SITE_BUILDER_CATEGORY, ('jimcdn.com', 'jimdo_layout_css', 'jimdo.com')),
        (
            'Mobirise',
            SITE_BUILDER_CATEGORY,
            (
                '/assets/mobirise/',
                '/assets/web/assets/mobirise-icons',
                'mobirise-icons.css',
                'mbr-additional.css',
                'mbr-section-title',
                'mbr-section-btn',
                'mbr-fonts-style',
            ),
        ),
        ('Liferay', CMS_CATEGORY, ('liferay', '/o/frontend-js-', 'portlet-boundary')),
        (
            'Microsoft SharePoint',
            CMS_CATEGORY,
            ('/_layouts/', '/_catalogs/', 'spclienttemplates', 'ms-webpartzone-cell'),
        ),
        ('NetCat', CMS_CATEGORY, ('/netcat/', 'netcat_template', 'netcat_files', 'nc-module')),
        ('Odoo', ECOMMERCE_CATEGORY, ('odoo.define', '/web/assets/', 'website.assets_frontend')),
        ('OpenCms', CMS_CATEGORY, ('opencms', '/opencms/', 'alkacon opencms')),
        ('Orchard CMS', CMS_CATEGORY, ('orchard', 'powered by orchard', '/modules/orchard.')),
        ('RoundCube Webmail', CMS_CATEGORY, ('roundcube', 'rcmail', '/program/js/app.js')),
        ('Salesforce Commerce Cloud', ECOMMERCE_CATEGORY, ('demandware.static', 'dwac-', 'salesforce commerce cloud')),
        ('Shoptet', ECOMMERCE_CATEGORY, ('shoptet', 'cdn.myshoptet.com', 'data-testid="shoptet"')),
        ('SilverStripe', CMS_CATEGORY, ('silverstripe', 'framework/javascript/', 'security/loginform')),
        ('Sitecore', CMS_CATEGORY, ('/sitecore/', 'sc_site=', 'sitecore.context')),
        ('Sitefinity', CMS_CATEGORY, ('telerik.sitefinity', 'sf-content-block', '/sitefinity/')),
        ('Spree', ECOMMERCE_CATEGORY, ('spreecommerce', 'spree commerce', '/assets/spree/')),
        ('TiddlyWiki', CMS_CATEGORY, ('tiddlywiki', 'tiddlywiki.com/static/')),
        ('Tiki Wiki CMS Groupware', CMS_CATEGORY, ('tiki-index.php', 'tikiwiki', 'tiki wiki cms groupware')),
        ('Webasyst / Shop-Script', ECOMMERCE_CATEGORY, ('wa-apps/', 'wa-content/', 'shop-script', 'webasyst')),
        ('WebGUI', CMS_CATEGORY, ('webgui', 'assetproxy', 'extras/webgui')),
        ('Weebly', SITE_BUILDER_CATEGORY, ('weebly.com/uploads/', 'weeblysite.com', 'cdn2.editmysite.com')),
        ('WHMCS', ECOMMERCE_CATEGORY, ('whmcs', 'whmcomplete solution', 'templates/six/')),
        ('XOOPS', CMS_CATEGORY, ('xoops', '/modules/system/', 'xoops_url')),
        ('Zen Cart CMS', ECOMMERCE_CATEGORY, ('zen cart', 'zencart', 'main_page=')),
        ('e107', CMS_CATEGORY, ('e107', 'e107_files/', 'e107_handlers')),
        ('ePages', ECOMMERCE_CATEGORY, ('epages', 'epages 6', 'epages.com')),
    )

    EXTENDED_CMS_HEADER_SIGNATURES = (
        ('Microsoft SharePoint', CMS_CATEGORY, 'microsoftsharepointteamservices', None),
        ('Microsoft SharePoint', CMS_CATEGORY, 'x-sharepointhealthscore', None),
        ('Sitecore', CMS_CATEGORY, 'x-sitecore', None),
        ('Sitecore', CMS_CATEGORY, 'x-generator', 'sitecore'),
        ('Liferay', CMS_CATEGORY, 'liferay-portal', None),
        ('DNN Platform', CMS_CATEGORY, 'x-compressed-by', 'dnn'),
        ('Odoo', ECOMMERCE_CATEGORY, 'x-odoo', None),
        ('Salesforce Commerce Cloud', ECOMMERCE_CATEGORY, 'x-dw-request-base-id', None),
        ('Salesforce Commerce Cloud', ECOMMERCE_CATEGORY, 'x-dw-trace-id', None),
        ('AEM', CMS_CATEGORY, 'x-dispatcher', None),
        ('UMI.CMS', CMS_CATEGORY, 'x-generated-by', 'umi.cms'),
        ('UMI.CMS', CMS_CATEGORY, 'x-generated-by', 'umi cms'),
    )

    EXTENDED_CMS_COOKIE_SIGNATURES = (
        ('RoundCube Webmail', CMS_CATEGORY, ('roundcube_sessid', 'roundcube_sessauth')),
        ('Microsoft SharePoint', CMS_CATEGORY, ('fedauth', 'rtfa')),
        ('Sitecore', CMS_CATEGORY, ('sitecore_device', 'sitecore_session')),
        ('Liferay', CMS_CATEGORY, ('guest_language_id',)),
        ('DNN Platform', CMS_CATEGORY, ('.dotnetnuke', 'dnnoutputcache')),
        ('CS-Cart', ECOMMERCE_CATEGORY, ('sid_customer_',)),
        ('Discuz!', CMS_CATEGORY, ('discuz_',)),
        ('Webasyst / Shop-Script', ECOMMERCE_CATEGORY, ('shop-script', 'webasyst', 'waid')),
        ('WHMCS', ECOMMERCE_CATEGORY, ('whmcs', 'whmcs_user')),
    )

    def __init__(self, config, client, progress_callback=None):
        """
        Init fingerprint detector.

        :param config: browser config
        :param client: prepared HTTP client
        :param callable|None progress_callback: optional progress reporter
        """

        self.__config = config
        self.__client = client
        self.__progress_callback = progress_callback
        self.__scores = defaultdict(float)
        self.__signals = defaultdict(list)
        self.__categories = {}
        self.__runtime_scores = defaultdict(float)
        self.__runtime_signals = defaultdict(list)
        self.__infra_scores = defaultdict(float)
        self.__infra_signals = defaultdict(list)
        self.__dotcms_probe_signals = []
        self.__request_cache = {}

    def detect(self):
        """
        Detect probable target technology.

        :return: dict
        """

        self.__scores = defaultdict(float)
        self.__signals = defaultdict(list)
        self.__categories = {}
        self.__runtime_scores = defaultdict(float)
        self.__runtime_signals = defaultdict(list)
        self.__infra_scores = defaultdict(float)
        self.__infra_signals = defaultdict(list)
        self.__dotcms_probe_signals = []
        self.__request_cache = {}

        progress_total = len(self.PROBES) + 4
        progress_current = 0
        self._emit_progress(progress_current, progress_total, 'start')

        base_url = self._build_base_url()
        root_response = self._request(base_url, method='GET')
        progress_current += 1
        self._emit_progress(progress_current, progress_total, 'root')
        if root_response is None:
            self._emit_progress(progress_total, progress_total, 'done')
            return self._default_result()

        root_response, final_root_url = self._follow_redirects(root_response, base_url, method='GET')
        body = self._extract_body(root_response)
        body_lower = body.lower()
        headers = self._extract_headers(root_response)
        security_headers = self._build_security_headers(headers, base_url, final_root_url)
        privacy_risks = self._build_privacy_risks(
            headers=headers,
            body=body,
            body_size=len(body.encode('utf-8')),
            final_root_url=final_root_url,
            security_headers=security_headers,
        )
        cookies = self._extract_cookies(root_response)
        generator = self._extract_generator(body)
        progress_current += 1
        self._emit_progress(progress_current, progress_total, 'metadata')

        probe_statuses = self._probe_endpoints(
            final_root_url,
            progress_offset=progress_current,
            progress_total=progress_total,
        )
        progress_current += len(self.PROBES)
        self.__dotcms_probe_signals = self._probe_dotcms_endpoint_signals(final_root_url)

        not_found_status, not_found_body, not_found_headers = self._probe_not_found_signature(final_root_url)
        progress_current += 1
        self._emit_progress(progress_current, progress_total, '404 baseline')

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

        progress_current += 1
        self._emit_progress(progress_current, progress_total, 'analyze')

        app_candidates = self._build_candidates()
        runtime_candidates = self._build_runtime_candidates()
        infra_candidates = self._build_infrastructure_candidates()

        if len(app_candidates) <= 0:
            result = self._default_result()
            result['runtime'] = self._build_runtime_result(runtime_candidates)
            result['infrastructure'] = self._build_infrastructure_result(infra_candidates)
            result['security_headers'] = security_headers
            result['privacy_risks'] = privacy_risks
            self._emit_progress(progress_total, progress_total, 'done')
            return result

        top_candidate = app_candidates[0]
        second_score = 0
        if len(app_candidates) > 1:
            second_score = app_candidates[1]['score']

        top_score = top_candidate['score']
        if top_score < 7:
            result = {
                'category': self.CUSTOM_CATEGORY,
                'name': 'Unknown custom stack',
                'confidence': 45,
                'score': round(top_score, 2),
                'signals': [],
                'candidates': app_candidates[:5],
                'runtime': self._build_runtime_result(runtime_candidates),
                'infrastructure': self._build_infrastructure_result(infra_candidates),
                'security_headers': security_headers,
                'privacy_risks': privacy_risks,
            }
            self._emit_progress(progress_total, progress_total, 'done')
            return result

        confidence = self._calculate_confidence(top_score, top_score - second_score)
        result = {
            'category': top_candidate['category'],
            'name': top_candidate['name'],
            'confidence': confidence,
            'score': top_candidate['score'],
            'signals': self.__signals.get(top_candidate['name'], [])[:10],
            'candidates': app_candidates[:5],
            'runtime': self._build_runtime_result(runtime_candidates),
            'infrastructure': self._build_infrastructure_result(infra_candidates),
            'security_headers': security_headers,
            'privacy_risks': privacy_risks,
        }
        self._emit_progress(progress_total, progress_total, 'done')
        return result

    def _emit_progress(self, current, total, label):
        """
        Emit a safe progress event when a callback is configured.

        :param int current: current progress position
        :param int total: total progress positions
        :param str label: human-readable current step
        :return: None
        """

        if self.__progress_callback is None:
            return

        try:
            self.__progress_callback(current, total, label)
        except (AttributeError, TypeError, ValueError):
            pass

    def _build_base_url(self):
        """
        Build target base URL.

        :return: str
        """

        scheme = self.__config.scheme or self.__config.DEFAULT_SCHEME
        host = self.__config.host
        port = self.__config.port

        prefix = str(getattr(self.__config, 'prefix', '') or '').strip('/')
        suffix = '{0}/'.format(prefix) if prefix else ''

        if (scheme == 'http://' and port == self.__config.DEFAULT_HTTP_PORT) \
                or (scheme == 'https://' and port == self.__config.DEFAULT_SSL_PORT):
            return '{0}{1}/{2}'.format(scheme, host, suffix)
        return '{0}{1}:{2}/{3}'.format(scheme, host, port, suffix)

    def _request(self, url, method='HEAD'):
        """
        Execute an HTTP request with a temporary method override.

        Exact duplicate fingerprint probes can happen when a generic probe is
        reused by a narrower technology-specific check. Cache successful
        responses for the current fingerprint pass only to avoid repeated
        traffic without changing detection semantics.

        :param str url: target URL
        :param str method: request method
        :return: mixed
        """

        normalized_method = str(method or 'HEAD').upper()
        cache_key = (normalized_method, str(url))
        if cache_key in self.__request_cache:
            return self.__request_cache[cache_key]

        previous_method = getattr(self.__config, '_method', None)

        try:
            setattr(self.__config, '_method', normalized_method)
            response = self.__client.request(url)
        finally:
            setattr(self.__config, '_method', previous_method)

        if response is not None:
            self.__request_cache[cache_key] = response

        return response

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

    @classmethod
    def _build_security_headers(cls, headers, base_url, final_root_url):
        """
        Build offline security-header posture from the observed target response.

        :param dict headers: normalized response headers from the final root response
        :param str base_url: configured root URL before redirects
        :param str final_root_url: final root URL after redirects
        :return: security header metadata
        :rtype: dict
        """

        return {
            'hsts': cls._build_hsts_result(
                headers=headers,
                base_url=base_url,
                final_root_url=final_root_url,
            )
        }

    @classmethod
    def _build_hsts_result(cls, headers, base_url, final_root_url):
        """
        Parse and grade the Strict-Transport-Security header from the final HTTPS response.

        :param dict headers: normalized response headers
        :param str base_url: configured root URL before redirects
        :param str final_root_url: final root URL after redirects
        :return: HSTS posture
        :rtype: dict
        """

        header = str(headers.get('strict-transport-security', '') or '').strip()
        directives = cls._parse_hsts_directives(header)
        max_age = cls._parse_hsts_max_age(directives.get('max-age'))
        include_subdomains = 'includesubdomains' in directives
        preload = 'preload' in directives
        final_is_https = str(final_root_url).lower().startswith('https://')
        http_to_https_redirect = str(base_url).lower().startswith('http://') and final_is_https
        warnings = []

        if not final_is_https:
            warnings.append('not_https')

        if not header or not final_is_https:
            warnings.append('missing_hsts')
            grade = 'missing'
        elif max_age is None:
            warnings.append('missing_max_age')
            grade = 'invalid'
        elif max_age <= 0:
            warnings.append('disabled')
            grade = 'disabled'
        elif max_age < 15552000:
            warnings.append('max_age_too_low')
            grade = 'weak'
        elif max_age < 31536000:
            warnings.append('max_age_below_preload_minimum')
            grade = 'moderate'
        elif not include_subdomains:
            warnings.append('missing_include_subdomains')
            grade = 'good'
        else:
            grade = 'strong'

        preload_ready = bool(
            final_is_https
            and header
            and max_age is not None
            and max_age >= 31536000
            and include_subdomains
            and preload
        )

        if preload and not preload_ready:
            warnings.append('preload_not_ready')

        if preload_ready:
            grade = 'preload-ready'

        return {
            'present': bool(header and final_is_https),
            'header': header,
            'max_age': max_age,
            'include_subdomains': include_subdomains,
            'preload': preload,
            'preload_ready': preload_ready,
            'http_to_https_redirect': http_to_https_redirect,
            'grade': grade,
            'warnings': warnings,
        }

    @staticmethod
    def _parse_hsts_directives(header):
        """
        Parse HSTS directives into a case-insensitive dictionary.

        :param str header: Strict-Transport-Security header value
        :return: directive map
        :rtype: dict
        """

        directives = {}
        for part in str(header or '').split(';'):
            part = part.strip()
            if not part:
                continue
            if '=' in part:
                key, value = part.split('=', 1)
                directives[key.strip().lower()] = value.strip().strip('"')
            else:
                directives[part.lower()] = True
        return directives

    @staticmethod
    def _parse_hsts_max_age(value):
        """
        Parse max-age directive as a non-negative integer.

        :param str|None value: max-age directive value
        :return: parsed max-age or None
        :rtype: int|None
        """

        if value is None:
            return None
        try:
            max_age = int(str(value).strip())
        except (TypeError, ValueError):
            return None
        if max_age < 0:
            return None
        return max_age

    @classmethod
    def _build_privacy_risks(cls, headers, body, body_size, final_root_url, security_headers):
        """
        Build passive privacy-risk metadata from the root fingerprint response.

        This detector reports server-side tracking surfaces only. It does not
        claim that a browser identifier was actually stored or recovered.

        :param dict headers: normalized response headers from the final root response
        :param str body: decoded root response body
        :param int body_size: decoded body size in bytes
        :param str final_root_url: final root URL after redirects
        :param dict security_headers: security-header metadata
        :return: privacy risk metadata
        :rtype: dict
        """

        supercookie = cls._build_supercookie_risk(
            headers=headers,
            body=body,
            body_size=body_size,
            final_root_url=final_root_url,
            security_headers=security_headers,
        )

        return {'supercookie': supercookie}

    @classmethod
    def _build_supercookie_risk(cls, headers, body, body_size, final_root_url, security_headers):
        """
        Build passive supercookie/tracking-surface risk metadata.

        :param dict headers: normalized response headers
        :param str body: decoded response body
        :param int body_size: response body size in bytes
        :param str final_root_url: final root URL
        :param dict security_headers: security-header metadata
        :return: supercookie risk metadata
        :rtype: dict
        """

        signals = []
        warnings = []
        score = 0
        hsts_surface = False
        etag_surface = False
        cache_surface = False
        cookie_surface = False

        hsts = security_headers.get('hsts') if isinstance(security_headers, dict) else {}
        if not isinstance(hsts, dict):
            hsts = {}

        hsts_max_age = hsts.get('max_age')
        subdomains = cls._extract_first_party_subdomains(body, final_root_url)
        long_hsts = bool(
            hsts.get('present')
            and hsts_max_age is not None
            and int(hsts_max_age) >= 15552000
        )

        if long_hsts:
            signals.append('long_lived_hsts:max_age={0}'.format(hsts_max_age))

        if len(subdomains) >= 3:
            signals.append('first_party_subdomain_fanout:{0}'.format(len(subdomains)))

        if long_hsts and len(subdomains) >= 3:
            hsts_surface = True
            score += 40
            warnings.append('long-lived HSTS combined with first-party subdomain fan-out')

        cache_control = str(headers.get('cache-control', '') or '').lower()
        etag = str(headers.get('etag', '') or '').strip()
        body_is_small = int(body_size or 0) <= 4096
        long_cache = cls._has_long_cache_lifetime(cache_control)

        if long_cache:
            cache_surface = True
            score += 10
            signals.append('long_lived_cache:{0}'.format(cache_control))

        if etag and long_cache and body_is_small:
            etag_surface = True
            score += 35
            signals.append('persistent_etag:{0}'.format(etag))
            warnings.append('persistent ETag/cache validator with long cache lifetime')

        cookie_warnings = cls._detect_persistent_cookie_surface(headers)
        if len(cookie_warnings) > 0:
            cookie_surface = True
            score += 20
            signals.extend(cookie_warnings)
            warnings.append('long-lived client cookie surface')

        risk = cls._privacy_score_to_risk(score)
        if risk in ('none', 'low'):
            warnings = []

        return {
            'risk': risk,
            'score': min(score, 100),
            'signals': signals,
            'warnings': warnings,
            'hsts_tracking_surface': hsts_surface,
            'etag_tracking_surface': etag_surface,
            'cache_tracking_surface': cache_surface,
            'persistent_cookie_surface': cookie_surface,
        }

    @staticmethod
    def _privacy_score_to_risk(score):
        """
        Convert a numeric privacy score into a stable risk bucket.

        :param int score: numeric risk score
        :return: risk bucket
        :rtype: str
        """

        score = int(score or 0)
        if score >= 60:
            return 'high'
        if score >= 35:
            return 'medium'
        if score > 0:
            return 'low'
        return 'none'

    @classmethod
    def _has_long_cache_lifetime(cls, cache_control):
        """
        Return True when Cache-Control allows persistent browser storage.

        :param str cache_control: raw Cache-Control header value
        :return: check result
        :rtype: bool
        """

        cache_control = str(cache_control or '').lower()
        if 'no-store' in cache_control:
            return False
        if 'immutable' in cache_control:
            return True

        match = re.search(r'(?:^|,|\s)max-age\s*=\s*(\d+)', cache_control)
        if match is None:
            return False

        try:
            return int(match.group(1)) >= 2592000
        except (TypeError, ValueError):
            return False

    @classmethod
    def _detect_persistent_cookie_surface(cls, headers):
        """
        Return persistent client-cookie signals from Set-Cookie headers.

        :param dict headers: normalized response headers
        :return: detected cookie signals
        :rtype: list[str]
        """

        raw_cookie = str(headers.get('set-cookie', '') or '')
        if not raw_cookie:
            return []

        cookie_parts = [item.strip() for item in raw_cookie.split(',') if item.strip()]
        signals = []

        for cookie in cookie_parts:
            cookie_lower = cookie.lower()
            max_age = cls._extract_cookie_max_age(cookie_lower)
            if max_age is None or max_age < 2592000:
                continue

            missing_attrs = []
            if 'httponly' not in cookie_lower:
                missing_attrs.append('httponly')
            if 'samesite=' not in cookie_lower:
                missing_attrs.append('samesite')
            if 'secure' not in cookie_lower:
                missing_attrs.append('secure')

            if len(missing_attrs) > 0:
                cookie_name = cookie.split('=', 1)[0].strip()
                signals.append(
                    'persistent_cookie:{0}:max_age={1}:missing={2}'.format(
                        cookie_name,
                        max_age,
                        '|'.join(missing_attrs),
                    )
                )

        return signals

    @staticmethod
    def _extract_cookie_max_age(cookie):
        """
        Extract cookie Max-Age as integer seconds.

        :param str cookie: raw Set-Cookie header value
        :return: max-age seconds or None
        :rtype: int|None
        """

        match = re.search(r'(?:^|;)\s*max-age\s*=\s*(\d+)', str(cookie or ''), re.IGNORECASE)
        if match is None:
            return None
        try:
            return int(match.group(1))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _extract_first_party_subdomains(cls, body, final_root_url):
        """
        Extract first-party subdomains referenced by absolute URLs in the body.

        The detector intentionally avoids matching special names such as bit00,
        id00 or track00. Only structural first-party subdomain fan-out matters.

        :param str body: decoded response body
        :param str final_root_url: final root URL
        :return: sorted first-party subdomains
        :rtype: list[str]
        """

        root_host = cls._normalize_host(urlparse(str(final_root_url or '')).hostname)
        site_domain = cls._site_domain(root_host)
        if not root_host or not site_domain:
            return []

        hosts = set()
        for match in re.finditer(r'https?://([^/\s"\'<>]+)', str(body or ''), re.IGNORECASE):
            host = cls._normalize_host(match.group(1).split(':', 1)[0])
            if not host or host == root_host:
                continue
            if host.endswith('.{0}'.format(site_domain)):
                hosts.add(host)

        return sorted(hosts)

    @staticmethod
    def _normalize_host(host):
        """
        Normalize host values for first-party comparisons.

        :param str|None host: host value
        :return: normalized host
        :rtype: str
        """

        return str(host or '').strip().strip('.').lower()

    @staticmethod
    def _site_domain(host):
        """
        Return a lightweight site-domain suffix without external dependencies.

        :param str host: normalized host
        :return: site-domain suffix
        :rtype: str
        """

        labels = [label for label in str(host or '').split('.') if label]
        if len(labels) < 2:
            return ''

        two_level_public_suffixes = {
            'co.uk', 'org.uk', 'ac.uk', 'gov.uk',
            'com.ua', 'net.ua', 'org.ua', 'gov.ua',
            'com.au', 'net.au', 'org.au',
            'co.jp', 'com.br', 'com.tr',
        }
        suffix = '.'.join(labels[-2:])
        if suffix in two_level_public_suffixes and len(labels) >= 3:
            return '.'.join(labels[-3:])

        return suffix

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
                value for key, value in getattr(raw_headers, 'items', list)()
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

    def _probe_endpoints(self, base_url, progress_offset=0, progress_total=None):
        """
        Probe lightweight technology endpoints.

        :param str base_url:
        :param int progress_offset: completed progress steps before endpoint probes
        :param int|None progress_total: total progress steps for callback reporting
        :return: dict
        """

        statuses = {}
        total = progress_total or len(self.PROBES)
        for index, probe_path in enumerate(self.PROBES, start=1):
            response = self._request(urljoin(base_url, probe_path.lstrip('/')), method='HEAD')
            if response is not None and hasattr(response, 'status'):
                statuses[probe_path] = int(getattr(response, 'status', 0))
            self._emit_progress(
                progress_offset + index,
                total,
                'probe {0}/{1}'.format(index, len(self.PROBES))
            )
        return statuses

    def _probe_dotcms_endpoint_signals(self, base_url):
        """
        Probe narrow dotCMS admin redirect/header signals.

        Some dotCMS deployments do not expose generator meta tags or x-dot*
        headers on the root page. A redirect from Strapi-like admin paths to
        /dotAdmin is a strong dotCMS signal and prevents endpoint-only Strapi
        false positives on dotCMS targets.

        :param str base_url:
        :return: list[dict]
        """

        signals = []
        seen_values = set()
        probe_paths = ('/admin/init', '/admin/init/')

        for probe_path in probe_paths:
            response = self._request(urljoin(base_url, probe_path.lstrip('/')), method='HEAD')
            if response is None:
                continue

            headers = self._extract_headers(response)
            dot_server = str(headers.get('x-dot-server', '') or '').strip()
            if 'dotcms' in dot_server.lower():
                value = 'x-dot-server={0}'.format(dot_server)
                if value not in seen_values:
                    signals.append({'type': 'header', 'value': value, 'weight': 10})
                    seen_values.add(value)

            has_dot_request_cost = 'x-dotrequest-cost' in headers
            has_dot_ratelimit = any(str(header_name).startswith('x-dotratelimit-') for header_name in headers)
            if has_dot_request_cost and has_dot_ratelimit:
                value = 'x-dotrequest-cost+x-dotratelimit-*'
                if value not in seen_values:
                    signals.append({'type': 'header', 'value': value, 'weight': 9})
                    seen_values.add(value)

            location = str(headers.get('location', '') or '').strip()
            if '/dotadmin' in location.lower():
                value = '{0} -> {1}'.format(probe_path, location)
                if value not in seen_values:
                    signals.append({'type': 'endpoint-redirect', 'value': value, 'weight': 9})
                    seen_values.add(value)

        return signals

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

        runtime = self.TECHNOLOGY_RUNTIME_MAP.get(technology)
        if runtime and self._should_propagate_runtime_from_signal(signal_type):
            self._add_runtime_signal(runtime, 'technology', technology, min(float(weight), 4))

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

    def _apply_server_infrastructure_rules(self, headers):
        """
        Add infrastructure signals from the HTTP Server header.

        Server software is treated as infrastructure only. It must not mutate
        application, framework or runtime candidates.

        :param dict headers:
        :return: None
        """

        server_header = str(headers.get('server', '')).strip()
        server = server_header.lower()

        if not server:
            return

        server_signal = 'server={0}'.format(server_header)
        server_rules = (
            ('Apache Tomcat', ('apache-coyote', 'apache tomcat', 'tomcat')),
            ('Eclipse Jetty', ('jetty',)),
            ('Microsoft IIS', ('microsoft-iis', 'iis/')),
            ('OpenResty', ('openresty',)),
            ('LiteSpeed', ('litespeed',)),
            ('lighttpd', ('lighttpd',)),
            ('Tornado', ('tornadoserver', 'tornado server')),
            ('Gunicorn', ('gunicorn',)),
            ('Uvicorn', ('uvicorn',)),
            ('Hypercorn', ('hypercorn',)),
            ('Waitress', ('waitress',)),
            ('Caddy', ('caddy',)),
            ('Envoy', ('envoy',)),
            ('Traefik', ('traefik',)),
            ('Nginx', ('nginx',)),
        )

        for provider, aliases in server_rules:
            if any(alias in server for alias in aliases):
                self._add_infrastructure_signal(provider, 'header', server_signal, 8)
                return

        if re.search(r'(^|[^a-z0-9])apache(/|\s|$)', server):
            self._add_infrastructure_signal('Apache HTTP Server', 'header', server_signal, 8)


    def _apply_qrator_infrastructure_rules(self, headers, cookies, body_lower, not_found_headers=None, not_found_body_lower=''):
        """
        Add Qrator Labs edge/security infrastructure signals.

        Qrator Labs commonly appears as an HTTP reverse proxy / DDoS
        protection / WAF / CDN edge. Keep these signals in the
        infrastructure bucket so QRATOR does not overwrite application or
        runtime fingerprints.

        :param dict headers: normalized root response headers
        :param list cookies: normalized root response cookie names
        :param str body_lower: normalized root response body
        :param dict|None not_found_headers: normalized 404 probe headers
        :param str not_found_body_lower: normalized 404 probe body
        :return: None
        """

        not_found_headers = not_found_headers or {}
        server_header = str(headers.get('server', '') or '').strip()
        server = server_header.lower()
        not_found_server_header = str(not_found_headers.get('server', '') or '').strip()
        not_found_server = not_found_server_header.lower()
        qrator_header_names = (
            'x-qrator-requestid',
            'x-qrator-request-id',
            'x-q-domid',
            'x-qrator-ip-source',
            'x-qrator-tcp-info',
            'x-q-geoip',
        )

        if server == 'qrator':
            self._add_infrastructure_signal('QRATOR', 'header', 'server={0}'.format(server_header), 18)
        elif 'qrator' in server:
            self._add_infrastructure_signal('QRATOR', 'header', 'server={0}'.format(server_header), 12)

        if not_found_server == 'qrator':
            self._add_infrastructure_signal('QRATOR', '404-header', 'server={0}'.format(not_found_server_header), 15)
        elif 'qrator' in not_found_server:
            self._add_infrastructure_signal('QRATOR', '404-header', 'server={0}'.format(not_found_server_header), 10)

        for header_name in qrator_header_names:
            if header_name in headers:
                self._add_infrastructure_signal('QRATOR', 'header', header_name, 11)

        for header_name in qrator_header_names:
            if header_name in not_found_headers:
                self._add_infrastructure_signal('QRATOR', '404-header', header_name, 9)

        if 'qrator_jsid' in cookies:
            self._add_infrastructure_signal('QRATOR', 'cookie', 'qrator_jsid', 11)

        if '/qrerror/' in body_lower or '/qrerror/' in not_found_body_lower:
            self._add_infrastructure_signal('QRATOR', 'error-page', '/qrerror/', 9)

        if 'qrator_jsid' in body_lower or 'qrator_jsid' in not_found_body_lower:
            self._add_infrastructure_signal('QRATOR', 'challenge', 'qrator_jsid', 8)

        if 'qrator labs' in body_lower or 'qrator labs' in not_found_body_lower:
            self._add_infrastructure_signal('QRATOR', 'body', 'Qrator Labs', 8)

    def _apply_dotcms_rules(self, body_lower, headers, cookies, probe_signals=None):
        """
        Add conservative dotCMS fingerprint signals.

        dotCMS often does not expose a generator meta tag or footer marker on
        production sites. Keep detection limited to vendor-specific x-dot*
        headers, dotCMS cookie pairs, or multiple dotCMS body/API markers.
        Generic AWS ALB cookies, JSESSIONID, Java and Tomcat markers are
        intentionally ignored here to avoid weak dotCMS false positives.

        :param str body_lower: normalized response body
        :param dict headers: normalized response headers
        :param list cookies: normalized cookie names
        :param list|None probe_signals: active dotCMS probe signals
        :return: None
        """

        probe_signals = probe_signals or []
        for signal in probe_signals:
            self._add_signal(
                'dotCMS',
                self.CMS_CATEGORY,
                signal.get('type', 'probe'),
                signal.get('value', 'dotCMS probe'),
                signal.get('weight', 7),
            )

        dot_server = str(headers.get('x-dot-server', '') or '').strip()
        dot_server_lower = dot_server.lower()
        if 'dotcms' in dot_server_lower:
            self._add_signal('dotCMS', self.CMS_CATEGORY, 'header', 'x-dot-server={0}'.format(dot_server), 10)
            return

        has_dot_request_cost = 'x-dotrequest-cost' in headers
        has_dot_ratelimit = any(str(header_name).startswith('x-dotratelimit-') for header_name in headers)
        if has_dot_request_cost and has_dot_ratelimit:
            self._add_signal('dotCMS', self.CMS_CATEGORY, 'header', 'x-dotrequest-cost+x-dotratelimit-*', 9)
            return

        dotcms_cookies = {'opvc', 'dmid', 'sitevisitscookie', 'svc', 'dwrsessionid', 'rme'}
        found_cookies = sorted(cookie for cookie in cookies if cookie in dotcms_cookies)
        if dot_server and len(found_cookies) >= 1:
            self._add_signal('dotCMS', self.CMS_CATEGORY, 'header+cookie', 'x-dot-server+{0}'.format(found_cookies[0]), 9)
            return
        if len(found_cookies) >= 2:
            self._add_signal('dotCMS', self.CMS_CATEGORY, 'cookie', '+'.join(found_cookies[:3]), 7)

        body_markers = (
            'data-dot-object=',
            'data-dot-identifier=',
            'data-dot-accept-types=',
            '/api/v1/page/json/',
            '/api/v1/nav/',
            '/dotadmin',
            '/dotajaxdirector/',
        )
        found_markers = sorted(marker for marker in body_markers if marker in body_lower)
        if len(found_markers) >= 2:
            self._add_signal('dotCMS', self.CMS_CATEGORY, 'markup', '+'.join(found_markers[:3]), 7)
        elif len(found_markers) == 1 and len(found_cookies) >= 1:
            self._add_signal('dotCMS', self.CMS_CATEGORY, 'markup+cookie', '{0}+{1}'.format(found_markers[0], found_cookies[0]), 7)


    @classmethod
    def _contains_mogutacms_brand(cls, text):
        """
        Return True when text contains an explicit MogutaCMS brand marker.

        The matcher intentionally avoids a standalone "moguta" token because
        portfolio pages, comparison articles and vendor links can mention the
        product without proving that the scanned target runs on it.

        :param str text: normalized text
        :return: check result
        :rtype: bool
        """

        source = str(text or '').lower()
        return re.search(r'(?<![a-z0-9])moguta\s*\.?\s*cms(?![a-z0-9])', source) is not None \
            or re.search(r'(?<![a-z0-9])mogutacms(?![a-z0-9])', source) is not None

    @classmethod
    def _has_mogutacms_powered_by_marker(cls, body_lower):
        """
        Return True for explicit powered-by footer style MogutaCMS markers.

        Examples such as "Сайт работает на движке: Moguta.CMS" are strong
        production-site evidence. Plain portfolio/marketing mentions are not
        accepted by this rule.

        :param str body_lower: normalized response body
        :return: check result
        :rtype: bool
        """

        body_text = str(body_lower or '').lower()
        if cls._contains_mogutacms_brand(body_text) is not True:
            return False

        return (
            'сайт работает на движке' in body_text
            or 'работает на движке' in body_text
            or 'powered by' in body_text
        )

    def _apply_mogutacms_rules(self, body_lower, generator):
        """
        Apply conservative passive MogutaCMS fingerprint signals.

        MogutaCMS is identified only from explicit generator/powered-by
        branding or from multiple documented engine asset paths. A generic
        vendor mention or a single ``mg-*`` path is not enough to avoid
        corrupting fingerprints on portfolio, comparison or unrelated pages.

        :param str body_lower: normalized response body
        :param str generator: raw generator meta value
        :return: None
        """

        generator_lower = str(generator or '').lower()
        has_generator = self._contains_mogutacms_brand(generator_lower)
        has_powered_by = self._has_mogutacms_powered_by_marker(body_lower)

        if has_generator:
            self._add_signal('MogutaCMS', self.ECOMMERCE_CATEGORY, 'meta', 'generator={0}'.format(generator), 8)

        if has_powered_by:
            self._add_signal('MogutaCMS', self.ECOMMERCE_CATEGORY, 'markup', 'powered by MogutaCMS', 9)

        engine_markers = (
            '/mg-templates/',
            '/mg-core/',
            '/mg-admin/',
            '/mg-plugins/',
            '/mg-pages/',
        )
        found_markers = sorted(marker for marker in engine_markers if marker in str(body_lower or ''))

        if len(found_markers) >= 2:
            self._add_signal('MogutaCMS', self.ECOMMERCE_CATEGORY, 'asset', '+'.join(found_markers[:3]), 8)
        elif len(found_markers) == 1 and (has_generator or has_powered_by):
            self._add_signal('MogutaCMS', self.ECOMMERCE_CATEGORY, 'asset+brand', found_markers[0], 4)


    def _apply_evolution_cms_rules(self, body_lower, generator, probe_statuses, not_found_status):
        """
        Apply strong Evolution CMS signals.

        Evolution CMS descends from MODX Evolution, but short words like
        "evo" or the generic /manager/ path are too noisy for standalone
        detection. Keep the rule limited to explicit branding or core fallback
        text, and use endpoint reachability only as corroborating evidence.

        :param str body_lower: normalized response body
        :param str generator: raw generator meta value
        :param dict probe_statuses: fingerprint endpoint probe statuses
        :param int not_found_status: neutral 404-baseline status
        :return: None
        """

        generator_lower = str(generator or '').lower()
        explicit_markers = (
            'evolution cms',
            'evolutioncms',
            'modx evolution',
        )

        has_explicit_marker = any(marker in generator_lower or marker in body_lower for marker in explicit_markers)

        if any(marker in generator_lower for marker in explicit_markers):
            self._add_signal('Evolution CMS', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 8)

        if 'powered by evolution cms' in body_lower:
            self._add_signal('Evolution CMS', self.CMS_CATEGORY, 'markup', 'powered by evolution cms', 7)

        if (
            'evolution cms is not currently installed' in body_lower
            or 'please run the evolution cms install utility' in body_lower
        ):
            self._add_signal('Evolution CMS', self.CMS_CATEGORY, 'markup', 'install fallback', 8)

        if 'modx evolution' in body_lower:
            self._add_signal('Evolution CMS', self.CMS_CATEGORY, 'markup', 'modx evolution', 7)

        if has_explicit_marker and self._is_distinct_probe_up(
            probe_statuses,
            '/manager/',
            [200, 301, 302, 401, 403],
            not_found_status,
        ):
            self._add_signal('Evolution CMS', self.CMS_CATEGORY, 'endpoint', '/manager/', 3)


    def _apply_datalife_engine_rules(self, body_lower, generator):
        """
        Apply conservative passive DataLife Engine (DLE) signals.

        DLE installations often remove explicit generator branding, but still
        expose stable runtime globals and engine asset bundle paths such as
        ``dle_root`` / ``dle_login_hash`` and ``engine/classes/js/dle_js.js``.
        Keep short ``dle`` text out of body matching to avoid false positives.

        :param str body_lower: normalized response body
        :param str generator: raw generator meta value
        :return: None
        """

        body_text = str(body_lower or '').lower()
        generator_lower = str(generator or '').lower()
        brand_markers = (
            'datalife engine',
            'data life engine',
            'dle-news.ru',
            'dle-news.com',
            'softnews media group',
        )

        if any(marker in generator_lower for marker in brand_markers):
            self._add_signal('DataLife Engine', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 8)

        if any(marker in body_text for marker in brand_markers):
            self._add_signal('DataLife Engine', self.CMS_CATEGORY, 'markup', 'DataLife Engine branding', 8)

        dle_globals = sorted(set(re.findall(
            r'(?:var\s+|window\.)(allow_dle_delete_news|dle_(?:root|admin|login_hash|group|skin|wysiwyg|act_lang|user_id|search_delay|search_value))\b',
            body_text,
        )))
        if len(dle_globals) >= 2:
            self._add_signal('DataLife Engine', self.CMS_CATEGORY, 'script', '+'.join(dle_globals[:4]), 8)
        elif len(dle_globals) == 1 and any(marker in body_text for marker in brand_markers):
            self._add_signal('DataLife Engine', self.CMS_CATEGORY, 'script+brand', dle_globals[0], 4)

        has_dle_js_asset = '/engine/classes/js/dle_js.js' in body_text or 'engine/classes/js/dle_js.js' in body_text
        has_dle_min_asset = '/engine/classes/min/index.php' in body_text or 'engine/classes/min/index.php' in body_text
        if has_dle_js_asset:
            self._add_signal('DataLife Engine', self.CMS_CATEGORY, 'asset', 'engine/classes/js/dle_js.js', 8)
        elif has_dle_min_asset and (len(dle_globals) >= 1 or any(marker in body_text for marker in brand_markers)):
            self._add_signal('DataLife Engine', self.CMS_CATEGORY, 'asset+script', 'engine/classes/min/index.php', 5)

        ajax_markers = (
            'dle_root+"engine/ajax/',
            "dle_root+'engine/ajax/",
            'dle_root + "engine/ajax/',
            "dle_root + 'engine/ajax/",
            '/engine/ajax/controller.php?mod=',
            'engine/ajax/controller.php?mod=',
        )
        if any(marker in body_text for marker in ajax_markers) and (len(dle_globals) >= 1 or has_dle_js_asset):
            self._add_signal('DataLife Engine', self.CMS_CATEGORY, 'ajax', 'engine/ajax/', 5)

    def _apply_extended_cms_catalog_rules(self, body_lower, headers, cookies, generator):
        """
        Apply extended catalog signals for CMSs not covered by dedicated rules.

        :param str body_lower: normalized response body
        :param dict headers: normalized response headers
        :param list cookies: normalized cookie names
        :param str generator: raw generator meta value
        :return: None
        """

        generator_lower = str(generator).lower()

        for technology, category, aliases in self.EXTENDED_CMS_GENERATOR_SIGNATURES:
            for alias in aliases:
                if alias in generator_lower:
                    self._add_signal(technology, category, 'meta', 'generator={0}'.format(generator), 7)
                    break

        for technology, category, markers in self.EXTENDED_CMS_BODY_SIGNATURES:
            for marker in markers:
                if marker in body_lower:
                    self._add_signal(technology, category, 'markup', marker, 6)
                    break

        for technology, category, header_name, header_value in self.EXTENDED_CMS_HEADER_SIGNATURES:
            if header_name not in headers:
                continue
            if header_value is not None and header_value not in str(headers.get(header_name, '')).lower():
                continue
            self._add_signal(technology, category, 'header', header_name, 7)

        for technology, category, cookie_markers in self.EXTENDED_CMS_COOKIE_SIGNATURES:
            for cookie_marker in cookie_markers:
                if any(cookie == cookie_marker or cookie.startswith(cookie_marker) for cookie in cookies):
                    self._add_signal(technology, category, 'cookie', cookie_marker, 6)
                    break

    @staticmethod
    def _has_diafan_meta_author(body_lower):
        """
        Return True when an HTML meta author tag exposes DiafanCMS branding.

        DiafanCMS commonly exposes a non-generator marker such as
        <meta content="DIAFAN.CMS https://www.diafan.ru/" name="author">.
        The check is constrained to meta tags to avoid classifying generic
        body text that merely links to or mentions Diafan.

        :param str body_lower: normalized response body
        :return: bool
        """

        body_text = str(body_lower or '')
        return (
            re.search(r'<meta[^>]+name=["\']author["\'][^>]+content=["\'][^"\']*diafan\.cms', body_text)
            is not None
            or re.search(r'<meta[^>]+content=["\'][^"\']*diafan\.cms[^"\']*["\'][^>]+name=["\']author["\']', body_text)
            is not None
        )

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

    @staticmethod
    def _has_php_route_marker(body_lower, final_root_url):
        """
        Return True when the page exposes first-party PHP route/file markers.

        :param str body_lower:
        :param str final_root_url:
        :return: bool
        """

        final_root_lower = str(final_root_url or '').lower()
        if re.search(r'\.php(?:[?#/&]|$)', final_root_lower):
            return True

        body_text = str(body_lower or '')
        if re.search(r"(?:href|src|action)=['\"](?:/|\.\.?/)?[^'\"]{0,160}\.php(?:[?#/&'\"]|$)", body_text):
            return True

        return re.search(
            r"\b(?:index|read|show|article|news|print|login|search|catalog|page|view|download|profile|forum|topic|item|anons|articles)\.php(?:[?#/&\"']|$)",
            body_text,
        ) is not None

    @staticmethod
    def _has_rails_authenticity_token_meta(body_lower):
        """
        Return True for canonical Rails CSRF meta tags.

        Rails commonly emits a csrf-param meta tag with the fixed
        authenticity_token value together with csrf-token. Keep this more
        specific than a generic csrf-token match to avoid false positives on
        other frameworks.

        :param str body_lower: normalized response body
        :return: check result
        :rtype: bool
        """

        body_text = str(body_lower or '')
        if 'csrf-token' not in body_text:
            return False

        return (
            re.search(
                r'<meta[^>]+name=["\']csrf-param["\'][^>]+content=["\']authenticity_token["\']',
                body_text,
            ) is not None
            or re.search(
                r'<meta[^>]+content=["\']authenticity_token["\'][^>]+name=["\']csrf-param["\']',
                body_text,
            ) is not None
        )

    @staticmethod
    def _has_rails_ujs_marker(body_lower):
        """
        Return True for Rails UJS/Turbo integration markers.

        These markers are not used as standalone Rails evidence. They only
        strengthen an existing Rails CSRF/cookie hint.

        :param str body_lower: normalized response body
        :return: check result
        :rtype: bool
        """

        body_text = str(body_lower or '')
        markers = (
            '@rails/ujs',
            'rails-ujs',
            'turbo-rails',
            'data-turbo-track=',
            'data-disable-with=',
            'data-remote="true"',
            "data-remote='true'",
            'data-method="delete"',
            'data-method="patch"',
            'data-method="put"',
            "data-method='delete'",
            "data-method='patch'",
            "data-method='put'",
        )
        return any(marker in body_text for marker in markers)

    @staticmethod
    def _has_rails_asset_marker(body_lower):
        """
        Return True for Rails asset pipeline or Webpacker application assets.

        Generic application.js/application.css names are intentionally ignored.
        A digest-like asset name is required and the result is only used with
        Rails corroboration.

        :param str body_lower: normalized response body
        :return: check result
        :rtype: bool
        """

        body_text = str(body_lower or '')
        return (
            re.search(r'/assets/application-[a-z0-9]{8,}\.(?:css|js)(?:[?"\']|$)', body_text) is not None
            or re.search(r'/packs/(?:js|css)/application-[a-z0-9]{8,}\.(?:css|js)(?:[?"\']|$)', body_text) is not None
            or re.search(r'/assets/manifest-[a-z0-9]{8,}\.json(?:[?"\']|$)', body_text) is not None
        )

    @staticmethod
    def _has_rails_error_marker(body_lower):
        """
        Return True for exposed Rails exception or diagnostic markers.

        These strings are framework-specific and only consume response bodies
        already fetched by fingerprinting. No active error probing is added.

        :param str body_lower: normalized response body
        :return: check result
        :rtype: bool
        """

        body_text = str(body_lower or '')
        error_markers = (
            'actioncontroller::routingerror',
            'actioncontroller::unknownformat',
            'actionview::template::error',
            'activerecord::',
            'rails.root',
            'action dispatch',
        )
        return any(marker in body_text for marker in error_markers)

    @staticmethod
    def _looks_like_express_not_found(not_found_status, not_found_body_lower):
        """
        Return True for canonical Express finalhandler 404 responses.

        :param int not_found_status:
        :param str not_found_body_lower:
        :return: bool
        """

        if int(not_found_status or 0) != 404:
            return False

        body_text = str(not_found_body_lower or '').strip()
        if len(body_text) > 1200:
            return False

        return (
            body_text.startswith(('cannot get /', 'cannot post /'))
            or '<pre>cannot get /' in body_text
            or '<pre>cannot post /' in body_text
        )

    @staticmethod
    def _looks_like_nest_not_found(not_found_status, not_found_body_lower):
        """
        Return True for canonical NestJS JSON 404 responses.

        :param int not_found_status:
        :param str not_found_body_lower:
        :return: bool
        """

        if int(not_found_status or 0) != 404:
            return False

        body_text = str(not_found_body_lower or '').strip()
        if len(body_text) > 1600:
            return False

        return (
            '"statuscode"' in body_text
            and '"message"' in body_text
            and 'cannot get /' in body_text
            and '"error"' in body_text
            and 'not found' in body_text
        )

    @staticmethod
    def _looks_like_fastify_not_found(not_found_status, not_found_body_lower):
        """
        Return True for canonical Fastify route-not-found responses.

        :param int not_found_status:
        :param str not_found_body_lower:
        :return: bool
        """

        if int(not_found_status or 0) != 404:
            return False

        body_text = str(not_found_body_lower or '').strip()
        if len(body_text) > 1600:
            return False

        return 'route get:' in body_text and 'not found' in body_text

    @staticmethod
    def _is_distinct_probe_status(probe_status, not_found_status):
        """
        Return True when a fingerprint probe status differs from the 404 baseline.

        This avoids counting catch-all/soft404 responses as endpoint evidence
        when the missing-path probe returns the same successful-looking status.

        :param int|None probe_status: probe HTTP status
        :param int|None not_found_status: missing-path baseline HTTP status
        :return: bool
        """

        try:
            status = int(probe_status or 0)
        except (TypeError, ValueError):
            return False

        if status <= 0:
            return False

        try:
            baseline_status = int(not_found_status or 0)
        except (TypeError, ValueError):
            baseline_status = 0

        if baseline_status in [200, 301, 302, 401, 403, 405] and status == baseline_status:
            return False

        return True

    @classmethod
    def _is_distinct_probe_up(cls, probe_statuses, path, allowed_statuses, not_found_status):
        """
        Return True when a probe path is reachable and not equal to soft404 baseline.

        :param dict probe_statuses: collected probe statuses
        :param str path: probe path
        :param list[int] allowed_statuses: statuses that represent a useful hit
        :param int|None not_found_status: missing-path baseline HTTP status
        :return: bool
        """

        status = probe_statuses.get(path)
        return status in allowed_statuses and cls._is_distinct_probe_status(status, not_found_status)

    @staticmethod
    def _should_propagate_runtime_from_signal(signal_type):
        """
        Return True when an application signal is strong enough to infer runtime.

        Pure endpoint reachability is intentionally excluded: many legacy PHP
        sites expose /docs, /swagger or redirected admin paths without running
        the framework that owns the endpoint name.

        :param str signal_type:
        :return: bool
        """

        return str(signal_type or '').lower() != 'endpoint'

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
        x_powered_cms = str(headers.get('x-powered-cms', '')).lower()
        server = str(headers.get('server', '')).lower()
        via = str(headers.get('via', '')).lower()
        x_cache = str(headers.get('x-cache', '')).lower()
        x_served_by = str(headers.get('x-served-by', '')).lower()
        x_amz_cf_id = str(headers.get('x-amz-cf-id', '')).lower()
        x_amz_request_id = str(headers.get('x-amz-request-id', '')).lower()
        x_amz_id_2 = str(headers.get('x-amz-id-2', '')).lower()
        content_security_policy = str(headers.get('content-security-policy', '')).lower()
        surrogate_key = str(headers.get('surrogate-key', '')).lower()
        x_wf_region = str(headers.get('x-wf-region', '')).lower()
        final_root_lower = str(final_root_url).lower()
        host_lower = str(getattr(self.__config, 'host', '') or '').lower()
        webflow_hosted_context = bool(
            host_lower == 'webflow.io'
            or host_lower.endswith('.webflow.io')
            or x_wf_region
            or 'webflow.io' in surrogate_key
            or 'webflow.com' in content_security_policy
            or 'webflow.io' in content_security_policy
        )
        not_found_body_lower = str(not_found_body).lower()
        not_found_powered_by = str(not_found_headers.get('x-powered-by', '')).lower()
        not_found_server = str(not_found_headers.get('server', '')).lower()
        php_route_marker = self._has_php_route_marker(body_lower, final_root_lower)
        express_not_found = self._looks_like_express_not_found(not_found_status, not_found_body_lower)
        nest_not_found = self._looks_like_nest_not_found(not_found_status, not_found_body_lower)
        fastify_not_found = self._looks_like_fastify_not_found(not_found_status, not_found_body_lower)
        swagger_probe_up = any(probe_statuses.get(path) in [200, 301, 302, 401, 403] for path in [
            '/swagger',
            '/swagger/',
            '/swagger-json',
            '/api-json',
            '/openapi.json',
        ])
        docs_probe_up = any(probe_statuses.get(path) in [200, 301, 302, 401, 403] for path in ['/docs', '/redoc'])

        # WordPress
        wordpress_root_evidence = False
        if 'wordpress' in generator_lower:
            self._add_signal('WordPress', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 7)
            wordpress_root_evidence = True
        if '/wp-content/' in body_lower:
            self._add_signal('WordPress', self.CMS_CATEGORY, 'markup', '/wp-content/', 6)
            wordpress_root_evidence = True
        if '/wp-includes/' in body_lower:
            self._add_signal('WordPress', self.CMS_CATEGORY, 'markup', '/wp-includes/', 5)
            wordpress_root_evidence = True
        if any(cookie.startswith(('wordpress_', 'wp-settings-')) for cookie in cookies):
            wordpress_root_evidence = True

        wordpress_static_probes = (
            ('/wp-content/', 6),
            ('/wp-includes/', 5),
            ('/wp-content/plugins/', 4),
            ('/wp-content/themes/', 4),
        )
        for probe_path, weight in wordpress_static_probes:
            if webflow_hosted_context and not wordpress_root_evidence:
                continue
            if self._is_distinct_probe_up(probe_statuses, probe_path, [200, 301, 302, 401, 403], not_found_status):
                self._add_signal('WordPress', self.CMS_CATEGORY, 'endpoint', probe_path, weight)

        if self._is_distinct_probe_up(probe_statuses, '/wp-json/', [200, 401, 403], not_found_status):
            self._add_signal('WordPress', self.CMS_CATEGORY, 'endpoint', '/wp-json/', 5)
        if self._is_distinct_probe_up(probe_statuses, '/wp-login.php', [200, 301, 302, 401, 403], not_found_status):
            self._add_signal('WordPress', self.CMS_CATEGORY, 'endpoint', '/wp-login.php', 2)
        if self._is_distinct_probe_up(probe_statuses, '/xmlrpc.php', [200, 301, 302, 401, 403, 405], not_found_status):
            self._add_signal('WordPress', self.CMS_CATEGORY, 'endpoint', '/xmlrpc.php', 2)
        if any(cookie.startswith(('wordpress_', 'wp-settings-')) for cookie in cookies):
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

        # DiafanCMS
        if self._has_diafan_meta_author(body_lower):
            self._add_signal('DiafanCMS', self.CMS_CATEGORY, 'meta', 'author=DIAFAN.CMS', 8)

        # Bitrix
        if 'bitrix' in x_powered_cms:
            self._add_signal('Bitrix', self.CMS_CATEGORY, 'header', 'x-powered-cms={0}'.format(headers.get('x-powered-cms')), 9)
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

        # Mobirise
        if 'mobirise' in generator_lower:
            self._add_signal('Mobirise', self.SITE_BUILDER_CATEGORY, 'meta', 'generator={0}'.format(generator), 8)
        if '/assets/mobirise/' in body_lower or '/assets/web/assets/mobirise-icons' in body_lower \
                or 'mobirise-icons.css' in body_lower:
            self._add_signal('Mobirise', self.SITE_BUILDER_CATEGORY, 'asset', 'assets/mobirise|mobirise-icons', 7)
        if 'mbr-additional.css' in body_lower or 'mbr-section-title' in body_lower \
                or 'mbr-section-btn' in body_lower or 'mbr-fonts-style' in body_lower:
            self._add_signal('Mobirise', self.SITE_BUILDER_CATEGORY, 'markup', 'mbr-*', 5)

        # Webflow
        if host_lower == 'webflow.io' or host_lower.endswith('.webflow.io'):
            self._add_signal('Webflow', self.SITE_BUILDER_CATEGORY, 'host', 'host=*.webflow.io', 9)
        if x_wf_region:
            self._add_signal('Webflow', self.SITE_BUILDER_CATEGORY, 'header', 'x-wf-region', 8)
        if 'webflow.io' in surrogate_key:
            self._add_signal('Webflow', self.SITE_BUILDER_CATEGORY, 'header', 'surrogate-key=webflow.io', 7)
        if 'webflow.com' in content_security_policy or 'webflow.io' in content_security_policy:
            self._add_signal('Webflow', self.SITE_BUILDER_CATEGORY, 'header', 'csp frame-ancestors webflow', 6)
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
        if any(cookie.startswith(('woocommerce_', 'wp_woocommerce_session_')) for cookie in cookies):
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
        if any(cookie.startswith(('phpbb3_', 'phpbb_')) for cookie in cookies):
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

        # Open Journal Systems
        ojs_text_hint = (
                'open journal systems' in generator_lower
                or 'open journal systems' in body_lower
                or 'pkp_structure_' in body_lower
        )

        if 'open journal systems' in generator_lower:
            self._add_signal('Open Journal Systems', self.CMS_CATEGORY, 'meta', 'generator={0}'.format(generator), 9)
        if 'pkp_structure_' in body_lower or 'pkp_page_' in body_lower:
            self._add_signal('Open Journal Systems', self.CMS_CATEGORY, 'markup', 'pkp_structure_*|pkp_page_*', 6)
        if '/plugins/themes/' in body_lower and (
                '/lib/pkp/' in body_lower or '/index.php/' in body_lower or ojs_text_hint):
            self._add_signal('Open Journal Systems', self.CMS_CATEGORY, 'asset', '/plugins/themes/ + OJS hint', 5)
        if any(probe_statuses.get(path) in [200, 301, 302, 401, 403] for path in [
            '/index.php/index/login',
            '/index.php/index/search',
            '/index.php/index/about',
        ]) and ojs_text_hint:
            self._add_signal('Open Journal Systems', self.CMS_CATEGORY, 'endpoint', '/index.php/index/*', 3)

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

        # MogutaCMS
        self._apply_mogutacms_rules(
            body_lower=body_lower,
            generator=generator,
        )

        # Evolution CMS
        self._apply_evolution_cms_rules(
            body_lower=body_lower,
            generator=generator,
            probe_statuses=probe_statuses,
            not_found_status=not_found_status,
        )

        # DataLife Engine
        self._apply_datalife_engine_rules(
            body_lower=body_lower,
            generator=generator,
        )

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
        strapi_header_hint = 'strapi' in x_powered_by
        strapi_markup_hint = 'strapi' in body_lower and ('/admin/init' in body_lower or '/uploads/' in body_lower)
        strapi_init_up = self._is_distinct_probe_up(probe_statuses, '/admin/init', [200], not_found_status)
        strapi_hint = strapi_header_hint or strapi_markup_hint or strapi_init_up

        if strapi_header_hint:
            self._add_signal('Strapi', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by')), 8)
        if strapi_markup_hint:
            self._add_signal('Strapi', self.FRAMEWORK_CATEGORY, 'markup', 'strapi + /admin/init|/uploads/', 7)
        if strapi_init_up:
            self._add_signal('Strapi', self.FRAMEWORK_CATEGORY, 'endpoint', '/admin/init', 7)
        if strapi_hint and self._is_distinct_probe_up(probe_statuses, '/admin', [200, 301, 302, 401, 403], not_found_status):
            self._add_signal('Strapi', self.FRAMEWORK_CATEGORY, 'endpoint', '/admin', 4)
        if strapi_hint and self._is_distinct_probe_up(probe_statuses, '/uploads/', [200, 301, 302, 401, 403], not_found_status):
            self._add_signal('Strapi', self.FRAMEWORK_CATEGORY, 'endpoint', '/uploads/', 4)

        # dotCMS
        self._apply_dotcms_rules(
            body_lower=body_lower,
            headers=headers,
            cookies=cookies,
            probe_signals=self.__dotcms_probe_signals,
        )

        # Extended CMS catalog extension
        self._apply_extended_cms_catalog_rules(
            body_lower=body_lower,
            headers=headers,
            cookies=cookies,
            generator=generator,
        )

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
        rails_cookie_hint = '_rails_session' in cookies
        rails_exact_csrf = self._has_rails_authenticity_token_meta(body_lower)
        rails_csrf_pair = 'csrf-param' in body_lower and 'csrf-token' in body_lower
        rails_ujs_hint = self._has_rails_ujs_marker(body_lower)
        rails_asset_hint = self._has_rails_asset_marker(body_lower)
        rails_error_hint = (
            self._has_rails_error_marker(body_lower)
            or self._has_rails_error_marker(not_found_body_lower)
        )

        if rails_cookie_hint:
            self._add_signal('Ruby on Rails', self.FRAMEWORK_CATEGORY, 'cookie', '_rails_session', 8)

        if rails_exact_csrf:
            self._add_signal('Ruby on Rails', self.FRAMEWORK_CATEGORY, 'markup', 'csrf-param=authenticity_token|csrf-token', 8)
        elif rails_csrf_pair:
            self._add_signal('Ruby on Rails', self.FRAMEWORK_CATEGORY, 'markup', 'csrf-param|csrf-token', 5)

        if rails_ujs_hint and (rails_cookie_hint or rails_exact_csrf or rails_csrf_pair):
            self._add_signal('Ruby on Rails', self.FRAMEWORK_CATEGORY, 'script', 'rails-ujs|turbo-rails', 7)

        if rails_asset_hint and (rails_cookie_hint or rails_exact_csrf or rails_csrf_pair or rails_ujs_hint):
            self._add_signal('Ruby on Rails', self.FRAMEWORK_CATEGORY, 'asset', 'rails application asset', 5)

        if rails_error_hint:
            self._add_signal('Ruby on Rails', self.FRAMEWORK_CATEGORY, 'exception', 'Rails exception marker', 8)

        # Express / NestJS / Fastify / FastAPI / Koa / Hapi
        if 'express' in x_powered_by or 'express' in not_found_powered_by:
            self._add_signal('Express', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by') or not_found_headers.get('x-powered-by')), 8)
        if 'connect.sid' in cookies:
            self._add_signal('Express', self.FRAMEWORK_CATEGORY, 'cookie', 'connect.sid', 6)
        if express_not_found:
            self._add_signal('Express', self.FRAMEWORK_CATEGORY, '404', 'Cannot GET/POST', 7)

        if 'nest' in x_powered_by or 'nest' in not_found_powered_by:
            self._add_signal('NestJS', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by') or not_found_headers.get('x-powered-by')), 8)
        if nest_not_found:
            self._add_signal('NestJS', self.FRAMEWORK_CATEGORY, '404', 'statusCode + Cannot GET + Not Found', 9)
        if swagger_probe_up:
            self._add_signal('NestJS', self.FRAMEWORK_CATEGORY, 'endpoint', 'swagger/openapi', 4)

        if 'fastify' in x_powered_by or 'fastify' in server or 'fastify' in not_found_powered_by or 'fastify' in not_found_server:
            self._add_signal('Fastify', self.FRAMEWORK_CATEGORY, 'header', 'x-powered-by|server=fastify', 8)
        if fastify_not_found:
            self._add_signal('Fastify', self.FRAMEWORK_CATEGORY, '404', 'Route GET:* not found', 9)

        if 'uvicorn' in server or 'hypercorn' in server or 'uvicorn' in not_found_server or 'hypercorn' in not_found_server:
            self._add_signal('FastAPI', self.FRAMEWORK_CATEGORY, 'header', 'server=uvicorn|hypercorn', 6)
        if not_found_status == 404 and '"detail"' in not_found_body_lower and 'not found' in not_found_body_lower:
            self._add_signal('FastAPI', self.FRAMEWORK_CATEGORY, '404', '{"detail":"Not Found"}', 8)
        if probe_statuses.get('/openapi.json') in [200, 301, 302, 401, 403] or docs_probe_up:
            self._add_signal('FastAPI', self.FRAMEWORK_CATEGORY, 'endpoint', '/openapi.json|/docs|/redoc', 5)

        if 'php' in x_powered_by:
            self._add_runtime_signal('PHP', 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by')), 8)
        if 'phpsessid' in cookies:
            self._add_runtime_signal('PHP', 'cookie', 'PHPSESSID', 7)
        if php_route_marker:
            self._add_runtime_signal('PHP', 'route', '.php route marker', 4.5)
        if 'asp.net' in x_powered_by or 'x-aspnet-version' in headers:
            self._add_runtime_signal('.NET', 'header', 'x-powered-by|x-aspnet-version', 8)
        if 'asp.net_sessionid' in cookies:
            self._add_runtime_signal('.NET', 'cookie', 'ASP.NET_SessionId', 7)
        if '__viewstate' in body_lower or '__eventvalidation' in body_lower:
            self._add_runtime_signal('.NET', 'markup', '__VIEWSTATE|__EVENTVALIDATION', 7)
        if 'jsessionid' in cookies:
            self._add_runtime_signal('Java/JVM', 'cookie', 'JSESSIONID', 5)
        if 'werkzeug' in server or 'gunicorn' in server or 'uwsgi' in server:
            self._add_runtime_signal('Python', 'header', 'server=Werkzeug|gunicorn|uWSGI', 6)
        if 'uvicorn' in server or 'hypercorn' in server or 'uvicorn' in not_found_server or 'hypercorn' in not_found_server:
            self._add_runtime_signal('Python', 'header', 'server=uvicorn|hypercorn', 6)
        if 'csrftoken' in cookies or 'csrfmiddlewaretoken' in body_lower:
            self._add_runtime_signal('Python', 'csrf', 'csrftoken|csrfmiddlewaretoken', 4)
        if '_rails_session' in cookies:
            self._add_runtime_signal('Ruby', 'cookie', '_rails_session', 7)
        node_powered_by = any(['express' in x_powered_by, 'nest' in x_powered_by, 'fastify' in x_powered_by, 'koa' in x_powered_by, 'hapi' in x_powered_by])
        if node_powered_by:
            self._add_runtime_signal('Node.js', 'header', 'x-powered-by={0}'.format(headers.get('x-powered-by')), 7)
        if 'connect.sid' in cookies or 'koa:sess' in cookies or 'koa.sess' in cookies:
            self._add_runtime_signal('Node.js', 'cookie', 'connect.sid|koa:sess', 6)
        if express_not_found or nest_not_found or fastify_not_found:
            self._add_runtime_signal('Node.js', '404', 'canonical Node.js 404', 6)

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

        # Infrastructure: Qrator Labs security edge / reverse proxy
        self._apply_qrator_infrastructure_rules(
            headers=headers,
            cookies=cookies,
            body_lower=body_lower,
            not_found_headers=not_found_headers,
            not_found_body_lower=not_found_body_lower,
        )

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

        # Fastly / Akamai / server engines
        if 'fastly' in x_served_by or 'x-fastly-request-id' in headers:
            self._add_infrastructure_signal('Fastly', 'header', 'x-served-by|x-fastly-request-id', 9)
        if 'akamai' in server or 'akamai-grn' in headers:
            self._add_infrastructure_signal('Akamai', 'header', 'server=akamai|akamai-grn', 9)

        self._apply_server_infrastructure_rules(headers)

        # Hostinger / DDoS-Guard / Tencent Cloud
        if self._header_contains(headers, 'server', 'hcdn') or 'x-hcdn-cache-status' in headers \
                or self._header_contains(headers, 'platform', 'hostinger'):
            self._add_infrastructure_signal('Hostinger', 'header', 'server=hcdn|x-hcdn-cache-status|platform=hostinger', 9)
        if self._header_contains(headers, 'server', 'ddos-guard') or 'x-ddos-guard-request-id' in headers \
                or 'x-ddg-cache-status' in headers:
            self._add_infrastructure_signal('DDoS-Guard', 'header', 'server=ddos-guard|x-ddos-guard-request-id|x-ddg-cache-status', 9)
        if 'x-cos-request-id' in headers or 'x-cos-hash-crc64ecma' in headers \
                or self._header_contains(headers, 'server', 'tencent-cos'):
            self._add_infrastructure_signal('Tencent Cloud', 'header', 'x-cos-request-id|x-cos-hash-crc64ecma|server=tencent-cos', 9)

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

    def _add_runtime_signal(self, runtime, signal_type, value, weight):
        self.__runtime_scores[runtime] += weight
        self.__runtime_signals[runtime].append({'type': signal_type, 'value': value})

    def _build_runtime_candidates(self):
        candidates = []
        for runtime, score in self.__runtime_scores.items():
            candidates.append({'category': self.RUNTIME_CATEGORY, 'name': runtime, 'score': score})
        return sorted(candidates, key=lambda item: item['score'], reverse=True)

    def _build_runtime_result(self, runtime_candidates):
        if len(runtime_candidates) == 0:
            return {'name': 'unknown', 'category': self.RUNTIME_CATEGORY, 'confidence': 0, 'signals': [], 'candidates': []}
        top = runtime_candidates[0]
        second_score = runtime_candidates[1]['score'] if len(runtime_candidates) > 1 else 0
        return {'name': top['name'], 'category': self.RUNTIME_CATEGORY, 'confidence': self._calculate_confidence(top['score'], second_score), 'signals': self.__runtime_signals[top['name']], 'candidates': runtime_candidates}

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
