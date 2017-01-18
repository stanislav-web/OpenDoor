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

from src.core import HttpRequestError, HttpsRequestError, ProxyRequestError
from src.core import SocketError
from src.core import helper
from src.core import request_http
from src.core import request_proxy
from src.core import request_ssl
from src.core import socket
from src.lib.reader import Reader
from src.lib.reader import ReaderError
from src.lib.tpl import Tpl as tpl
from .config import Config
from .debug import Debug
from .exceptions import BrowserError
from .exceptions import ThreadPoolError
from .filter import Filter
from .threadpool import ThreadPool


class Browser(Debug, Filter):
    """ Browser class """

    __client = None
    __config = None
    __reader = None
    __pool = None

    def __init__(self, params):
        """
        Browser constructor
        :param dict params: filtered input params
        :raise BrowserError
        """

        try:

            self.__config = Config(params)

            self.__reader = Reader(
                browser_config={'list': self.__config.scan, 'use_random': self.__config.is_random_list})
            self.__reader._count_total_lines(self.__config.scan)
            Debug.__init__(self, self.__config)
            Filter.__init__(self, self.__config, self.__reader.total_lines)

            self.__pool = ThreadPool(self.__config.threads, self.__reader.total_lines)

        except (ThreadPoolError, ReaderError) as e:
            raise BrowserError(e)

    def ping(self):
        """
        Check remote host for available
        :raise: BrowserError
        :return: None
        """

        try:
            if 0 < self.__config.debug:
                tpl.debug(key='checking_connect', host=self.__config.host, port=self.__config.port)
            socket.ping(self.__config.host, self.__config.port, self.__config.DEFAULT_SOCKET_TIMEOUT)
            tpl.info(key='online', host=self.__config.host, port=self.__config.port,
                     ip=socket.get_ip_address(self.__config.host))

        except SocketError as e:
            raise BrowserError(e)

    def scan(self):
        """
        Scanner
        :raise BrowserError
        :return: None
        """

        self._debug_user_agents()
        self._debug_proxy()
        if True is self.__config.is_random_list:
            self._debug_randomizing_list()
            self.__reader._randomize_list(self.__config.scan)
        self._debug_list(total_lines=self.__reader.total_lines)
        tpl.info(key='scanning', host=self.__config.host)

        try:  # beginning scan process

            if True is self.__config.is_proxy:
                self.__client = request_proxy(self.__config, proxy_list=self.__reader.get_proxies(),
                                              debug=self.__config.debug, tpl=tpl)
            else:

                if True is self.__config.ssl:
                    self.__client = request_ssl(self.__config, debug=self.__config.debug, tpl=tpl)
                else:
                    self.__client = request_http(self.__config, debug=self.__config.debug, tpl=tpl)

            if True is self.__pool.is_started:
                self.__reader.get_lines(self.__config.scan,
                                        params={'host': self.__config.host, 'port': self.__config.port,
                                                'scheme': self.__config.scheme},
                                        loader=getattr(self, '_add_url'.format()))
        except (HttpRequestError, HttpsRequestError, ProxyRequestError) as e:
            raise BrowserError(e)

    def __http_request(self, url):
        """
        Make HTTP request
        :param str url: recieved url
        :return: None
        """

        self.__client.request(url)

        if 0 < self.__config.debug:
            tpl.line_log(key='get_item_lvl1',
                         percent=tpl.line(msg=helper.percent(self.__pool.size, self.__reader.total_lines),
                                          color='cyan'), current=self.__pool.size, total=self.__reader.total_lines,
                         item=url, size='10kb')
        else:
            tpl.line_log(key='get_item_lvl0',
                         percent=tpl.line(msg=helper.percent(0, self.__reader.total_lines), color='cyan'), item=url)

    def _add_url(self, url):
        """
        Add recieved url to threadpool
        :param str url
        :raise KeyboardInterrupt
        :return: None
        """

        try:
            self.__pool.add(self.__http_request, url)
        except (SystemExit, KeyboardInterrupt):
            raise KeyboardInterrupt
