# -*- coding: utf-8 -*-

"""Config classes """

from ..filesystem.filesystem import FileSystem


def exception_log():
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
            }
        },
        "loggers": {
            "exceptions": {
                "handlers": ["exception_file_handler"],
            }
        }
    }