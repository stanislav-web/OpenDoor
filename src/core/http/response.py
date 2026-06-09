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

    Development Team: Stanislav WEB
"""

from src.core import helper
from src.core.http.socks import Socket
from .exceptions import ResponseError
from .providers import ResponseProvider
from src.core.http.plugins.response_plugin import ResponsePlugin, ResponsePluginError
from src.core.http.redirect_classifier import RedirectClassifier


class Response(ResponseProvider):

    """Response class"""

    def __init__(self, config, debug, **kwargs):
        """
        Response instance
        :param src.lib.browser.config.Config config: configurations
        :param src.lib.browser.debug.Debug debug: debugger
        """

        ResponseProvider.__init__(self, config)

        self.__debug = debug
        self.__config = config
        self.__tpl = kwargs.get('tpl')
        self.__subdomain_ip_cache = {}

        if True is self.__config.is_sniff:
            try:
                self.load_sniffers_plugins(self.__config.sniffers)
            except ResponsePluginError as error:
                raise ResponseError(str(error))

    def debug_response_data(
            self,
            response_data,
            request_url,
            items_size,
            total_size,
            response=None,
            request_source=None,
            crawl_enqueued_size=0,
            crawl_processed_size=0,
            base_total_size=None,
    ):
        """
        Emit runtime/debug output for an already classified response.

        This keeps response classification single-pass while allowing callers to
        defer visible runtime rendering until after auto-calibration and filters.

        :param tuple response_data: classified response tuple
        :param str request_url: original request URL
        :param int items_size: processed item count
        :param int total_size: total item count
        :param object response: optional raw response object
        :param str | None request_source: logical request source for UI markers
        :param int crawl_enqueued_size: accepted crawl URL count for progress labels
        :param int crawl_processed_size: processed crawl request count for progress labels
        :param int | None base_total_size: original dictionary total for crawl progress labels
        :return: True
        :rtype: bool
        """

        status, rendered_url, content_size, response_code = response_data
        redirect_uri = rendered_url if status == 'redirect' else None
        redirect_classification = None
        waf_detection = self.waf_detection if status == self.DEFAULT_WAF_STATUS else None
        stacktrace_detection = None
        secret_detection = None
        shadow_detection = None
        openredirect_detection = None
        malware_detection = None
        endpoint_detection = None

        if response is not None and status == 'redirect':
            redirect_classification = getattr(response, 'opendoor_redirect_classification', None)
        if response is not None and status == 'stacktrace':
            stacktrace_detection = getattr(response, 'opendoor_stacktrace_detection', None)
        if response is not None and status == 'secret':
            secret_detection = getattr(response, 'opendoor_secret_detection', None)
        if response is not None and status == 'shadow':
            shadow_detection = getattr(response, 'opendoor_shadow_detection', None)
        if response is not None and status == 'openredirect':
            openredirect_detection = getattr(response, 'opendoor_openredirect_detection', None)
        if response is not None and status == 'malware':
            malware_detection = getattr(response, 'opendoor_malware_detection', None)
        if response is not None and status == 'endpoint':
            endpoint_detection = getattr(response, 'opendoor_endpoint_detection', None)

        self.__debug_classified_response(
            status=status,
            request_url=request_url,
            redirect_uri=redirect_uri,
            items_size=items_size,
            total_size=total_size,
            content_size=content_size,
            response_code=response_code,
            waf_detection=waf_detection,
            stacktrace_detection=stacktrace_detection,
            secret_detection=secret_detection,
            shadow_detection=shadow_detection,
            openredirect_detection=openredirect_detection,
            malware_detection=malware_detection,
            endpoint_detection=endpoint_detection,
            redirect_classification=redirect_classification,
            request_source=request_source,
            crawl_enqueued_size=crawl_enqueued_size,
            crawl_processed_size=crawl_processed_size,
            base_total_size=base_total_size,
        )

        return True

    def __debug_classified_response(
            self,
            status,
            request_url,
            redirect_uri,
            items_size,
            total_size,
            content_size,
            response_code,
            waf_detection=None,
            stacktrace_detection=None,
            secret_detection=None,
            shadow_detection=None,
            openredirect_detection=None,
            malware_detection=None,
            endpoint_detection=None,
            redirect_classification=None,
            request_source=None,
            crawl_enqueued_size=0,
            crawl_processed_size=0,
            base_total_size=None,
    ):
        """
        Emit the paired runtime and deep classification debug events.

        :param str status: OpenDoor result bucket
        :param str request_url: request URL displayed in debug output
        :param str | None redirect_uri: redirect target when available
        :param int items_size: processed item count
        :param int total_size: total item count
        :param str | int content_size: formatted response size
        :param str | int response_code: HTTP response code
        :param dict | None waf_detection: optional WAF metadata
        :param dict | None stacktrace_detection: optional stacktrace metadata
        :param dict | None secret_detection: optional secret metadata
        :param dict | None shadow_detection: optional shadow metadata
        :param dict | None openredirect_detection: optional open redirect metadata
        :param dict | None malware_detection: optional malware metadata
        :param dict | None endpoint_detection: optional endpoint metadata
        :param dict | None redirect_classification: optional redirect metadata
        :param str | None request_source: logical request source for UI markers
        :param int crawl_enqueued_size: accepted crawl URL count for progress labels
        :param int crawl_processed_size: processed crawl request count for progress labels
        :param int | None base_total_size: original dictionary total for crawl progress labels
        :return: True
        :rtype: bool
        """

        optional_metadata = dict(
            ({'shadow_detection': shadow_detection} if shadow_detection is not None else {}),
            **({'openredirect_detection': openredirect_detection} if openredirect_detection is not None else {}),
            **({'malware_detection': malware_detection} if malware_detection is not None else {}),
            **({'endpoint_detection': endpoint_detection} if endpoint_detection is not None else {}),
            **({'redirect_classification': redirect_classification} if redirect_classification is not None else {})
        )

        progress_metadata = {}
        if request_source is not None:
            progress_metadata['request_source'] = request_source
        if crawl_enqueued_size:
            progress_metadata['crawl_enqueued_size'] = crawl_enqueued_size
        if crawl_processed_size:
            progress_metadata['crawl_processed_size'] = crawl_processed_size
        if base_total_size is not None:
            progress_metadata['base_total_size'] = base_total_size

        self.__debug.debug_request_uri(
            status=status,
            request_uri=request_url,
            redirect_uri=redirect_uri,
            items_size=items_size,
            total_size=total_size,
            content_size=content_size,
            response_code=response_code,
            waf_name=waf_detection.get('name') if waf_detection else None,
            waf_confidence=waf_detection.get('confidence') if waf_detection else None,
            stacktrace_detection=stacktrace_detection,
            secret_detection=secret_detection,
            **progress_metadata,
            **optional_metadata
        )
        getattr(self.__debug, 'debug_classification', lambda *args, **kwargs: True)(
            status=status,
            code=response_code,
            size=content_size,
            waf_name=waf_detection.get('name') if waf_detection else None,
            waf_confidence=waf_detection.get('confidence') if waf_detection else None,
            signals=waf_detection.get('signals') if waf_detection else None,
            redirect_uri=redirect_uri,
            stacktrace_detection=stacktrace_detection,
            secret_detection=secret_detection,
            **optional_metadata
        )

        return True

    def load_sniffers_plugins(self, plugins):
        """

        :param list plugins: response plugins list
        :return:
        """

        for plugin in plugins:
            try:
                plg_object = ResponsePlugin.load(plugin)
                self._response_plugins.append(plg_object)
                if 0 < self.__debug.level:
                    self.__debug.debug_load_sniffer_plugin(plg_object.DESCRIPTION)
            except ResponsePluginError as error:
                raise ResponsePluginError(str(error))

    def _get_subdomain_ips(self, request_url):
        """
        Resolve and cache IP addresses rendered for subdomain scan report items.

        :param str request_url: request URL
        :return: str
        """

        hostname = helper.parse_url(request_url).hostname
        if not hostname:
            return ''

        if not hasattr(self, '_Response__subdomain_ip_cache'):
            self.__subdomain_ip_cache = {}

        hostname = str(hostname).strip().lower()
        if hostname not in self.__subdomain_ip_cache:
            self.__subdomain_ip_cache[hostname] = Socket.get_ips_addresses(hostname)

        return self.__subdomain_ip_cache.get(hostname, '')

    def handle(self, response, request_url, items_size, total_size, ignore_list, emit_debug=True):
        """
        Response handler
        :param urllib3.response.HTTPResponse response: response object
        :param str request_url: url from request
        :param int items_size: current items sizes
        :param int total_size: response object
        :param list ignore_list: ignore list
        :param bool emit_debug: whether runtime/debug output should be emitted
        :raise ResponseError
        :return: tuple
        """

        if hasattr(response, 'status'):
            response.headers.update({'Status': str(response.status)})

            try:
                status = super(Response, self).detect(request_url, response)
                redirect_uri = None
                content_size = ResponseProvider._get_content_size(response)
                response_code = str(response.status)
                waf_detection = self.waf_detection if status == self.DEFAULT_WAF_STATUS else None
                stacktrace_detection = getattr(response, 'opendoor_stacktrace_detection', None) if status == 'stacktrace' else None
                secret_detection = getattr(response, 'opendoor_secret_detection', None) if status == 'secret' else None
                malware_detection = getattr(response, 'opendoor_malware_detection', None) if status == 'malware' else None
                endpoint_detection = getattr(response, 'opendoor_endpoint_detection', None) if status == 'endpoint' else None
                shadow_detection = getattr(response, 'opendoor_shadow_detection', None) if status == 'shadow' else None
                openredirect_detection = getattr(response, 'opendoor_openredirect_detection', None) if status == 'openredirect' else None
                redirect_classification = None

                if status in ['redirect']:
                    redirect_location = RedirectClassifier.get_location(response)
                    redirect_uri = self._get_redirect_url(request_url, response)
                    redirect_classification = RedirectClassifier.classify(request_url, response.status, redirect_location)
                    if redirect_classification:
                        try:
                            setattr(response, 'opendoor_redirect_classification', dict(redirect_classification))
                        except (AttributeError, TypeError):
                            pass
                    check_for_ignored = helper.parse_url(redirect_uri).path[1:]
                    if check_for_ignored in ignore_list:
                        status = 'failed'
                    if self.__config.SUBDOMAINS_SCAN == self.__config.scan:
                        ips = self._get_subdomain_ips(request_url)
                        url = request_url = '{0} {1}'.format(request_url, ips)
                    else:
                        url = redirect_uri
                else:
                    if self.__config.SUBDOMAINS_SCAN == self.__config.scan:
                        ips = self._get_subdomain_ips(request_url)
                        url = request_url = '{0} {1}'.format(request_url, ips)
                    else:
                        url = request_url

                if emit_debug is True:
                    self.__debug_classified_response(
                        status=status,
                        request_url=request_url,
                        redirect_uri=redirect_uri,
                        items_size=items_size,
                        total_size=total_size,
                        content_size=content_size,
                        response_code=response_code,
                        waf_detection=waf_detection,
                        stacktrace_detection=stacktrace_detection,
                        secret_detection=secret_detection,
                        shadow_detection=shadow_detection,
                        openredirect_detection=openredirect_detection,
                        malware_detection=malware_detection,
                        endpoint_detection=endpoint_detection,
                        redirect_classification=redirect_classification,
                    )

                return status, url, content_size, response_code

            except Exception as error:
                raise ResponseError(str(error))

        elif 'subdomains' in self._cfg.scan:
            status = 'failed'
            content_size = ResponseProvider._get_content_size(response)
            self.__debug.debug_request_uri(
                status=status,
                request_uri=request_url,
                items_size=items_size,
                total_size=total_size,
                content_size=content_size,
                response_code='-'
            )
            return status, request_url, content_size, '-'
        else:
            pass
