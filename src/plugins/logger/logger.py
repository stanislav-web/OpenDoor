# -*- coding: utf-8 -*-

"""LoggerPlugin classes"""

from src.registry import Plugin

class Logger(Plugin):

    """ LoggerPlugin class"""

    def register_signals(self):
        print "Class created and registering signals"

