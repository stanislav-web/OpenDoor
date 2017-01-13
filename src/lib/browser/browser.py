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
from src.core import process
from src.core import SocketError
from src.lib.exceptions import LibError
from src.lib import tpl
from src.lib.reader import Reader
from .config import Config
from .debug import Debug
from .pool import Pool

class Browser(Config, Reader, Debug, Pool):
    """ Browser class """

    def __init__(self, params):
        """
        Browser constructor

        :param dict params: filtered input params
        :raise LibError
        """

        try:

            Config.__init__(self, params)
            Pool.__init__(self, params.get('threads'))
            Reader.__init__(self, self.get_pool_instance(), browser_config={
                'use_random' : self._is_random_list
            })
            Debug.__init__(self)


        except LibError as e:
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
            self._randomize_list(self._scan)
        self._debug_list()

        self._get_lines(self._scan,
            params={'host' : self._host, 'port' : self._port, 'scheme' : self._scheme},
            callback= getattr(self, '_create_pool'.format())
        )

        pass

    def _create_pool(self):
        """
        Create items pool

        :return: None
        """

        if self._total_lines() == self.count_in_queue():
            tpl.info(key='scanning', host=self._host)
            #self.read_from_queue(self.__load)
        else:
            self._debug_progress(self.count_in_queue(), self._total_lines())
            pass

    def __load(self, threadno, url):
        """
        Process adding items into queue pool

        :return: None
        """
        if False == self.is_pooled(threadno):
            tpl.line_log("{0} - {1}".format(threadno, url))
        else:
            tpl.message("\n")
            tpl.info("{0} - {1}".format(threadno, url))
