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


class Config:
    """Config class"""

    DEFAULT_SOCKET_TIMEOUT = 10
    DEFAULT_MIN_THREADS = 1
    DEFAULT_MAX_THREADS = 15
    DEFAULT_DEBUG_LEVEL = 0
    DEFAULT_HTTP_METHOD = 'HEAD'
    DEFAULT_USER_AGENT = 'Opera/9.0 (Windows NT 5.1; U; en)'
    DEFAULT_SOURCE_DETECT_MIN_SIZE = 1000000
    DEFAULT_HTTP_SUCCESS_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    DEFAULT_HTTP_REDIRECT_STATUSES = [301, 302, 303, 304, 307, 308]
    DEFAULT_HTTP_FAILED_STATUSES = [404, 429, 500, 501, 502, 503, 504]
    DEFAULT_HTTP_UNRESOLVED_STATUSES = [401, 403]
    DEFAULT_HTTP_BAD_REQUEST_STATUSES = [400]

    def __init__(self, params):
        """
        Read filtered input params
        :param params:
        """

        self._default_scan = 'directories'
        self._scan = params.get('scan')
        self._scheme = params.get('scheme')
        self._ssl = params.get('ssl')
        self._host = params.get('host')
        self._accept_cookies = False if params.get('accept_cookies') is None else True
        self._port = params.get('port')
        self._is_indexof = params.get('indexof')
        self._retries = False if params.get('retries') is None else params.get('retries')
        self._method = params.get('method') if params.get('indexof') is None else 'GET'
        self._delay = params.get('delay')
        self._timeout = params.get('timeout')
        self._debug = self.DEFAULT_DEBUG_LEVEL if params.get('debug') is None else params.get('debug')
        self._is_proxy = params.get('tor')
        self._is_random_user_agent = params.get('random_agent')
        self._is_random_list = params.get('random_list')
        self._user_agent = self.DEFAULT_USER_AGENT
        self._threads = self.DEFAULT_MIN_THREADS if params.get('threads') is None else params.get('threads')

    @property
    def default_scan(self):
        return self._default_scan

    @property
    def scan(self):
        return self._scan

    @property
    def scheme(self):
        return self._scheme

    @property
    def ssl(self):
        return self._ssl

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def is_indexof(self):
        return self._is_indexof

    @property
    def method(self):
        return self._method

    @property
    def delay(self):
        return self._delay

    @property
    def timeout(self):
        return self._timeout

    @property
    def retries(self):
        return self._retries

    @property
    def debug(self):
        return self._debug

    @property
    def is_proxy(self):
        return self._is_proxy

    @property
    def is_random_user_agent(self):
        return self._is_random_user_agent

    @property
    def is_random_list(self):
        return self._is_random_list

    @property
    def user_agent(self):
        return self._user_agent

    @property
    def threads(self):
        return self._threads

    @property
    def accept_cookies(self):
        return self._accept_cookies
