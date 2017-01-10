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

import socket

from .exceptions import SocketError
from .config import SocketConfig as config

class Socket:
    """Socket class"""

    @staticmethod
    def ping(host, port):
        """
        Ping remote host

        :param str host: target  host
        :param int port: target port
        :raise SocketError
        :return: None
        """
        sock = socket.socket()

        try:

            sock.settimeout(config.timeout)
            sock.connect((host, port))

        except (socket.gaierror, socket.timeout, SocketError) as e:
            raise SocketError(e)
        finally:
            sock.close()

    @staticmethod
    def get_ip_address(host):
        """
        Get remote ip address

        :param str host: target  host
        :raise SocketError
        :return: str
        """

        try:
            ip = socket.gethostbyname(host)
            return ip
        except socket.gaierror as e:
            raise SocketError(e.message)