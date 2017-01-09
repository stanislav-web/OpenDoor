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

from src.core import socket, request, response
from src.core import SocketError
from src.lib.exceptions import LibError
from src.lib import tpl
from src.lib.reader import Reader
from .config import Config
from .debug import Debug
class Browser(Config, Reader, Debug):
    """Browser class"""

    def __init__(self, params):

        try:
            self.debugger = None

            Config.__init__(self, params)
            Reader.__init__(self)
            Debug.__init__(self)


        except LibError as e:
            raise LibError(e)

    def ping(self):
        """ ping host:port for available """

        try:

            socket.ping(self._host, self._port)

            tpl.info(key='online', host=self._host, port=self._port, ip=socket.get_ip_address(self._host))

        except SocketError as e:
            raise LibError(e)

    def _process_directories(self, line):
        """ process with directories list """

        self._debug_line(line)
        pass

    def _process_subdomains(self, line):
        """ process with subdomains list """

        self._debug_line(line)
        pass

    def scan(self):
        """ scan host with params """

        self._debug_user_agents()
        self._debug_proxy()
        self._debug_list()

        tpl.info(key='scanning', host=self._host)

        self._get_list(self._scan,
            params={'host' : self._host, 'port' : self._port, 'scheme' : self._scheme},
            callback= getattr(self, '_process_{0}'.format(self._scan))
        )
        pass

