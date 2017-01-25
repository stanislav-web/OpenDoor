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
from src.core import filesystem

class ResponseProvider():
    """ ResponseProvider class"""

    __DEFAULT_SOURCE_DETECT_MIN_SIZE = 1000000
    __DEFAULT_HTTP_SUCCESS_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    __DEFAULT_HTTP_REDIRECT_STATUSES = [301, 302, 303, 304, 307, 308]
    __DEFAULT_HTTP_FAILED_STATUSES = [404, 429, 500, 501, 502, 503, 504]
    __DEFAULT_HTTP_UNRESOLVED_STATUSES = [401, 403]
    __DEFAULT_HTTP_BAD_REQUEST_STATUSES = [400]

    def __init__(self, config, tpl):
        """
        Response instance
        :param src.lib.browser.config.Config config: configurations
        :param src.lib.tpl.tpl.Tpl tpl: templater
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
        print resp, request_url, pool_size, total_size
        pass

    def _get_content_size(self, response):
        """
        Get content size

        :param urllib3.response.HTTPResponse response: response object
        :return: str
        """

        if 'Content-Length' in response.headers:
            return filesystem.human_size(response.headers['Content-Length'])
        return '0B'

    def _sucess(self):
        """
        Handle success response
        :return: @TODO
        """
        pass

    def _failed(self):
        """
        Handle failed response
        :return: @TODO
        """
        pass

    def _redirect(self):
        """
        Handle redirect response
        :return: @TODO
        """
        pass

    def _unresolved(self):
        """
        Handle unresolved response
        :return: @TODO
        """
        pass

    def _bad(self):
        """
        Handle bad response
        :return: @TODO
        """
        pass