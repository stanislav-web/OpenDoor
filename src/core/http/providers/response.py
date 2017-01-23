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


class ResponseProvider():
    """ ResponseProvider class"""

    def __init__(self, config, tpl):
        """

        :param dict config: configurations
        :param tpl: templater interface
        """

        self._config = config
        self._tpl = tpl


    def handle(self, resp, request_url, pool_size, total_size):
        """
        Handle response
        :param urllib3.response.HTTPResponse response: response object
        :param str request_url: url from request
        :param int pool_size: response object
        :param int total_size: response object
        :return: @TODO
        """

        pass
