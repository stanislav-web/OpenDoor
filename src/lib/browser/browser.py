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

from src.core import socket
from src.core import request
from src.core import helper
from src.core import SocketError
from src.lib.exceptions import LibError
from src.lib import tpl
from src.lib.reader import Reader
from .config import Config
from .debug import Debug
from .filter import Filter
from .threadpool import ThreadPool
from .exceptions import ThreadPoolError

class Browser(Debug, Filter, ThreadPool):
    """ Browser class """

    def __init__(self, params):
        """
        Browser constructor

        :param dict params: filtered input params
        :raise LibError
        """

        try:

            self.__config = Config(params)
            self.reader = Reader(browser_config={
                'list'       : self.__config.scan,
                'use_random' : self.__config.is_random_list
            })
            self.reader._count_total_lines(self.__config.scan)

            Debug.__init__(self, self.__config)
            Filter.__init__(self, self.__config)
            ThreadPool.__init__(self, self.__config.threads, self.reader.total_lines)

        except (ThreadPoolError, LibError) as e:
            raise LibError(e)

    def ping(self):
        """
        Check remote host for available

        :raise: LibError
        :return: None
        """

        try:

            socket.ping(self.__config.host, self.__config.port)

            tpl.info(key='online', host=self.__config.host, port=self.__config.port, ip=socket.get_ip_address(self.__config.host))

        except SocketError as e:
            raise LibError(e)

    def scan(self):
        """
        Scanner

        :raise LibError
        :return: None
        """

        self._debug_user_agents()
        self._debug_proxy()
        if True is self.__config.is_random_list:
            self._debug_randomizing_list()
            self.reader._randomize_list(self.__config.scan)
        self._debug_list(total_lines=self.reader.total_lines)
        tpl.info(key='scanning', host=self.__config.host)

        if True is self.is_pool_started:
            self.reader._get_lines(self.__config.scan,
                params={'host' : self.__config.host, 'port' : self.__config.port, 'scheme' : self.__config.scheme},
                loader= getattr(self, '_add_url'.format())
            )

    def __http_request(self, url):
        """
        Make HTTP request

        :param str url: recieved url
        :return:
        """
        import time
        time.sleep(1)

        print request(self.__config)

        exit()
        if 0 < self.__config.debug:
            tpl.line_log(key='get_item_lvl1',
                         percent=tpl.line(msg=helper.percent(self.pool_items_size, self.reader.total_lines), color='cyan'),
                         current=self.pool_items_size,
                         total=self.reader.total_lines,
                         item=url,
                         size='10kb'
                        )
        else:
            tpl.line_log(key='get_item_lvl0',
                         percent=tpl.line(msg=helper.percent(0, self.reader.total_lines), color='cyan'),
                         item=url
                         )


    def _add_url(self, url):
        """
        Url handler
        :param str url
        :return: None
        """
        if True is self.is_pool_started:
            self.add(self.__http_request, url)

