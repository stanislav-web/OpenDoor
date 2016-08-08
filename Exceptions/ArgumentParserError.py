from argparse import ArgumentParser

class ArgumentParserError(Exception):
    """ArgumentParserError class"""
    pass

class ThrowingArgumentParser(ArgumentParser):
    """ThrowingArgumentParser class"""

    @staticmethod
    def error(message):
        raise ArgumentParserError(message)
