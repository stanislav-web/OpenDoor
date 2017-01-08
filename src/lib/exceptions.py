# -*- coding: utf-8 -*-

"""LibError class"""

from src.core import exception

class LibError(Exception):
    """LibError class"""

    def __init__(self, message):

        class_name = type(message).__name__

        exception.log(class_name=class_name, message=message)

        super(LibError, self).__init__(message)
