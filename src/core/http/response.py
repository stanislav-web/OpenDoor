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

        if True is self.__config.is_sniff:
            try:
                self.load_sniffers_plugins(self.__config.sniffers)
            except ResponsePluginError as error:
                raise ResponseError(str(error))

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

    def handle(self, response, request_url, items_size, total_size, ignore_list):
        """
        Response handler
        :param urllib3.response.HTTPResponse response: response object
        :param str request_url: url from request
        :param int items_size: current items sizes
        :param int total_size: response object
        :param list ignore_list: ignore list
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

                if status in ['redirect']:
                    redirect_uri = self._get_redirect_url(request_url, response)
                    check_for_ignored = helper.parse_url(redirect_uri).path[1:]
                    if check_for_ignored in ignore_list:
                        status = 'failed'
                    if self.__config.SUBDOMAINS_SCAN == self.__config.scan:
                        ips = Socket.get_ips_addresses(helper.parse_url(request_url).hostname)
                        url = request_url = '{0} {1}'.format(request_url, ips)
                    else:
                        url = redirect_uri
                else:
                    if self.__config.SUBDOMAINS_SCAN == self.__config.scan:
                        ips = Socket.get_ips_addresses(helper.parse_url(request_url).hostname)
                        url = request_url = '{0} {1}'.format(request_url, ips)
                    else:
                        url = request_url

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
                )
                getattr(self.__debug, 'debug_classification', lambda *args, **kwargs: True)(
                    status=status,
                    code=response_code,
                    size=content_size,
                    waf_name=waf_detection.get('name') if waf_detection else None,
                    waf_confidence=waf_detection.get('confidence') if waf_detection else None,
                    signals=waf_detection.get('signals') if waf_detection else None,
                    redirect_uri=redirect_uri
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