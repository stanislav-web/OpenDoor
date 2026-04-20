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

import os

from .provider import PluginProvider
from src.core import CoreConfig
from src.core import filesystem, FileSystemError
from json2html.jsonconv import Json2Html


class HtmlReportPlugin(PluginProvider):
    """ HtmlReportPlugin class"""

    PLUGIN_NAME = 'HtmlReport'
    EXTENSION_SET = '.html'

    def __init__(self, target, data, directory=None):
        """
        PluginProvider constructor
        :param str target: target host
        :param dict data: result set
        :param str directory: custom directory
        """

        PluginProvider.__init__(self, target, data)

        try:

            if None is directory:
                directory = CoreConfig.get('data').get('reports')
            self.__target_dir = filesystem.makedir(os.path.join(directory, self._target))
        except FileSystemError as error:
            raise Exception(error)

    def process(self):
        """
        Process data
        :return: str
        """

        try:
            filesystem.clear(self.__target_dir, extension=self.EXTENSION_SET)
            report_data = dict(self._data)
            report_data['report_items'] = {
                status: self.get_report_items(status)
                for status in self._data.get('items', {}).keys()
            }
            resultset = Json2Html().convert(json=report_data, table_attributes='border="1" cellpadding="2"')
            self.record(self.__target_dir, self._target, resultset)
        except FileSystemError as error:
            raise Exception(error)