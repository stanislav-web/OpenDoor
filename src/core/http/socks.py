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

import socket

from .exceptions import SocketError


class Socket(object):

    """Socket class"""

    @staticmethod
    def ping(host, port, timeout=10):
        """
        Ping remote host
        :param str host: target  host
        :param int port: target port
        :param int timeout: connection timeout
        :raise SocketError
        :return: None
        """

        sock = socket.socket()

        try:

            sock.settimeout(timeout)
            sock.connect((host, port))

        except (socket.gaierror, socket.error, socket.timeout, SocketError) as error:
            raise SocketError(error)
        finally:
            sock.close()

    @staticmethod
    def get_ip_address(host):
        """
        Get remote ip address
        :param str host: target host
        :raise SocketError
        :return: str
        """

        try:
            ip_address = socket.gethostbyname(host)
            return ip_address
        except socket.gaierror as error:
            raise SocketError(str(error))
