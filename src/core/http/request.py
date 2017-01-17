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

import urllib3
import socket

from .exceptions import RequestError

class RequestPool(type):
    """RequestPool class"""

    @property
    def _pool(cls, *args, **kargs):
        if getattr(cls, '_request', None) is None:
            socket_options = urllib3.connection.HTTPConnection.default_socket_options + [
                (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1), ]
            cls._request = urllib3.connection_from_url('http://google.com/', socket_options=socket_options)
        return cls._request

class Request(object):
    """Request class"""

    def __int__(self, config):

        print config
        exit()
        self.__metaclass__._pool(config)
        pass
