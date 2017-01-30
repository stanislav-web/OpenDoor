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

    Development Team: Stanislav WEB
"""

from src.core import colour
from src.core import logger
from src.core import sys
from .config import Config
from .exceptions import TplError


class Tpl(object):
    """Tpl class"""

    @staticmethod
    def cancel(msg='', key='', **args):
        """
        Print message and stop propagation
        :param str msg: text message
        :param str key: message key for template
        :param dict args: additional arguments
        :raise TplError
        :return: None
        """

        try:
            if key:
                msg = Tpl.__format_message(key, args=args)
            sys.exit(logger.log().warning(msg))
        except (AttributeError, TplError) , e:
            raise TplError(e.message)

    @staticmethod
    def line_log(msg='', key='', status='info', write=True, **args):
        """
        Stored colored log line to variable
        :param str msg: text message
        :param str key: message key for template
        :param str status: log status
        :param bool write: write immediatelly
        :param dict args: additional arguments
        :raise TplError
        :return: None
        """

        try:
            if key:
                msg = Tpl.__format_message(key, args=args)
                msg = logger.inline(msg=msg, status=status)
            if True is write:
                sys.writels(msg)
            else:
                return msg

        except (AttributeError, TplError) , e:
            raise TplError(e.message)

    @staticmethod
    def prompt(key='', status='info'):
        """
        Prompt message
        :param str msg:
        :param str key:
        :param str status:
        :return:str
        """

        msg = Tpl.line_log(key=key, status=status, write=False)
        result = raw_input(msg)
        return result

    @staticmethod
    def line(msg='', key='', color='white', **args):
        """
        Stored colored line to variable
        :param str msg: text message
        :param str key: message key for template
        :param str color: color
        :param dict args: additional arguments
        :raise TplError
        :return: str
        """

        try:
            if key:
                msg = Tpl.__format_message(key, args=args)
            return colour.colored(msg, color=color)
        except (AttributeError, TplError) , e:
            raise TplError(e.message)

    @staticmethod
    def message(msg, args=None, color='white'):
        """
        Simple colored message
        :param str msg: text message
        :param dict args: additional arguments
        :param str color: color
        :return: None
        """

        if None is args:
            args = {}

        sys.writeln(colour.colored(msg.format(**args), color=color))

    @staticmethod
    def error(msg='', key='', **args):
        """
        Error log message
        :param str msg: text message
        :param str key: message key for template
        :param dict args: additional arguments
        :raise TplError
        :return: None
        """

        msg = str(msg)

        try:
            if key:
                msg = Tpl.__format_message(key, args=args)

            logger.log().error(msg)
        except (AttributeError, TplError) , e:
            raise TplError(e.message)

    @staticmethod
    def warning(msg='', key='', **args):
        """
        Warning log message
        :param str msg: text message
        :param str key: message key for template
        :param dict args: additional arguments
        :raise TplError
        :return: None
        """

        msg = str(msg)

        try:
            if key:
                msg = Tpl.__format_message(key, args=args)

            logger.log().warning(msg)
        except (AttributeError, TplError) , e:
            raise TplError(e.message)

    @staticmethod
    def info(msg='', key='', clear=False, **args):
        """
        Info log message
        :param str msg: text message
        :param str key: message key for template
        :param dict args: additional arguments
        :param bool clear: clear prev line
        :raise TplError
        :return: None
        """

        msg = str(msg)

        try:
            if key:
                msg = Tpl.__format_message(key, args=args)
            if True is clear:
                sys.writels("")
            logger.log().info(msg)
        except (AttributeError, TplError) , e:
            raise TplError(e.message)

    @staticmethod
    def debug(msg='', key='', **args):
        """
        Debug log message
        :param str msg: text message
        :param str key: message key for template
        :param dict args: additional arguments
        :raise TplError
        :return: None
        """

        msg = str(msg)

        try:
            if key:
                msg = Tpl.__format_message(key, args=args)

            logger.log().debug(msg)
        except (AttributeError, TplError) , e:
            raise TplError(e.message)

    @staticmethod
    def __format_message(key, **args):
        """
        Format message from config key
        :param str key: message
        :param dict args: additional arguments
        :raise AttributeError
        :raise TplError
        :return: str
        """

        tpl = getattr(Config, 'templates')
        if key not in tpl:
            raise TplError('Could not find tpl option `{0}`'.format(key))
        msg = tpl[key]

        args = args.get('args')
        if not len(args):
            return msg
        else:
            return msg.format(**args)
