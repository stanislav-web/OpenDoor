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

from .provider import PluginProvider
from src.core import filesystem, FileSystemError


class TextReportPlugin(PluginProvider):
    """ TextReportPlugin class"""

    PLUGIN_NAME = 'TextReport'
    EXTENSION_SET = '.txt'

    def __init__(self, taget, data, directory=None):
        """
        PluginProvider constructor
        :param str taget: target host
        :param dict data: result set
        :param str directory: custom directory
        """
        
        PluginProvider.__init__(self, taget, data)

        try:
            if None is directory:
                config = filesystem.readcfg(self.CONFIG_FILE)
                directory = config.get('opendoor', 'reports')
            self.__target_dir = "".join((directory, self._target))
            filesystem.makedir(self.__target_dir)
        except FileSystemError as error:
            raise Exception(error)

    def process(self):
        """
        Process data
        :return: str
        """

        resultset = self._data.get('items').items()

        try:
            filesystem.clear(self.__target_dir, extension=self.EXTENSION_SET)

            for status, data in resultset:

                if status not in ['failed']:
                    self.record(self.__target_dir, status, data, '\n')
        except (Exception, FileSystemError) as error:
            raise Exception(error)
