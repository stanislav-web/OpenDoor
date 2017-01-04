# -*- coding: utf-8 -*-

"""Tpl class"""

from .exceptions import TplError
from .config import Config


class Tpl:
    """Tpl class"""

    def __init__(self, modulename):
        """ init module name """

        self.modulename = modulename

    def string(self, option, **args):
        """ apply tpl to string """

        if None is Config.template[self.modulename]:
            raise TplError('Could not find tpl module `{0}`'.format(self.modulename))

        tpl = Config.template[self.modulename]

        if None is tpl[option]:
            raise TplError('Could not find tpl option `{0}`'.format(option))

        return self._log(option=option, args=args)

    def _log(self, option, args):
        """ apply arguments to tpl """

        pass

