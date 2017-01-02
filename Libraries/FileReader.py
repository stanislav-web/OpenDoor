# -*- coding: utf-8 -*-

"""Filereader class"""

import ConfigParser
import StringIO
import os
from random import randrange

from .Logger import Logger as Log


class FileReader(object):
    """Filereader class"""

    def __init__(self):

        try:
            self.config = self.get_config()
        except ConfigParser.ParsingError as e:
            Log.critical(e.message)

        self.__useragents = self.get_file_data('useragents')
        self.__proxy = self.get_file_data('proxy')
        self.__directories = self.get_file_data('directories')
        self.__subdomains = self.get_file_data('subdomains')

    def get_file_data(self, target):
        """ Get target file data"""

        file_path = self.config.get('opendoor', target)
        file = os.path.join(os.getcwd(), file_path)
        if not os.path.isfile(file):
            Log.critical(file + """ is not a file""")
        if not os.access(file, os.R_OK):
            Log.critical(file + """ file can not be read. Run chmod 0644 """ + file)
        with open(file) as f_handler:
            data = f_handler.readlines()
        return data

    @staticmethod
    def get_config():
        """ Get configuration file data """

        config = ConfigParser.RawConfigParser()
        config_file = os.path.join(os.getcwd(), 'setup.cfg')
        if not os.path.isfile(config_file):
            Log.critical("{0} is not a file".format('setup.cfg'))
        if not os.access(config_file, os.R_OK):
            Log.critical("Configuration file setup.cfg can not be read. Add chmod 0644 {0}".format(config_file))

        try:
            config.read(config_file)
            return config
        except ConfigParser.ParsingError as e:
            Log.critical(e.message)

    @staticmethod
    def get_config_raw(s_config):
        """ Get configuration file data as raw format"""

        buf = StringIO.StringIO(s_config)
        try:
            config = ConfigParser.ConfigParser()
            config.readfp(buf)
            return config
        except ConfigParser.Error as e:
            Log.critical(e.message)

    def get_random_user_agent(self):
        """ Get random user agent from user-agents list"""

        index = randrange(0, len(self.__useragents))
        return self.__useragents[index].rstrip()

    def get_random_proxy(self):
        """ Get random proxy from proxy list"""

        index = randrange(0, len(self.__proxy))
        return self.__proxy[index].rstrip()
