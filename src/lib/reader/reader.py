# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development Team: Stanislav WEB
"""

import random
from .config import Config
from src.core import process
from src.core import filesystem
from src.core import FileSystemError , SystemError
from ...lib.exceptions import LibError

class Reader():

    """Reader class"""

    def __init__(self, browser_config):
        """
        Reader constructor

        :param dict browser_config:
        """

        self.__config =  self.__load_config()
        self.__browser_config =  browser_config
        self.__useragents = []
        self.__proxies = []
        self.__counter = 0

    @staticmethod
    def __load_config():
        """
        Load main configuration file

        :raise LibError
        :return: ConfigParser.RawConfigParser
        """

        try :
            config = filesystem.readcfg(Config.setup)
            return config
        except FileSystemError as e:
            raise LibError(e)


    def _get_random_user_agent(self):
        """
        Get random user agent from user-agents list

        :raise LibError
        :return: str
        """

        try:

            if not len(self.__useragents):
                self.__useragents = filesystem.read(self.__config.get('opendoor', 'useragents'))

            index = random.randrange(0, len(self.__useragents))
            return self.__useragents[index].strip()

        except FileSystemError as e:
            raise LibError(e)


    def _get_random_proxy(self):
        """
        Get random proxy from proxy list

        :raise LibError
        :return: str
        """

        try:

            if not len(self.__proxies):
                self.__proxies = filesystem.read(self.__config.get('opendoor', 'proxies'))

            index = random.randrange(0, len(self.__proxies))
            return self.__proxies[index].strip()

        except FileSystemError as e:
            raise LibError(e)

    def _get_lines(self, listname, params, loader):
        """
        Read lines from large file

        :param str listname: list name
        :param dict params: input params
        :param funct loader:  callback function
        :raise LibError
        :return: str
        """

        if True is self.__browser_config.get('use_random'):
            dirlist = self.__config.get('opendoor', 'tmplist')
        else:
            dirlist = self.__config.get('opendoor', listname)

        try:
            filesystem.readline(dirlist,
                                      handler=getattr(self, '_{0}__line'.format(
                                                        self.__browser_config.get('list'))
                                                      ),
                                      handler_params=params,
                                      loader=loader
                                      )
        except FileSystemError as e:
            raise LibError(e)


    def _subdomains__line(self, line, params):
        """
        Read lines from subdomains file

        :param str line: single line
        :param dict params: input params
        :return: str
        """

        line = line.strip("\n")
        line.strip('/')

        host = params.get('host')
        port = params.get('port')

        if 'www.' in host:
            host = host.replace("www.", "")

        if Config.port is port:
            port = ''
        else:
            port = ':{0}'.format(port)

        line = "{scheme}{sub}.{host}{port}".format(
            scheme=params.get('scheme'),
            host=host,
            port=port,
            sub=line,
        )

        return line

    def _directories__line(self, line, params):
        """
        Read lines from directories file

        :param str line: single line
        :param dict params: input params
        :return: str
        """

        line = line.strip("\n")
        line.lstrip('/')

        port = params.get('port')

        if Config.port is port:
            port = ''
        else:
            port = ':{0}'.format(port)

        line = "{scheme}{host}{port}/{uri}".format(
            scheme=params.get('scheme'),
            host=params.get('host'),
            port=port,
            uri=line,
        )

        return line

    def _randomize_list(self, target_list):
        """
        Randomize scan list

        :param str target_list: target list
        :return: Null
        """
        try:

            target_file = self.__config.get('opendoor', target_list)
            result_file = self.__config.get('opendoor', 'tmplist')
            filesystem.makefile(result_file)
            process.execute('shuf {target} -o {result}'.format(target=target_file, result=result_file))
        except (SystemError, FileSystemError) as e:
            raise LibError(e)

    def _count_total_lines(self, listname):

        """
        Count total lines inside wordlist

        :param string listname:
        :raise LibError
        :return: int
        """
        try:

            if 0 is self.__counter:
                dirlist = self.__config.get('opendoor', listname)
                self.__counter = filesystem.read(dirlist).__len__()

            return self.__counter

        except FileSystemError as e:
            raise LibError(e)

    @property
    def total_lines(self):

        """
        Return total lines

        :return: int
        """

        return self.__counter
