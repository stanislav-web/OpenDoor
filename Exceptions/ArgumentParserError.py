# -*- coding: utf-8 -*-
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
