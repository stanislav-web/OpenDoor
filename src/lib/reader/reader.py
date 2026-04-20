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

import re

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

    @staticmethod
    def _is_default_port(port):
        """
        Check whether port is one of the default HTTP/HTTPS ports.

        :param int port:
        :return: bool
        """

        return port == Config.ssl_port or port == Config.http_port

    @staticmethod
    def _format_port(port):
        """
        Convert a port to an URL suffix.

        :param int port:
        :return: str
        """

        if Reader._is_default_port(port):
            return ''
        return ':{0}'.format(port)

    @staticmethod
    def _normalize_extensions(extensions):
        """
        Normalize extension names for regex-based filters.

        :param list extensions:
        :return: list
        """

        normalized = []
        for extension in extensions:
            extension = str(extension).strip().lstrip('.')
            if extension:
                normalized.append(extension)
        return normalized

    @staticmethod
    def _build_include_extension_pattern(extensions):
        """
        Build a regex that keeps only the selected extensions.

        :param list extensions:
        :return: str
        """

        normalized = Reader._normalize_extensions(extensions)
        escaped = [re.escape(extension) for extension in normalized]
        return r'.*\.({0})$'.format('|'.join(escaped))

    @staticmethod
    def _build_ignore_extension_pattern(extensions):
        """
        Build a regex that excludes the selected extensions.

        :param list extensions:
        :return: str
        """

        normalized = Reader._normalize_extensions(extensions)
        escaped = [re.escape(extension) for extension in normalized]
        return r'^(?!.*\.({0})$).*$'.format('|'.join(escaped))

    def _get_dirlist_path(self):
        """
        Resolve the active wordlist path according to browser configuration.

        :return: str
        """

        if True is self.__browser_config.get('use_random'):
            return self.__config.get('tmplist')

        if True is self.__browser_config.get('use_extensions') and 'directories' == self.__browser_config.get('list'):
            return self.__config.get('extensionlist')

        if True is self.__browser_config.get('use_ignore_extensions') and 'directories' == self.__browser_config.get('list'):
            return self.__config.get('ignore_extensionlist')

        if True is self.__browser_config.get('is_external_wordlist'):
            return self.__browser_config.get('wordlist')

        return self.__config.get(self.__browser_config.get('list'))

    def get_user_agents(self):
        """
        Get user agents from user-agents list
        :raise ReaderError
        :return: list
        """

        try:
            if not self.__useragents:
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
            if not self.__ignored:
                ignored = filesystem.read(self.__config.get('ignored'))
                for item in ignored:
                    item = item.replace("\n", "").strip()
                    if not item:
                        continue
                    if item.startswith('/'):
                        item = item.strip('/')
                    if item:
                        self.__ignored.append(item)

            return self.__ignored

        except (TypeError, FileSystemError) as error:
            raise ReaderError(error)

    def get_proxies(self):
        """
        Get a proxy list
        :raise ReaderError
        :return: list
        """

        try:
            if False is self.__browser_config.get('is_standalone_proxy'):
                if True is self.__browser_config.get('is_external_torlist'):
                    self.__proxies = filesystem.read(self.__browser_config.get('torlist'))
                elif not self.__proxies:
                    self.__proxies = filesystem.read(self.__config.get('proxies'))
                return self.__proxies
            return []

        except (TypeError, FileSystemError) as error:
            raise ReaderError(error)

    def get_lines(self, params, loader):
        """
        Read lines from large file
        :param dict params: input params
        :param funct loader: callback function
        :raise ReaderError
        :return: None
        """

        try:
            dirlist = self._get_dirlist_path()
            list_type = self.__browser_config.get('list')
            line_handler = getattr(self, '_{0}__line'.format(list_type))

            prepared_params = dict(params)
            scheme = prepared_params.get('scheme')
            port_suffix = self._format_port(prepared_params.get('port'))

            if 'directories' == list_type:
                prepared_params['prefix'] = self.__browser_config.get('prefix', '')
                prepared_params['base_url'] = scheme + prepared_params.get('host') + port_suffix + '/'
            elif 'subdomains' == list_type:
                host = prepared_params.get('host')
                if host.startswith('www.'):
                    host = host[4:]
                prepared_params['host_no_www'] = host
                prepared_params['port_suffix'] = port_suffix

            filesystem.readline(
                dirlist,
                handler=line_handler,
                handler_params=prepared_params,
                loader=loader,
            )
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

        host = params.get('host_no_www')
        if host is None:
            host = params.get('host')
            if 'www.' in host:
                host = host.replace("www.", "")

        port = params.get('port_suffix')
        if port is None:
            port = cls._format_port(params.get('port'))

        return params.get('scheme') + line + '.' + host + port

    def _directories__line(self, line, params):
        """
        Read lines from directories file
        :param str line: single line
        :param dict params: input params
        :return: str
        """

        line = helper.filter_directory_string(line)

        prefix = params.get('prefix')
        if prefix is None:
            prefix = self.__browser_config.get('prefix', '')

        if prefix:
            line = prefix + line

        base_url = params.get('base_url')
        if base_url is None:
            port = self._format_port(params.get('port'))
            base_url = params.get('scheme') + params.get('host') + port + '/'

        return base_url + line

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
        Filter list by multiple extensions.

        Fast in-memory path retained intentionally because the fully streaming
        variant reduced memory significantly but caused unacceptable runtime
        regression in benchmark measurements.

        :param str target: target list
        :param str output: output list
        :param list extensions: filtered extensions
        :return: None
        """

        try:
            target_file = self.__config.get(target)
            output_file = self.__config.get(output)

            dirlist = filesystem.read(target_file)
            dirlist = [item.strip() for item in dirlist]
            pattern = self._build_include_extension_pattern(extensions)
            newlist = filesystem.filter_file_lines(dirlist, pattern)
            filesystem.makefile(output_file)
            filesystem.writelist(output_file, newlist, '\n')
            self.__counter = len(newlist)

        except (CoreSystemError, FileSystemError) as error:
            raise ReaderError(error)

    def filter_by_ignore_extension(self, target, output, extensions):
        """
        Specific filter for selected extensions.

        Fast in-memory path retained intentionally because the fully streaming
        variant reduced memory significantly but caused unacceptable runtime
        regression in benchmark measurements.

        :param str target: target list
        :param str output: output list
        :param list extensions: filtered extensions
        :return: None
        """

        try:
            target_file = self.__config.get(target)
            output_file = self.__config.get(output)
            dirlist = filesystem.read(target_file)
            dirlist = [item.strip() for item in dirlist]
            pattern = self._build_ignore_extension_pattern(extensions)
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
                if True is self.__browser_config.get('use_random'):
                    dirlist = self.__config.get('tmplist')
                else:
                    dirlist = self._get_dirlist_path()
                self.__counter = filesystem.count_lines(dirlist)

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