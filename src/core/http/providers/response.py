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

import re

from src.core import filesystem
from src.core import helper


class ResponseProvider(object):
    """ ResponseProvider class"""

    HTTP_DBG_LEVEL = 3
    INDEX_OF_TITLE = 'Index of /'
    DEFAULT_SOURCE_DETECT_MIN_SIZE = 1000000
    DEFAULT_HTTP_SUCCESS_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    DEFAULT_HTTP_REDIRECT_STATUSES = [301, 302, 303, 304, 307, 308]
    DEFAULT_HTTP_FAILED_STATUSES = [404, 406, 429, 500, 501, 502, 503, 504]
    DEFAULT_HTTP_FORBIDDEN_STATUSES = [401, 403]
    DEFAULT_HTTP_BAD_REQUEST_STATUSES = [400]

    def __init__(self, config):
        """
        Response instance
        :param src.lib.browser.config.Config config: configurations
        """
        
        self._cfg = config

    @property
    def is_indexof(self):
        """
        Check response as index of/ page
        :return: bool
        """

        regex = re.compile('<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)
        title = regex.search(self.INDEX_OF_TITLE)
        if None is not title:
            return True
        return False

    @classmethod
    def _get_redirect_url(cls, url, response):
        """
        Get redirect url
        :param str url:
        :param urllib3.response.HTTPResponse response:
        :return: str
        """

        redirect_url = None
        location = response.get_redirect_location()

        if location is not False:
            matches = re.search("(?P<url>https?://[^\s]+)", location)
            if matches.group("url") is not None:
                redirect_url = matches.group("url")
            else:
                urlp = helper.parse_url(url)
                redirect_url = urlp.scheme + '://' + urlp.netloc + location

        return redirect_url

    def detect(self, request_url, response):
        """
        Detect response by status code
        :param str request_url: request url
        :param urllib3.response.HTTPResponse response:
        :raise Exception
        :return: str
        """

        if response.status in self.DEFAULT_HTTP_SUCCESS_STATUSES:
            if 'Content-Length' in response.headers:
                if self.DEFAULT_SOURCE_DETECT_MIN_SIZE <= int(response.headers['Content-Length']):
                    return 'file'
                if True is self._cfg.is_indexof:
                    if True is self.is_indexof:
                        return 'indexof'
            return 'success'
        elif response.status in self.DEFAULT_HTTP_FAILED_STATUSES:
            return 'failed'
        elif response.status in self.DEFAULT_HTTP_REDIRECT_STATUSES:
            if  response.get_redirect_location() is not False:
                urlfrag = helper.parse_url(request_url)
                redirect_url = response.get_redirect_location().rstrip('/')

                redirectfrag = helper.parse_url(redirect_url)
                url = "{0}://{1}".format(urlfrag.scheme, urlfrag.netloc)

                if url == redirect_url or redirectfrag.query in urlfrag.path:
                    return 'failed'
            return 'redirect'
        elif response.status in self.DEFAULT_HTTP_BAD_REQUEST_STATUSES:
            return 'bad'
        elif response.status in self.DEFAULT_HTTP_FORBIDDEN_STATUSES:
            return 'forbidden'
        else:
            raise Exception('Unknown response status : `{0}`'.format(response.status))

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

    @staticmethod
    def _get_content_size(response):
        """
        Get content size

        :param urllib3.response.HTTPResponse response: response object
        :return: str
        """

        if 'Content-Length' in response.headers:
            return filesystem.human_size(response.headers['Content-Length'], 0)
        return '0B'
