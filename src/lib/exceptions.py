# -*- coding: utf-8 -*-

"""LibError class"""

class LibError(Exception):
    """LibError class"""

    def __init__(self, message, errors):
        super(LibError, self).__init__(message)
        self.errors = errors