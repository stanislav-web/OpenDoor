# -*- coding: utf-8 -*-

"""Reader class"""

import ConfigParser
import StringIO
import os
from random import randrange

import sys

from src.lib.logger.logger import Logger as Log


class Reader(object):
    """Reader class"""

    @staticmethod
    def read_file(filename):
        dir = os.path.dirname(os.path.realpath(__file__))

    def __init__(self):

        try:
            self.config = self.get_config()
        except ConfigParser.ParsingError as e:
            sys.exit(Log.error(e.message))

        self.__useragents = self.get_file_data('useragents')
        self.__proxy = self.get_file_data('proxy')
        self.__directories = self.get_file_data('directories')
        self.__subdomains = self.get_file_data('subdomains')

    def get_file_data(self, target):
        """ Get target file data"""

        file_path = self.config.get('opendoor', target)
        file = os.path.join(os.getcwd(), file_path)
        if not os.path.isfile(file):
            sys.exit(Log.error("{0} is not a file".format(file)))
        if not os.access(file, os.R_OK):
            sys.exit(Log.error("{0} file can not be read. Setup chmod 0644 ".format(file)))
        with open(file) as f_handler:
            data = f_handler.readlines()
        return data

    @staticmethod
    def get_config():
        """ Get configuration file data """

        config = ConfigParser.RawConfigParser()
        config_file = os.path.join(os.getcwd(), 'setup.cfg')
        if not os.path.isfile(config_file):
            sys.exit(Log.error("{0} is not a file ".format(config_file)))
        if not os.access(config_file, os.R_OK):
            sys.exit(Log.error("Configuration file {0} can not be read. Setup chmod 0644".format(config_file)))

        try:
            config.read(config_file)
            return config
        except ConfigParser.ParsingError as e:
            sys.exit(Log.error(e.message))

    @staticmethod
    def get_config_raw(s_config):
        """ Get configuration file data as raw format"""

        buf = StringIO.StringIO(s_config)
        try:
            config = ConfigParser.ConfigParser()
            config.readfp(buf)
            return config
        except ConfigParser.Error as e:
            sys.exit(Log.error(e.message))

    def get_random_user_agent(self):
        """ Get random user agent from user-agents list"""

        index = randrange(0, len(self.__useragents))
        return self.__useragents[index].rstrip()

    def get_random_proxy(self):
        """ Get random proxy from proxy list"""

        index = randrange(0, len(self.__proxy))
        return self.__proxy[index].rstrip()
