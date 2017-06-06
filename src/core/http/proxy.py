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

import importlib
import random

from urllib3 import ProxyManager, disable_warnings
from urllib3.exceptions import DependencyWarning, MaxRetryError, ProxySchemeUnknown,\
    ReadTimeoutError, InsecureRequestWarning

from src.core import helper
from .exceptions import ProxyRequestError
from .providers import DebugProvider
from .providers import RequestProvider


class Proxy(RequestProvider, DebugProvider):

    """Proxy class"""

    def __init__(self, config, debug, **kwargs):
        """
        Proxy instance
        :param src.lib.browser.config.Config config: global configurations
        :param DebugProvider debug: debugger
        """

        try:
            self.__tpl = kwargs.get('tpl')
            self.__proxylist = kwargs.get('proxy_list')
            RequestProvider.__init__(self, config, agent_list=kwargs.get('agent_list'))

            self.__server = None
            self.__pm = None
            self.__cfg = config
            self.__debug = debug
            self.__debug.debug_proxy_pool()

            if False is config.is_standalone_proxy and 0 == len(self.__proxylist):
                raise TypeError('Proxy list empty or has invalid format')

        except (TypeError, ValueError) as error:
            raise ProxyRequestError(error)

    def __proxy_pool(self):
        """
        Create Proxy connection pool
        :raise ProxyRequestError
        :return: urllib3.HTTPConnectionPool
        """

        try:

            self.__server = self.__cfg.proxy if True is self.__cfg.is_standalone_proxy else self.__get_random_proxy()

            if self.__get_proxy_type(self.__server) == 'socks':

                disable_warnings(InsecureRequestWarning)

                if not hasattr(self, '__pm'):

                    package_module = importlib.import_module('urllib3.contrib.socks')
                    self.__pm = getattr(package_module, 'SOCKSProxyManager')

                pool = self.__pm(self.__server, num_pools=self.__cfg.threads, timeout=self.__cfg.timeout, block=True)
            else:
                pool = ProxyManager(self.__server, num_pools=self.__cfg.threads, timeout=self.__cfg.timeout, block=True)
            return pool
        except (DependencyWarning, ProxySchemeUnknown, ImportError) as error:
            raise ProxyRequestError(error)

    def request(self, url):
        """
        Client request using Proxy
        :param str url: request uri
        :return: urllib3.HTTPResponse
        """

        if self._HTTP_DBG_LEVEL <= self.__debug.level:
            self.__debug.debug_request(self._headers, url, self.__cfg.method)

        try:
            response = self.__pool_request(url)
            return response

        except MaxRetryError:
            if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:
                self.__tpl.warning(key='proxy_max_retry_error', url=helper.parse_url(url).path, proxy=self.__server)
                # Retrying request
                return self.__pool_request(url)

        except ReadTimeoutError:
            if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:
                self.__tpl.warning(key='read_timeout_error', url=helper.parse_url(url).path)

    def __pool_request(self, url):
        """
        Shadow pool request
        :param string url: target url
        :return: urllib3.HTTPResponse
        """

        pool = self.__proxy_pool()
        response = pool.request(self.__cfg.method, url, headers=self._headers, retries=self.__cfg.retries,
                                redirect=False)

        self.cookies_middleware(is_accept=self.__cfg.accept_cookies, response=response)

        return response

    def __get_random_proxy(self):
        """
        Get random server from proxy list
        :return: str
        """

        index = random.randrange(0, len(self.__proxylist))
        server = self.__proxylist[index].strip()
        return server

    @classmethod
    def __get_proxy_type(cls, server):
        """
        Set proxy type
        :param str server: input proxy server
        :return: str
        """

        if 'socks' in server:
            return 'socks'
        elif 'https' in server:
            return 'https'
        else:
            return 'http'
