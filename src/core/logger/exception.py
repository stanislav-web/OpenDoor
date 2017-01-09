# -*- coding: utf-8 -*-

"""Logger classes"""

import logging
import logging.config
import inspect

from .config import Config

class Exception():

    @staticmethod
    def log(class_name='Error', message=''):
        try:

            logging.config.dictConfig(Config.exceptions)
            logger = logging.getLogger('exceptions')


            # dump the message + the name of this function to the log.
            func = inspect.currentframe().f_back.f_code

            message = "{class_name}: {message} in {file} -> {func}() line {line}".format(
                class_name=class_name,
                message=message,
                file=func.co_filename,
                func=func.co_name,
                line=func.co_firstlineno
            )
            logger.error(message)
        except ValueError as e:
            raise e
