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

    Development: Stanislav WEB
"""

import socket
from .exceptions import SocketError


class Socket(object):

    """Socket class"""

    @staticmethod
    def _resolve_connect_addresses(host, port):
        """
        Resolve TCP connect candidates for diagnostics.

        :param str host: target host
        :param int port: target port
        :return: unique address list
        """

        try:
            addr_info = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except (socket.gaierror, socket.error, TypeError, ValueError):
            return []

        addresses = []
        for item in addr_info:
            try:
                address = item[4][0]
            except (IndexError, TypeError):
                continue

            if address not in addresses:
                addresses.append(address)

        return addresses

    @staticmethod
    def _format_connect_addresses(addresses):
        """
        Format resolved addresses for error output.

        :param list addresses: resolved addresses
        :return: printable address list
        """

        if not addresses:
            return 'unresolved'

        return ', '.join([str(address) for address in addresses])

    @classmethod
    def _format_connect_error(cls, host, port, timeout, error):
        """
        Build an actionable preflight connection error.

        :param str host: target host
        :param int port: target port
        :param int|float timeout: connection timeout
        :param Exception error: original socket error
        :return: formatted error message
        """

        addresses = cls._format_connect_addresses(cls._resolve_connect_addresses(host, port))
        return (
            'Unable to connect to {host}:{port} within {timeout}s. '
            'Resolved addresses: {addresses}. Socket error: {error}'
        ).format(host=host, port=port, timeout=timeout, addresses=addresses, error=error)

    @staticmethod
    def ping(host, port, timeout=10):
        """
        Ping remote host.

        Uses socket.create_connection() instead of a raw AF_INET socket so
        localhost and dual-stack targets work with both IPv4 and IPv6 bindings.

        :param str host: target host
        :param int port: target port
        :param int timeout: connection timeout
        :raise SocketError
        :return: None
        """

        sock = None

        try:
            sock = socket.create_connection((host, int(port)), timeout=timeout)
        except (socket.gaierror, socket.error, socket.timeout, OSError, ValueError) as error:
            raise SocketError(Socket._format_connect_error(host, port, timeout, error))
        finally:
            if sock is not None:
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

    @staticmethod
    def get_ips_addresses(host):
        """
        Get remote ip addresses
        :param str host: target host
        :return: list
        """

        try:
            _, _, ips_list = socket.gethostbyname_ex(host)
            if not ips_list:
                ips = ''
            else:
                ips = '['+', '.join(ips_list) +']'
        except socket.gaierror:
            ips = ''
        return ips
