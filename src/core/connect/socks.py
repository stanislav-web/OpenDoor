# -*- coding: utf-8 -*-

"""Socket class"""

import socket

from .exceptions import SocketError

class Socket:
    """Socket class"""

    @staticmethod
    def get_ip_address(host):
        """ get ip address """

        try:
            ip = socket.gethostbyname(host)
            return ip
        except socket.gaierror as e:
            raise SocketError(e.message)