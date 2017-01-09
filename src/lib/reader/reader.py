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

    Development Team: Stanislav Menshov
"""

from random import randrange
from .config import Config
from src.core import filesystem
from src.core import FileSystemError
from ...lib.exceptions import LibError

class Reader():

    """Reader class"""

    def __init__(self):

        self.__config =  self.__load_config()
        self.__useragents = []
        self.__proxies = []

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


    def _get_random_user_agent(self):
        """ get random user agent from user-agents list"""

        if not len(self.__useragents):
            self.__useragents = filesystem.read(self.__config.get('opendoor','useragents'))

        index = randrange(0, len(self.__useragents))
        return self.__useragents[index].strip()

    def _get_random_proxy(self):
        """ get random proxy from proxy list"""

        if not len(self.__proxies):
            self.__proxies = filesystem.read(self.__config.get('opendoor', 'proxies'))

        index = randrange(0, len(self.__proxies))
        return self.__proxies[index].strip()

    def _get_list(self, list, params, callback):
        """ read list """

        dirlist = self.__config.get('opendoor', list)
        filesystem.readliner(dirlist, resolver=getattr(self, '_{0}__line'.format(self._scan)),
                             params=params,
                             callback=callback)


    def _subdomains__line(self, line, params):
        """ resolve subdomains line"""

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

        return "{scheme}{sub}.{host}{port}".format(
            scheme=params.get('scheme'),
            host=host,
            port=port,
            sub=line,
        )

    def _directories__line(self, line, params):
        """ resolve directories line """

        line = line.strip("\n")
        line.lstrip('/')

        port = params.get('port')

        if Config.port is port:
            port = ''
        else:
            port = ':{0}'.format(port)

        return "{scheme}{host}{port}/{uri}".format(
            scheme=params.get('scheme'),
            host=params.get('host'),
            port=port,
            uri=line,
        )