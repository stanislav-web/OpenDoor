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

import inspect
import logging
import logging.config

from src.core import filesystem
from .config import Config


class LoggerException(object):

    """ Exception class """

    @staticmethod
    def log(class_name='Error', message=''):
        """
        Syslog error handler
        :param str class_name: log name
        :param str message: log message
        :raise Error
        :return: None
        """

        try:

            filesystem.makedir(Config.logdir)
            try:
                logging.config.dictConfig(Config.exceptions)
            except AttributeError:
                logging.config.fileConfig(Config.legacy_config)
            logger = logging.getLogger('exceptions')
            func = inspect.currentframe().f_back.f_code
            message = "{class_name}: {message} in {file} -> {func}() line {line}".format(
                    class_name=class_name,
                    message=message,
                    file=func.co_filename,
                    func=func.co_name,
                    line=func.co_firstlineno)
            logger.error(message)
        except (Exception, ValueError) as error:
            raise Exception(error)
