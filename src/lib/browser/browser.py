# -*- coding: utf-8 -*-

"""Browser class"""

from src.core import socket, request, response
from src.core import SocketError
from src.lib.exceptions import LibError
from src.lib import tpl
from src.lib.reader import Reader
from .config import Config
class Browser(Config, Reader):
    """Browser class"""

    def __init__(self, params):

        try:

            Config.__init__(self, params)
            Reader.__init__(self)


        except LibError as e:
            raise LibError(e)

    def ping(self):
        """ ping host:port for available """

        try:

            socket.ping(self._host, self._port)

            tpl.info(key='online', host=self._host, port=self._port, ip=socket.get_ip_address(self._host))
            tpl.info(key='scanning', host=self._host)

        except SocketError as e:
            raise LibError(e)

    def scan(self):

        """ scan host with params """

        print self._scan
        print self._host
        print self._port
        print self._method
        print self._threads
        print self._delay
        print self._timeout
        print self._debug
        print self._is_proxy
        print self._is_indexof
        print self._is_random_user_agent
        pass

