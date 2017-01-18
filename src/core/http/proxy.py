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

import random
from urllib3 import ProxyManager
from .exceptions import ProxyRequestError

try :
    from urllib3.contrib.socks import SOCKSProxyManager
except ImportError as e:
    raise ProxyRequestError(e.message)

class Proxy():
    """Proxy class"""

    __debug = False
    __cfg = False
    __pool = None
    __list = None

    def __init__(self, config, debug=0, **kwargs):
        """
        Proxy instance
        :param src.lib.browser.config.Config config:
        :param int debug: debug flag
        :raise ProxyRequestError
        """

        try:
            self.__tpl = kwargs.get('tpl')
            self.__list = kwargs.get('proxy_list')

            if type(self.__list) is not list or 0 == len(self.__list):
                raise TypeError('Proxy list empty or has invalid format')

        except (TypeError,ValueError) as e:
            raise ProxyRequestError(e.message)

        self.__list = kwargs.get('proxy_list')

        self.__cfg = config
        self.__debug = False if debug < 2 else True
        self.__pool = self.__proxy_pool()

    def __proxy_pool(self):
        """
        Create Proxy connection pool
        :raise ProxyRequestError
        :return: urllib3.HTTPConnectionPool
        """

        try:

            if True is self.__debug:
                self.__tpl.debug(key='proxy_pool_start')

            server = self.__get_random_server()
            if self.__get_proxy_type(server) == 'socks':
                pool = SOCKSProxyManager(server, num_pools=self.__cfg.threads,
                                    timeout=self.__cfg.timeout, block=True)
            else:
                pool = ProxyManager(server, num_pools=self.__cfg.threads,
                                timeout=self.__cfg.timeout, block=True)
            return pool
        except Exception as e:
            raise ProxyRequestError(e)



    def __get_random_server(self):
        """
        Get random server from proxy list
        :return: str
        """

        index = random.randrange(0, len(self.__list))
        server = self.__list[index].strip()

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
