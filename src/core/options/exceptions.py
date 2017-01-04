# -*- coding: utf-8 -*-

"""ArgumentParserError class"""

from argparse import ArgumentParser


class ArgumentParserError(Exception):
    """ArgumentParserError class"""
    pass


class ThrowingArgumentParser(ArgumentParser):
    """ThrowingArgumentParser class"""

    @staticmethod
    def error(message):
        """Error raiser"""

        raise ArgumentParserError(message)


class OptionsError(Exception):
    """OptionsError class"""

    def __init__(self, message, errors):
        super(OptionsError, self).__init__(message)
        self.errors = errors

class FilterError(Exception):
    """FilterError class"""

    def __init__(self, message, errors):
        super(FilterError, self).__init__(message)
        self.errors = errors