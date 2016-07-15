from argparse import ArgumentParser

class ArgumentParserError(Exception): pass

class ThrowingArgumentParser(ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)
