# -*- coding: utf-8 -*-

"""SocketError class"""


class SocketError(Exception):
    """SocketError class"""

    def __init__(self, message):
        super(SocketError, self).__init__(message)

class RequestError(Exception):
    """RequestError class"""

    def __init__(self, message):
        super(RequestError, self).__init__(message)

class ResponseError(Exception):
    """ResponseError class"""

    def __init__(self, message):
        super(ResponseError, self).__init__(message)

