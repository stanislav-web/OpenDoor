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

import sys
import logging
import logging.config
from colorize import ColorizingStreamHandler
from rainbow import RainbowLoggingHandler

class Logger():
    """ Logger class"""

    @staticmethod
    def get_colorized_line(message, level=logging.INFO):

        record = type('', (), {})()
        record.levelno = level
        color = ColorizingStreamHandler()
        print color.is_tty
        color.output_colorized(message)
        return color.colorize(message, record)

    @staticmethod
    def log(name=__name__, use_stream=False):
        """
        Library log handler

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
