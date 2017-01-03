"""HttpError class"""

# -*- coding: utf-8 -*-
class HttpError(Exception):
    """HttpError class"""

    def __init__(self, arg):
        self.msg = arg