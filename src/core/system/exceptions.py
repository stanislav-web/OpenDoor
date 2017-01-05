# -*- coding: utf-8 -*-

"""SystemError class"""


class SystemError(Exception):
    """SystemError class"""

    def __init__(self, message):
        super(SystemError, self).__init__(message)
