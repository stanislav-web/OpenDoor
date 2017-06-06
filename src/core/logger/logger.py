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

import logging
import logging.config
import sys
import time
from inspect import currentframe
from .rainbow import RainbowLoggingHandler


class Logger(object):

    """ Logger class"""

    _record = None

    _levels = {'error': 40, 'warning': 30, 'info': 20, 'debug': 10}

    @staticmethod
    def inline(msg='', status='info'):
        """
        Formatted log message for inline console stdout
        :param str msg: formatted message
        :param str status: status name
        :return: str
        """

        if None is Logger._record:
            Logger._record = type('record', (object,),
                                  dict(exc_info=False,
                                       stack_info=False,
                                       exc_text=False,
                                       name='',
                                       levelno=Logger._levels.get(status),
                                       funcName=status,
                                       lineno=currentframe().f_back.f_lineno)
                                  )

        Logger._record.created = time.time()

        # noinspection PyPep8Naming
        def getMessage(__class__):
            """
            Emulate message

            :param __class__: current class
            :return: str
            """

            del __class__

            return msg

        setattr(Logger._record, 'getMessage', classmethod(getMessage))
        message = RainbowLoggingHandler().colorize(Logger._record)
        return message

    @staticmethod
    def log(name=__name__):
        """
        Log handler
        :param str name: log name
        :return: logging
        """

        logger = logging.getLogger(name)

        if not len(logger.handlers):
            logger.setLevel(logging.ERROR)
            logger.setLevel(logging.INFO)
            logger.setLevel(logging.WARNING)
            logger.setLevel(logging.DEBUG)
            handler = RainbowLoggingHandler(sys.stdout)
            logger.addHandler(handler)

        return logger
