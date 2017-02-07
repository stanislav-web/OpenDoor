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
from src.core import sys
from src.core.http.providers.debug import DebugProvider
from src.lib.tpl import Tpl as tpl


class Debug(DebugProvider):
    """Debug class"""

    def __init__(self, Config):
        """
        Debug constructor
        :param Config: Config
        """

        self.__catched = False
        self.__clear = False
        self.__cfg = Config
        self.__level = self.__cfg.debug

        if 0 < self.__level:
            tpl.debug(key='debug', level=self.__cfg.debug, method=self.__cfg.method)
            if True is self.__cfg.is_indexof:
                tpl.debug(key='indexof_act', method=self.__cfg.method)

    @property
    def level(self):
        """
        Get debug level
        :return: int
        """

        return self.__level

    def debug_user_agents(self):
        """
        Debug info for user agent
        :return: None
        """

        if 0 < self.__level:
            if True is self.__cfg.is_random_user_agent:
                tpl.debug(key='random_browser')
            else:
                tpl.debug(key='browser', browser=self.__cfg.user_agent)

    def debug_list(self, total_lines):
        """
        Debug scan list
        :param int total_lines: list lines
        :return: None
        """

        if True is self.__cfg.is_random_list:
            tpl.debug(key='randomizing')

        if 0 < self.__level:
            if self.__cfg.DEFAULT_SCAN is self.__cfg.scan:
                tpl.debug(key='directories', total=total_lines)
            else:
                tpl.debug(key='subdomains', total=total_lines)
            tpl.debug(key='create_queue', threads=self.__cfg.threads)

    def debug_connection_pool(self, keymsg, pool):
        """
        Debug connection pool message
        :param str keymsg: tpl key
        :param object pool: pool object
        :return: None
        """

        tpl.debug(key=keymsg)
        if pool:
            tpl.debug(str(pool))

    def debug_proxy_pool(self):
        """
        Debug proxy pool message
        :return: None
        """

        if True is self.__cfg.is_external_torlist:
            tpl.debug(key='proxy_pool_external_start')

        elif True is self.__cfg.is_standalone_proxy:
            tpl.debug(key='proxy_pool_standalone', server=self.__cfg.proxy)

        elif True is self.__cfg.is_internal_torlist:
            tpl.debug(key='proxy_pool_internal_start')

    def debug_request(self, request_header, url, method):
        """
        Debug request
        :param dict request_header: request header
        :param str url: request url
        :param str method: request method
        :return: None
        """

        request_header.update({'Request URI': url})
        request_header.update({'Request Method': method})

        tpl.debug(key='request_header_dbg', dbg=helper.to_json(request_header))

    def debug_response(self, response_header):
        """
        Debug response
        :param dict response_header: response header
        :return: bool
        """

        tpl.debug(key='response_header_dbg', dbg=helper.to_json(response_header))

        return True

    def debug_request_uri(self, status, request_uri, **kwargs):
        """
        Debug request_uri
        :param int status: response status
        :param str request_uri: http request uri
        :param **kwargs:
        :return: bool
        """

        percentage = tpl.line(
            msg=helper.percent(kwargs.get('items_size', 0), kwargs.get('total_size', 1)),
            color='cyan')

        if status in ['success']:
            request_uri = tpl.line(key='success', color='green', url=helper.parse_url(request_uri).path)
        elif status in ['file']:
            request_uri = tpl.line(key='file', color='green', url=helper.parse_url(request_uri).path)
        elif status in ['bad', 'forbidden']:
            request_uri = tpl.line(key='forbidden', color='yellow', url=helper.parse_url(request_uri).path)
        elif status in ['redirect']:
            request_uri = tpl.line(key='redirect', color='blue', url=helper.parse_url(request_uri).path,
                                   rurl=kwargs.get('redirect_uri'))

        self.__clear = True if self.__catched else False

        if 0 < self.__level:

            if status in ['success', 'bad', 'forbidden', 'redirect']:

                tpl.info(key='get_item_lvl1',
                         clear=self.__clear,
                         percent=percentage,
                         current=kwargs.get('items_size', 0),
                         total=kwargs.get('total_size', 1),
                         item=request_uri,
                         size=kwargs.get('content_size')
                         )
                self.__catched = True
            else:
                tpl.line_log(key='get_item_lvl1', percent=percentage, current=kwargs.get('items_size', 0),
                             total=kwargs.get('total_size', 1), item=request_uri, size=kwargs.get('content_size'))
                self.__catched = False
                sys.writels("", flush=self.__catched)

        else:
            if status in ['success', 'bad', 'forbidden', 'redirect']:
                tpl.info(key='get_item_lvl0', clear=self.__clear, percent=percentage, item=request_uri)
            else:
                tpl.line_log(key='get_item_lvl0', percent=percentage, item=request_uri)

        return True
