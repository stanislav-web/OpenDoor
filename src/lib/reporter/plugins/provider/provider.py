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


class PluginProvider(object):
    """"PluginProvider class"""

    def __init__(self, data):
        """
        PluginProvider constructor
        :return: None
        """

        self._data = {}
        self.__set_data(data)
        pass

    def __set_data(self, data):
        """
        Set report data

        :param dict data: report data
        :return:
        """

        if False is isinstance(data, dict):
            raise TypeError("Report data has a wrong type")
        self._data = data

        pass

    def process(self):
        """
        Process data
        :return: mixed
        """

        pass
