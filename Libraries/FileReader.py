try:
    import ConfigParser
    import os
    import sys
    from random import randint
    from linereader import copen
except ImportError:
    sys.exit("""You need linereader!
                install it from http://pypi.python.org/pypi
                or run pip install linereader .""")

class FileReader:
    """Filereader class"""
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read(os.getcwd() + '/setup.cfg')

        # Files User Agent
        useragents_file_path = config.get('opendoor', 'useragents')
        self.__useragents_file = copen(os.getcwd() + '/' + useragents_file_path)
        self.__useragents_file_lines = self.__useragents_file.count('\n')

    def get_user_agent(self):
        user_agent = self.__useragents_file.getline(1)
        return user_agent

    def get_random_user_agent(self):
        random_user_agent = self.__useragents_file.getline(randint(1, self.__useragents_file_lines))
        return random_user_agent