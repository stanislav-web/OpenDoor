# -*- coding: utf-8 -*-

"""TplErrors classes"""

class TplError(Exception):
    """TplError class"""

    def __init__(self, message, errors):
        super(TplError, self).__init__(message)
        self.errors = errors

class ColorError(Exception):
    """ColorError class"""

    def __init__(self, message, errors):
        super(ColorError, self).__init__(message)
        self.errors = errors