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

from ..filesystem.filesystem import FileSystem


def exception_log():
    """
    Get exception log path
    :return: string
    """
    config = FileSystem.readcfg('setup.cfg')
    return config.get('system', 'exceptions_log')


class Config:
    """Config class"""

    exceptions = {
        "version" : 1,
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
                "backupCount" : 10
            }
        },
        "loggers": {
            "exceptions": {
                "handlers": ["exception_file_handler"],
            }
        }
    }