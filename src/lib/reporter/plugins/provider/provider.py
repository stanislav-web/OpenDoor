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

from src.core import filesystem, FileSystemError
from src.lib import tpl


class PluginProvider(object):
    """"PluginProvider class"""
    
    CONFIG_FILE = 'setup.cfg'
    PLUGIN_NAME = 'PluginProvider'
    EXTENSION_SET = '.pp'
    
    def __init__(self, taget, data):
        """
        PluginProvider constructor
        :param str taget: target host
        :param dict data: result set
        """

        self._target = str(taget)
        self._data = {}
        self.__set_data(data)

    def __set_data(self, data):
        """
        Set report data
        :param dict data: report data
        :return:
        """

        if False is isinstance(data, dict):
            raise TypeError("Report data has a wrong type")
        self._data = data

    def process(self):
        """
        Process data
        :return: mixed
        """

        pass
    
    @classmethod
    def record(cls, dirname, filename, resultset, separator=''):
        """
        Record data process
        :param str dirname: report directory
        :param str filename: report filename
        :param list resultset: report result
        :param str separator: result separator
        :raise Exception
        :return: None
        """
        
        try:
            filename = "".join((dirname, filesystem.sep, filename, cls.EXTENSION_SET))
            filesystem.makefile(filename)
            filesystem.writelist(filename, resultset, separator)
            tpl.info(key='report', plugin=cls.PLUGIN_NAME, dest=filesystem.getabsname(filename))
        except FileSystemError as error:
            raise Exception(error)
