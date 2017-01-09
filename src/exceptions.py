# -*- coding: utf-8 -*-

"""SrcError classes"""

class SrcError(Exception):
    """SrcError class"""

    def __init__(self, message):
        super(SrcError, self).__init__(message)
