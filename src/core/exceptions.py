# -*- coding: utf-8 -*-

"""CoreError class"""

class CoreError(Exception):
    """CoreError class"""

    def __init__(self, message, errors):
        super(CoreError, self).__init__(message)
        self.errors = errors