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
from src.core import filesystem , FileSystemError
from src.lib import tpl
from json2html.jsonconv import Json2Html

class HtmlReportPlugin(PluginProvider):
    """ HtmlReportPlugin class"""

    PLUGIN_NAME = 'HtmlReport'
    EXTENSION_SET = '.html'

    def __init__(self, taget, data):
        """
        PluginProvider constructor
        :param str taget: target host
        :param dict data: result set
        """

        PluginProvider.__init__(self, taget, data)

        try:
            config = filesystem.readcfg('setup.cfg')
            directory = config.get('opendoor', 'reports')
            self.__target_dir = "".join((directory, self._target))
            filesystem.makedir(self.__target_dir)
        except FileSystemError as e:
            raise Exception(e)

    def process(self):
        """
        Process data
        :return: str
        """

        try:
            filesystem.clear(self.__target_dir, extension=self.EXTENSION_SET)
            filename = "".join((self.__target_dir, filesystem.sep, self._target, self.EXTENSION_SET))
            filesystem.makefile(filename)
            resultset = Json2Html().convert(json=self._data, table_attributes='border="1" cellpadding="2"')
            filesystem.writelist(filename, resultset)
            tpl.info(key='report', plugin=self.PLUGIN_NAME, dest=filesystem.getabsname(filename))

        except FileSystemError as e:
            raise Exception(e)

