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

from src.core import helper


class ResponsePluginProvider(object):
    """"ResponsePluginProvider class"""

    def __init__(self):
        """
        PluginProvider constructor
        """
        self._status = 0
        self._headers = {}
        self._body = ''

    def __set_body(self, body):
        """
        Set response data
        :param str body: response data
        :return: None
        """

        if False is isinstance(body, str):
            self._body = helper.decode(body)

    def process(self, response):
        """
        Process data
        :param urllib3.response.HTTPResponse response: response object
        :return: str
        """

        self._status = int(float(response.status))
        self._headers = response.headers
        self.__set_body(response.data)

        pass
