# -*- coding: utf-8 -*-

"""FileSystemError class"""

class FileSystemError(Exception):
    """FileSystemError class"""

    def __init__(self, message, errors):
        super(FileSystemError, self).__init__(message)
        self.errors = errors