# -*- coding: utf-8 -*-

"""Socket class"""

import socket

from .exceptions import SocketError
from .config import SocketConfig as config

class Socket:
    """Socket class"""

    @staticmethod
    def ping(host, port):

        sock = socket.socket()

        try:

            sock.settimeout(config.get('timeout'))
            sock.connect((host, port))

        except (socket.gaierror, socket.timeout, SocketError) as e:
            raise SocketError(e)
        finally:
            sock.close()

    @staticmethod
    def get_ip_address(host):
        """ get ip address """

        try:
            ip = socket.gethostbyname(host)
            return ip
        except socket.gaierror as e:
            raise SocketError(e.message)