# -*- coding: utf-8 -*-

"""Tpl class"""

from src.core import logger
from src.core import colour
from src.core import sys
from .config import Config
from .exceptions import TplError

class Tpl():
    """Tpl class"""

    @staticmethod
    def cancel(message='', key='', **args):
        if key:
            message = Tpl.__message(key, args=args)
        sys.exit(logger.log().warning(message))

    @staticmethod
    def line(message='', key='', color='white', **args):
        """ stored colored message """

        if key:
            message = Tpl.__message(key, args=args)
        sys.writels(Tpl.info(message))

    @staticmethod
    def inline(message='', key='',  color='white', **args):
        """ stored colored message """

        if key:
            message = Tpl.__message(key, args=args)
        return colour.colored(message, color=color)

    @staticmethod
    def message(string, args={} , color='white'):

        """ colored message """
        sys.writeln(colour.colored(string.format(**args), color=color))

    @staticmethod
    def error(message='', key='', **args):

        message = str(message)

        if key:
            message = Tpl.__message(key, args=args)

        logger.log().error(message)

    @staticmethod
    def warning(message='', key='', **args):

        message = str(message)

        if key:
            message = Tpl.__message(key, args=args)
        logger.log().warning(message)

    @staticmethod
    def info(message='', key='', **args):

        message = str(message)

        if key:
            message = Tpl.__message(key, args=args)
        logger.log().info(message)


    @staticmethod
    def debug(message='', key='', **args):

        message = str(message)

        if key:
            message = Tpl.__message(key, args=args)
        logger.log().debug(message)

    @staticmethod
    def __message(key, **args):
        """ apply option to log message """

        try:

            message = Tpl.__tpl_message(key)
            args = args.get('args')
            if not len(args):
                return message
            else:
                return message.format(**args)
        except (AttributeError, TplError) as e:
            raise TplError(e)

    @staticmethod
    def __tpl_message(key, **args):
        tpl = getattr(Config, 'templates')
        if key not in tpl:
            raise TplError('Could not find tpl option `{0}`'.format(**args))
        message = tpl[key]
        return message