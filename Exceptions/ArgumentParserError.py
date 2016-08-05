from argparse import ArgumentParser

class ArgumentParserError(Exception):
    """ArgumentParserError class"""
    pass

class ThrowingArgumentParser(ArgumentParser):
    """ThrowingArgumentParser class"""

    def error(self, message):
        raise ArgumentParserError(message)
