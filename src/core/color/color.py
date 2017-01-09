# -*- coding: utf-8 -*-

"""Color class"""
import sys
from .config import Config

class Color:
    """Color class"""

    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    has = False

    @staticmethod
    def has_colors(stream):
        if not hasattr(stream, "isatty"):
            return False
        if not stream.isatty():
            return False  # auto color only on TTYs
        try:
            import curses
            curses.setupterm()
            return curses.tigetnum("colors") > 2
        except:
            # guess false in case of error
            return False

    @staticmethod
    def colored(text, color):

        if type(text) is not str:
            text = str(text)
        if Color.has_colors(sys.stdout):
            text = text.strip('\n')
            seq = "\x1b[%dm" % (30 + Config.get(color)) + text + "\x1b[0m"
            return seq
        else:
            return text
