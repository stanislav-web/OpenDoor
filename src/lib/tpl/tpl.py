# -*- coding: utf-8 -*-

"""Tpl class"""

from src.core import logger
from src.core import colour
from src.core import sys
from .config import Config
from .exceptions import TplError

class Tpl(sys, colour):
    """Tpl class"""

    def __init__(self, modulename=None):
        """ init module name """

        if None is not modulename:
            self.logger = logger.set(modulename)
            self.modulename = modulename

    @staticmethod
    def inline(string, args={} , color=colour.WHITE):
        """ stored colored message """

        return colour.colored(string.format(args), color=color)

    def message(self, string, args={} , color=colour.WHITE):
        """ colored message """

        self.writeln(colour.colored(string.format(args), color=color))


    def log(self, option, args={}):
        """ apply option to log message """

        try:
            tpl = getattr(Config, self.modulename)
            if option not in tpl:
                raise TplError('Could not find tpl option `{0}`'.format(option))
            message = tpl[option]
        except (AttributeError , TplError):
            message = option

        return self.logger

    def __log(self, message, args={}):
        """ apply arguments to tpl """
        return self.logger
        if not len(args):
            self.logger.info(message)
        else:
            self.logger.info(message, args)
