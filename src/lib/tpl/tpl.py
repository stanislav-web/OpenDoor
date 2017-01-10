# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development Team: Stanislav Menshov
"""
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
    def line(message='', key='', **args):
        """ stored colored message """

        if key:
            message = Tpl.__message(key, args=args)

        print logger.get_colorized_line(message)
        exit()
        log = logger.log(use_stream=True)[0]
        stream = logger.log(use_stream=True)[1]
        #@TODO
        log.info(message)
        log_contents = stream.getvalue()
        stream.close()
        sys.writels(message)

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