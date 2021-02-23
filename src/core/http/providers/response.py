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

import re
from src.core import filesystem
from src.core import helper


class ResponseProvider(object):
    """ ResponseProvider class"""

    HTTP_DBG_LEVEL = 3
    DEFAULT_HTTP_SUCCESS_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    DEFAULT_HTTP_REDIRECT_STATUSES = [300, 301, 302, 303, 304, 307, 308]
    DEFAULT_HTTP_FAILED_STATUSES = [404, 406, 410, 409, 412, 424, 429, 440, 500, 501, 502, 503, 504, 520, 522]
    DEFAULT_SSL_CERT_REQUIRED_STATUSES = [423, 496]
    DEFAULT_HTTP_FORBIDDEN_STATUSES = [403,405]
    DEFAULT_HTTP_AUTH_STATUSES = [401]
    DEFAULT_HTTP_BAD_REQUEST_STATUSES = [400, 415, 508]

    def __init__(self, config):
        """
        Response instance
        :param src.lib.browser.config.Config config: configurations
        """

        self._cfg = config
        self._response_plugins = []

    @classmethod
    def _get_redirect_url(cls, url, response):
        """
        Get redirect url
        :param str url: redirect url
        :param urllib3.response.HTTPResponse response: response object
        :return: str
        """

        redirect_url = None
        location = response.get_redirect_location()

        if location is not False:
            matches = re.search("(?P<url>https?://[^\s]+)", location)
            if matches is not None:
                redirect_url = matches.group("url")
            else:
                urlp = helper.parse_url(url)
                location = location if True is location.startswith('/') else ''.join(('/', location))
                redirect_url = urlp.scheme + '://' + urlp.netloc + location

        return redirect_url

    def detect(self, request_url, response):
        """
        Detect response by status code
        :param str request_url: request url
        :param urllib3.response.HTTPResponse response: response object
        :raise Exception
        :return: str
        """

        status = None
        for _, resp_plugin in enumerate(self._response_plugins):
            status = resp_plugin.process(response)
            if None is not status:
                break

        if None is status:
            if response.status in self.DEFAULT_HTTP_SUCCESS_STATUSES:
                return 'success'
            elif response.status in self.DEFAULT_HTTP_FAILED_STATUSES:
                return 'failed'
            elif response.status in self.DEFAULT_SSL_CERT_REQUIRED_STATUSES:
                return 'certificat'
            elif response.status in self.DEFAULT_HTTP_REDIRECT_STATUSES:
                return self.__is_redirect(response, request_url)
            elif response.status in self.DEFAULT_HTTP_BAD_REQUEST_STATUSES:
                return 'bad'
            elif response.status in self.DEFAULT_HTTP_FORBIDDEN_STATUSES:
                return 'forbidden'
            elif response.status in self.DEFAULT_HTTP_AUTH_STATUSES:
                return 'auth'
            else:
                raise Exception('Unknown response status : `{0}`'.format(response.status))
        else:
            return status

    def handle(self, response, request_url, items_size, total_size, ignore_list):
        """
        Response handler
        :param urllib3.response.HTTPResponse response: response object
        :param str request_url: url from request
        :param int items_size: current items sizes
        :param int total_size: response object
        :param list ignore_list: ignore list
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
        size = 0

        try:
            size = 0 if not hasattr(response, 'headers') else int(response.headers['Content-Length'])
        except (KeyError, ValueError):
            size = len(response.data)
        finally:
            size = filesystem.human_size(size, 0)
        return size

    @staticmethod
    def __is_redirect(response, request_url):
        """
        Return redirect status
        :param str request_url: request url
        :param urllib3.response.HTTPResponse response: response object
        :return: str
        """

        location = response.get_redirect_location()
        if location is not False and location is not None:
            urlfrag = helper.parse_url(request_url)
            redirect_url = location.rstrip('/')

            redirectfrag = helper.parse_url(redirect_url)
            url = "{0}://{1}".format(urlfrag.scheme, urlfrag.netloc)
            if url == redirect_url \
                    or (0 < len(redirectfrag.query) and redirectfrag.query in urlfrag.path):
                return 'failed'
            return 'redirect'
        else:
            return 'failed'
