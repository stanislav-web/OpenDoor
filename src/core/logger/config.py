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

import os

from src.core import filesystem


def exception_log():
    """
    Get exception log path
    :return: string
    """

    config = filesystem.readcfg('setup.cfg')
    return filesystem.getabsname(config.get('system', 'exceptions_log'))


class Config(object):

    """Config class"""

    logdir = os.path.dirname(exception_log())
    legacy_config = "{0}{1}{2}".format(os.path.dirname(__file__), filesystem.sep, 'legacy.conf')
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
