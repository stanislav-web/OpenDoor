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

from src.core import FileSystemError
from src.core import CoreSystemError
from src.core import filesystem
from src.core import process
from src.core import sys
from .config import Config
from .exceptions import ReaderError


class Reader(object):

    """Reader class"""

    def __init__(self, browser_config):
        """
        Reader constructor
        :param dict browser_config:
        """

        self.__config = self.__load_config()
        self.__browser_config = browser_config
        self.__useragents = []
        self.__proxies = []
        self.__ignored = []
        self.__counter = 0

    @staticmethod
    def __load_config():
        """
        Load main configuration file
        :raise ReaderError
        :return: ConfigParser.RawConfigParser
        """

        try:
            config = filesystem.readcfg(Config.setup)
            return config
        except FileSystemError as error:
            raise ReaderError(str(error))

    def get_user_agents(self):
        """
        Get user agents from user-agents list
        :raise ReaderError
        :return: list
        """

        try:
            if not len(self.__useragents):
                self.__useragents = filesystem.read(self.__config.get('opendoor', 'useragents'))
            return self.__useragents

        except (TypeError, FileSystemError) as error:
            raise ReaderError(error)

    def get_ignored_list(self):
        """
        Get ignored dir list
        :raise ReaderError
        :return: list
        """

        try:

            if not len(self.__ignored):
                ignored = filesystem.read(self.__config.get('opendoor', 'ignored'))
                for item in ignored:
                    item = item.replace("\n", "")
                    if "/" == item[0]:
                        item = item.strip('/')
                    self.__ignored.append(item)

            return self.__ignored

        except (TypeError, FileSystemError) as error:
            raise ReaderError(error)

    def get_proxies(self):
        """
        Get proxy list
        :raise ReaderError
        :return: list
        """

        try:
            if False is self.__browser_config.get('is_standalone_proxy'):

                if True is self.__browser_config.get('is_external_torlist'):
                    self.__proxies = filesystem.read(self.__browser_config.get('torlist'))
                else:

                    if not len(self.__proxies):
                        self.__proxies = filesystem.read(self.__config.get('opendoor', 'proxies'))
                return self.__proxies
            else:
                return []

        except (TypeError, FileSystemError) as error:
            raise ReaderError(error)

    def get_lines(self, params, loader):
        """
        Read lines from large file
        :param dict params: input params
        :param funct loader:  callback function
        :raise ReaderError
        :return: None
        """

        try:
            if True is self.__browser_config.get('use_extensions')\
                    and 'directories' == self.__browser_config.get('list'):
                dirlist = self.__config.get('opendoor', 'extensionlist')
            elif True is self.__browser_config.get('use_random'):
                dirlist = self.__config.get('opendoor', 'tmplist')
            else:
                if True is self.__browser_config.get('is_external_wordlist'):
                    dirlist = self.__browser_config.get('list')
                    self.__browser_config.update({'list': 'directories'})
                else:
                    dirlist = self.__config.get('opendoor', self.__browser_config.get('list'))

            filesystem.readline(dirlist, handler=getattr(self, '_{0}__line'.format(self.__browser_config.get('list'))),
                                handler_params=params, loader=loader)
        except (TypeError, FileSystemError) as error:
            raise ReaderError(error)

    @classmethod
    def _subdomains__line(cls, line, params):
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
        
        if port is Config.ssl_port or port is Config.http_port:
            port = ''
        else:
            port = ':{0}'.format(port)

        line = "{scheme}{sub}.{host}{port}".format(scheme=params.get('scheme'), host=host, port=port, sub=line)

        return line

    def _directories__line(self, line, params):
        """
        Read lines from directories file
        :param str line: single line
        :param dict params: input params
        :return: str
        """

        line = line.strip("\n")
        if True is line.startswith('/'):
            line = line[1:]

        if 'prefix' in self.__browser_config and 0 < len(self.__browser_config.get('prefix')):
            line = self.__browser_config.get('prefix') + line

        if False is line.endswith('/') and False is filesystem.has_extension(line) and '.' not in line:
            line = '{0}/'.format(line)

        port = params.get('port')

        if port is Config.ssl_port or port is Config.http_port:
            port = ''
        else:
            port = ':{0}'.format(port)
        line = "{scheme}{host}{port}/{uri}".format(scheme=params.get('scheme'), host=params.get('host'), port=port,
                                                   uri=line, )

        return line

    def randomize_list(self, target, output):
        """
        Randomize scan list
        :param str target: target list
        :param str output: output list
        :raise ReaderError
        :return: None
        """

        try:

            target_file = self.__config.get('opendoor', target)
            output_file = self.__config.get('opendoor', output)
            filesystem.makefile(output_file)

            if False is sys().is_windows:
                process.execute('shuf {target} -o {output}'.format(target=target_file, output=output_file))
            else:
                filesystem.shuffle(target=target_file, output=output_file, total=self.total_lines)
        except (CoreSystemError, FileSystemError) as error:
            raise ReaderError(error)

    def filter_by_extension(self, target, output, extensions):
        """
        Filter list by multiple extensions

        :param str target: target list
        :param str output: output list
        :param list extensions: filtered extensions
        :return: None
        """

        try:

            target_file = self.__config.get('opendoor', target)
            output_file = self.__config.get('opendoor', output)

            dirlist = filesystem.read(target_file)
            dirlist = [i.strip() for i in dirlist]
            pattern = '.*\.' + '|.*\.'.join(extensions)
            newlist = filesystem.filter_file_lines(dirlist, pattern)
            filesystem.makefile(output_file)
            filesystem.writelist(output_file, newlist, '\n')
            self.__counter = len(newlist)

        except (CoreSystemError, FileSystemError) as error:
            raise ReaderError(error)

    def count_total_lines(self):
        """
        Count total lines inside wordlist
        :raise ReaderError
        :return: int
        """
        try:

            if 0 is self.__counter:
                if True is self.__browser_config.get('is_external_wordlist'):
                    dirlist = self.__browser_config.get('list')
                else:
                    dirlist = self.__config.get('opendoor', self.__browser_config.get('list'))
                self.__counter = len(filesystem.read(dirlist))

            return self.__counter

        except (TypeError, FileSystemError) as error:
            raise ReaderError(error)

    @property
    def total_lines(self):
        """
        Return total lines
        :return: int
        """

        return self.__counter
