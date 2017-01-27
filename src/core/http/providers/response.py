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

class ResponseProvider(object):
    """ ResponseProvider class"""

    _HTTP_DBG_LEVEL = 3
    __DEFAULT_SOURCE_DETECT_MIN_SIZE = 1000000
    __DEFAULT_HTTP_SUCCESS_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    __DEFAULT_HTTP_REDIRECT_STATUSES = [301, 302, 303, 304, 307, 308]
    __DEFAULT_HTTP_FAILED_STATUSES = [404, 429, 500, 501, 502, 503, 504]
    __DEFAULT_HTTP_FORBIDDEN_STATUSES = [401, 403]
    __DEFAULT_HTTP_BAD_REQUEST_STATUSES = [400]

    def __init__(self):
        """
        Response instance
        """

    def detect(self, status_code):
        """
        Detect response by status code
        :param int status_code: response status
        :return: str
        """

        if status_code in self.__DEFAULT_HTTP_SUCCESS_STATUSES:
            return 'sucess'
        elif status_code in self.__DEFAULT_HTTP_FAILED_STATUSES:
            return 'failed'
        elif status_code in self.__DEFAULT_HTTP_REDIRECT_STATUSES:
            return 'redirect'
        elif status_code in self.__DEFAULT_HTTP_BAD_REQUEST_STATUSES:
            return 'bad'
        elif status_code in self.__DEFAULT_HTTP_FORBIDDEN_STATUSES:
            return 'forbidden'
        else:
            raise Exception('Unknown response status : `{0}`'.format(status_code) )

    def handle(self, response, request_url, items_size, total_size):
        """
        Handle response
        :param urllib3.response.HTTPResponse response: response object
        :param str request_url: url from request
        :param int items_size: current items sizes
        :param int total_size: response object
        :raise ResponseError
        :return: dict
        """
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

    def _forbidden(self):
        """
        Handle forbidden response
        :return: @TODO
        """

        pass

    def _bad(self):
        """
        Handle bad response
        :return: @TODO
        """

        pass