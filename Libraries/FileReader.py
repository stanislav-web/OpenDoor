from Logger import Logger as log

try:
    import os
    import StringIO
    import ConfigParser
    from random import randrange
    from linereader import copen

except ImportError:
    log.critical("""\t\t[!] You need linereader!
                install it from http://pypi.python.org/pypi
                or run pip install linereader """)

class FileReader:
    """Filereader class"""

    def __init__(self):

        try:
            self.config = self.get_config()
        except ConfigParser.ParsingError as e:
            log.critical(e.message)

        self.__useragents = self.get_file_data('useragents')
        self.__proxy = self.get_file_data('proxy')
        self.__directories = self.get_file_data('directories')
        self.__subdomains = self.get_file_data('subdomains')

    def get_file_data(self, target):
        """ Get target file data"""
        file_path = self.config.get('opendoor', target)
        file = os.path.join(os.getcwd(), file_path);
        if not os.path.isfile(file):
            log.critical(file + """ is not a file""")
        if not os.access(file, os.R_OK):
            log.critical(file + """ file can not be read. Run chmod 0644 """ + file)
        with open(file) as f_handler:
            data = f_handler.readlines()
        return data

    @staticmethod
    def get_config():
        config = ConfigParser.RawConfigParser()

        config_file = os.path.join(os.getcwd(), 'setup.cfg');
        if not os.path.isfile(config_file):
            log.critical(file + """ is not a file""")
        if not os.access(config_file, os.R_OK):
            log.critical(""" Configuration file setup.cfg can not be read. Run chmod 0644 """ + config_file)

        try:
            config.read(config_file)
            return config
        except ConfigParser.ParsingError as e:
            log.critical(e.message)

    @staticmethod
    def get_config_raw(s_config):
        buf = StringIO.StringIO(s_config)
        try:
            config = ConfigParser.ConfigParser()
            config.readfp(buf)
            return config
        except ConfigParser.Error as e:
            log.critical(e.message)

    def get_user_agent(self):
        user_agent = self.__useragents[0]
        return user_agent

    def get_random_user_agent(self):

        index = randrange(0,len(self.__useragents))
        return self.__useragents[index].rstrip()

    def get_random_proxy(self):

        index = randrange(0,len(self.__proxy))
        return self.__proxy[index].rstrip()