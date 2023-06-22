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

    Development Team: Brain Storm Team
"""

from src.core import FileSystemError
from src.core import CoreSystemError
from src.core import CoreConfig
from src.core import filesystem
from src.core import process
from src.core import sys
from src.core import helper
from .config import Config
from .exceptions import ReaderError


class Reader(object):

    """Reader class"""

    def __init__(self, browser_config):
        """
        Reader constructor
        :param dict browser_config:
        """

        self.__config = CoreConfig.get('data')
        self.__browser_config = browser_config
        self.__useragents = []
        self.__proxies = []
        self.__ignored = []
        self.__counter = 0

    def get_user_agents(self):
        """
        Get user agents from user-agents list
        :raise ReaderError
        :return: list
        """

        try:
            if not len(self.__useragents):
                self.__useragents = filesystem.read(self.__config.get('useragents'))
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
                ignored = filesystem.read(self.__config.get('ignored'))
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
                        self.__proxies = filesystem.read(self.__config.get('proxies'))
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
            if True is self.__browser_config.get('use_random'):
                # use randomizing list.dat
                dirlist = self.__config.get('tmplist')
            elif True is self.__browser_config.get('use_extensions')\
                    and 'directories' == self.__browser_config.get('list'):
                dirlist = self.__config.get('extensionlist')
            elif True is self.__browser_config.get('use_ignore_extensions')\
                    and 'directories' == self.__browser_config.get('list'):
                dirlist = self.__config.get('ignore_extensionlist')
            else:
                if True is self.__browser_config.get('is_external_wordlist'):
                    dirlist = self.__browser_config.get('wordlist')
                else:
                    dirlist = self.__config.get(self.__browser_config.get('list'))
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

        line = helper.filter_domain_string(line)

        host = params.get('host')
        port = params.get('port')

        if 'www.' in host:
            host = host.replace("www.", "")

        if port is Config.ssl_port or port is Config.http_port:
            port = ''
        else:
            port = ':{0}'.format(port)

        line = "{scheme}{sub}.{host}{port}".format(scheme=params.get('scheme'),
                                                   host=host,
                                                   port=port,
                                                   sub=line)

        return line

    def _directories__line(self, line, params):
        """
        Read lines from directories file
        :param str line: single line
        :param dict params: input params
        :return: str
        """

        line = helper.filter_directory_string(line)

        if 'prefix' in self.__browser_config and 0 < len(self.__browser_config.get('prefix')):
            line = self.__browser_config.get('prefix') + line
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

            target_file = self.__config.get(target)
            tmp_file = self.__config.get(output)
            output_file = filesystem.makefile(tmp_file)

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

            target_file = self.__config.get(target)
            output_file = self.__config.get(output)

            dirlist = filesystem.read(target_file)
            dirlist = [i.strip() for i in dirlist]
            pattern = '.*\.' + '|.*\.'.join(extensions)
            newlist = filesystem.filter_file_lines(dirlist, pattern)
            filesystem.makefile(output_file)
            filesystem.writelist(output_file, newlist, '\n')
            self.__counter = len(newlist)

        except (CoreSystemError, FileSystemError) as error:
            raise ReaderError(error)

    def filter_by_ignore_extension(self, target, output, extensions):
        """
        Specific filter for selected exuensions

        :param str target: target list
        :param str output: output list
        :param list extensions: filtered extensions
        :return: None
        """

        try:

            target_file = self.__config.get(target)
            output_file = self.__config.get(output)
            dirlist = filesystem.read(target_file)
            dirlist = [i.strip() for i in dirlist]
            pattern = '^('
            for ext in extensions:
                pattern += '(?!\.{0})'.format(ext)
            pattern += '.)*$'
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
            if 0 == self.__counter:
                if True is self.__browser_config.get('is_external_wordlist'):
                    dirlist = self.__browser_config.get('wordlist')
                else:
                    dirlist = self.__config.get(self.__browser_config.get('list'))
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
