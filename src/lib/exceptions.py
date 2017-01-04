# -*- coding: utf-8 -*-

"""LibError class"""

class LibError(Exception):
    """LibError class"""

    def __init__(self, message):
        super(LibError, self).__init__(message)
