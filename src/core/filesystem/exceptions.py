# -*- coding: utf-8 -*-

"""FileSystemError class"""


class FileSystemError(Exception):
    """FileSystemError class"""

    def __init__(self, message):
        super(FileSystemError, self).__init__(message)
