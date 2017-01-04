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

    def __init__(self, message):
        super(OptionsError, self).__init__(message)

class FilterError(Exception):
    """FilterError class"""

    def __init__(self, message):
        super(FilterError, self).__init__(message)
