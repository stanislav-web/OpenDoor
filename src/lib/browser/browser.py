# -*- coding: utf-8 -*-

"""Browser class"""
from src.core import socket,request,response
from src.core import SocketError
from ...lib.exceptions import LibError

class Browser:
    """Browser class"""

    @staticmethod
    def ping(host, port):
        """ ping host:port for available """
        try:
            socket.ping(host, port)
        except SocketError as e:
            raise LibError(e)

