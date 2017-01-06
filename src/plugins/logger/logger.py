# -*- coding: utf-8 -*-

"""LoggerPlugin classes"""

from src.registry import Plugin
from config import Config
from src.core import filesystem

class Logger(Plugin):

    """ LoggerPlugin class"""


    def register_signals(self):
        #print "Class created and registering signals"
        pass

    @staticmethod
    def is_logged(resource):
        return filesystem.is_exist(Config.params['log_dir'], resource)
