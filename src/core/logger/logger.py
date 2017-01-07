# -*- coding: utf-8 -*-

"""Logger classes"""

import logging
import logging.config

from config import Config
from src.core import filesystem
from colorize import ColorizingStreamHandler

class Logger():
    """ Logger class"""
    def __init__(self):
        pass

    @staticmethod
    def set(logger_name=''):

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(ColorizingStreamHandler())



        logging.debug('DEBUG')
        logging.info('INFO')
        logging.warning('WARNING')
        logging.error('ERROR')
        logging.critical('CRITICAL')




        return root
