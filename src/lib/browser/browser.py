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

    Development Team: Stanislav Menshov
"""

from src.core import socket
from src.core import helper
from src.core import SocketError
from src.lib.exceptions import LibError
from src.lib import tpl
from src.lib.reader import Reader
from .config import Config
from .debug import Debug
from .threadpool import ThreadPool
from .exceptions import ThreadPoolError

class Browser(Config, Debug):
    """ Browser class """

    def __init__(self, params):
        """
        Browser constructor

        :param dict params: filtered input params
        :raise LibError
        """

        try:

            Config.__init__(self, params)
            Debug.__init__(self)

            self.threadpool = ThreadPool(self._threads)
            self.reader = Reader(browser_config={
                'list'       : self._scan,
                'use_random' : self._is_random_list,
                'threadpool' : self.threadpool.get_queue_instance
            })

        except (ThreadPoolError, LibError) as e:
            raise LibError(e)

    def ping(self):
        """
        Check remote host for available

        :raise: LibError
        :return: None
        """

        try:

            socket.ping(self._host, self._port)

            tpl.info(key='online', host=self._host, port=self._port, ip=socket.get_ip_address(self._host))

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
        if True is self._is_random_list:
            self._debug_randomizing_list()
            self.reader._randomize_list(self._scan)
        self._debug_list(total_lines=self.reader._count_total_lines(self._scan))
        tpl.info(key='scanning', host=self._host)

        self.reader._get_lines(self._scan,
            params={'host' : self._host, 'port' : self._port, 'scheme' : self._scheme},
            loader= getattr(self, '_get_url'.format())
        )

    def __http_request(self, url):
        """
        Make HTTP request

        :param str url: recieved url
        :return:
        """

        import time
        time.sleep(1)

        if 0 < self._debug:

            tpl.info(key='get_item_lvl1',
                         percent=tpl.line(msg=helper.percent(0, self.reader.total_lines), color='cyan'),
                         current=self.threadpool.get_pool_items_size,
                         total=self.reader.total_lines,
                         item=url,
                         size='10kb'
                        )
        else:
            tpl.info(key='get_item_lvl0',
                         percent=tpl.line(msg=helper.percent(0, self.reader.total_lines), color='cyan'),
                         item=url
                         )


    def _get_url(self, url):
        """
        Url handler

        :return: None
        """

        self.threadpool.add(self.__http_request, url)

