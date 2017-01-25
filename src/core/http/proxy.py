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

from urllib3 import ProxyManager, PoolManager
from urllib3.exceptions import DependencyWarning, MaxRetryError, ProxySchemeUnknown, ReadTimeoutError

from src.core import helper
from .exceptions import ProxyRequestError
from .providers import RequestProvider
from .providers import DebugProvider

class Proxy(RequestProvider, DebugProvider):
    """Proxy class"""

    def __init__(self, config, debug, **kwargs):
        """
        Proxy instance
        :param src.lib.browser.config.Config config:
        :param DebugProvider debug:
        :raise ProxyRequestError
        """

        try:
            self.__tpl = kwargs.get('tpl')
            self.__proxylist = kwargs.get('proxy_list')
            RequestProvider.__init__(self, config, agent_list=kwargs.get('agent_list'))

            self.__cfg = config
            self.__debug = debug
            self.__debug.debug_proxy_pool()

            if False is config.is_standalone_proxy and 0 == len(self.__proxylist):
               raise TypeError('Proxy list empty or has invalid format')

        except (TypeError, ValueError) as e:
            raise ProxyRequestError(e.message)

    def __proxy_pool(self):
        """
        Create Proxy connection pool
        :raise ProxyRequestError
        :return: urllib3.HTTPConnectionPool
        """

        try:

            self.__server = self.__cfg.proxy if True is self.__cfg.is_standalone_proxy else self.__get_random_proxyserver()

            if self.__get_proxy_type(self.__server) == 'socks':

                if not hasattr(self, '__pm'):

                    module = importlib.import_module('urllib3.contrib.socks')
                    self.__pm = getattr(module, 'SOCKSProxyManager')

                pool = self.__pm(self.__server, num_pools=self.__cfg.threads, timeout=self.__cfg.timeout, block=True)
            else:
                pool = ProxyManager(self.__server, num_pools=self.__cfg.threads, timeout=self.__cfg.timeout, block=True)
            return pool
        except (DependencyWarning, ProxySchemeUnknown, ImportError) as e:
            raise ProxyRequestError(e)

    def request(self, url):
        """
        Client request using Proxy
        :param str url: request uri
        :return: urllib3.HTTPResponse
        """

        pool = self.__proxy_pool()

        if self._HTTP_DBG_LEVEL <= self.__debug.level:
            self.__debug.debug_request(self._headers)

        try:
            response = pool.request(self.__cfg.method, url, headers=self._headers, retries=self.__cfg.retries,
                                    redirect=False)

            self.cookies_middleware(is_accept=self.__cfg.accept_cookies, response=response)

            return response

        except MaxRetryError:
            if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:
                self.__tpl.warning(key='proxy_max_retry_error', url=helper.parse_url(url).path, proxy=self.__server)
            pass
        except ReadTimeoutError:
            if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:
                self.__tpl.warning(key='read_timeout_error', url=helper.parse_url(url).path)
            pass

    def __get_random_proxyserver(self):
        """
        Get random server from proxy list
        :return: str
        """

        index = random.randrange(0, len(self.__proxylist))
        server = self.__proxylist[index].strip()

        return server

    def __get_proxy_type(self, server):
        """
        Set proxy type
        :param str server:
        :return: str
        """

        if 'socks' in server:
            return 'socks'
        elif 'https' in server:
            return 'https'
        else:
            return 'http'
