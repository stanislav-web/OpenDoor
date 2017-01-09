# -*- coding: utf-8 -*-

"""Logger classes"""

import sys
import logging
import logging.config
from rainbow import RainbowLoggingHandler

class Logger():
    """ Logger class"""

    @staticmethod
    def log(name=__name__):

        logger = logging.getLogger(name)

        if not len(logger.handlers):
            logger.setLevel(logging.ERROR)
            logger.setLevel(logging.INFO)
            logger.setLevel(logging.WARNING)
            logger.setLevel(logging.DEBUG)
            handler = RainbowLoggingHandler(sys.stdout)
            logger.addHandler(handler)

        return logger
