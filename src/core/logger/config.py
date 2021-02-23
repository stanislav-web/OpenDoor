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

    Development Team: Brain Storm Team
"""

import os

from src.core import filesystem
from src.core import CoreConfig


def exception_log():
    """
    Get exception log path
    :return: string
    """

    exception_filelog = CoreConfig.get('data').get('exceptions_log')
    return filesystem.getabsname(exception_filelog)


class Config(object):

    """Config class"""

    logdir = os.path.dirname(exception_log())
    exceptions = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "exception_format": {
                "format": "%(asctime)s [%(levelname)s] : %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "exception_file_handler": {
                "level": "ERROR",
                "formatter": "exception_format",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": exception_log(),
                "maxBytes": 10485760,
                "backupCount": 10
            }
        },
        "loggers": {
            "exceptions": {
                "handlers": ["exception_file_handler"]
            }
        }
    }
