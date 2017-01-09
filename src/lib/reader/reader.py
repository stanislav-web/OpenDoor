# -*- coding: utf-8 -*-

"""Reader class"""

from .config import Config
from src.core import filesystem
from src.core import FileSystemError
from ...lib.exceptions import LibError

class Reader():

    """Reader class"""

    def __init__(self):

        self.config =  self.__load_config()

        # try:
        #     self.config = self.get_config()
        # except ConfigParser.ParsingError as e:
        #     sys.exit(Log.error(e.message))
        #
        # self.__useragents = self.get_file_data('useragents')
        # self.__proxy = self.get_file_data('proxy')
        # self.__directories = self.get_file_data('directories')
        # self.__subdomains = self.get_file_data('subdomains')

    @staticmethod
    def __load_config():
        """ load configuration file """

        try :
            config = filesystem.readcfg(Config.setup)
            return config
        except FileSystemError as e:
            raise LibError(e)




    # def get_file_data(self, target):
    #     """ Get target file data"""
    #
    #     file_path = self.config.get('opendoor', target)
    #     file = os.path.join(os.getcwd(), file_path)
    #     if not os.path.isfile(file):
    #         sys.exit(Log.error("{0} is not a file".format(file)))
    #     if not os.access(file, os.R_OK):
    #         sys.exit(Log.error("{0} file can not be read. Setup chmod 0644 ".format(file)))
    #     with open(file) as f_handler:
    #         data = f_handler.readlines()
    #     return data
    #
    # def get_random_user_agent(self):
    #     """ Get random user agent from user-agents list"""
    #
    #     index = randrange(0, len(self.__useragents))
    #     return self.__useragents[index].rstrip()
    #
    # def get_random_proxy(self):
    #     """ Get random proxy from proxy list"""
    #
    #     index = randrange(0, len(self.__proxy))
    #     return self.__proxy[index].rstrip()
