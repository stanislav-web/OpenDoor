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


class Config(object):

    """Config class"""

    DEFAULT_SOCKET_TIMEOUT = 10
    DEFAULT_MIN_THREADS = 1
    DEFAULT_MAX_THREADS = 25
    DEFAULT_DEBUG_LEVEL = 0
    DEFAULT_REPORT = 'std'
    DEFAULT_SCAN = 'directories'
    DEFAULT_SCHEME = 'http://'
    DEFAULT_HTTP_PORT = 80
    DEFAULT_SSL_PORT = 443
    DEFAULT_HTTP_METHOD = 'HEAD'
    DEFAULT_USER_AGENT = 'Opera/9.0 (Windows NT 5.1; U; en)'

    def __init__(self, params):
        """
        Read filtered input params
        :param dict params: input cli arguments
        """

        self._scan = params.get('scan') if params.get('wordlist') is None else params.get('wordlist')
        self._scheme = self.DEFAULT_SCHEME if params.get('scheme') is None else params.get('scheme')
        self._ssl = params.get('ssl')
        self._host = params.get('host')
        self._proxy = '' if params.get('proxy') is None else params.get('proxy')
        self._accept_cookies = False if params.get('accept_cookies') is None else True
        self._port = params.get('port')
        self._wordlist = params.get('wordlist')
        self._reports_dir = params.get('reports_dir')
        self._prefix = "" if params.get('prefix') is None else params.get('prefix')
        self._reports = params.get('reports')
        self._extensions = params.get('extensions')
        self._is_indexof = params.get('indexof')
        self._retries = False if params.get('retries') is None else params.get('retries')
        self._method = params.get('method') if params.get('indexof') is None else 'GET'
        self._delay = params.get('delay')
        self._timeout = params.get('timeout')
        self._debug = self.DEFAULT_DEBUG_LEVEL if params.get('debug') is None else params.get('debug')
        self._is_tor = params.get('tor')
        self._torlist = '' if 'torlist' not in params else params.get('torlist')
        self._is_random_user_agent = params.get('random_agent')
        self._is_random_list = False if params.get('random_list') is None else True
        self._is_extension_filter = False if params.get('extensions') is None else True
        self._user_agent = self.DEFAULT_USER_AGENT
        self._threads = self.DEFAULT_MIN_THREADS if params.get('threads') is None else params.get('threads')
        
    @property
    def scan(self):
        """
        Scan property
        :return: str
        """
        
        return self.DEFAULT_SCAN if self._scan is None else self._scan

    @property
    def scheme(self):
        """
        Protocol property
        :return: str
        """

        return self._scheme

    @property
    def is_ssl(self):
        """
        If using ssl
        :return: bool
        """

        return self._ssl

    @property
    def prefix(self):
        """
        Paths prefix
        :return: str
        """

        return self._prefix.lstrip("/")

    @property
    def host(self):
        """
        Hostname property
        :return: str
        """

        return self._host

    @property
    def port(self):
        """
        Port property
        :return: int
        """
        
        if True is self._ssl and self._port is self.DEFAULT_HTTP_PORT:
            self._port = self.DEFAULT_SSL_PORT
        return self._port

    @property
    def is_indexof(self):
        """
        If index of/ scan is available
        :return: bool
        """

        return self._is_indexof

    @property
    def method(self):
        """
        Scan method property
        :return: str
        """

        return self.DEFAULT_HTTP_METHOD if self._method is None else self._method

    @property
    def delay(self):
        """
        Delay property
        :return: int
        """

        if None is self._delay:
            self._delay = 0
        elif 1 <= self._delay:
            self._delay = int(self._delay)

        return self._delay

    @property
    def timeout(self):
        """
        Timeout property
        :return: int
        """

        return self._timeout

    @property
    def retries(self):
        """
        Retries property
        :return: int
        """

        return self._retries

    @property
    def debug(self):
        """
         Debug level property
         :return: int
         """

        return self._debug

    @property
    def proxy(self):
        """
        Standalone proxy property
        :return: bool
        """

        return self._proxy

    @property
    def is_proxy(self):
        """
        If proxy is available
        :return: bool
        """

        if True is self._is_tor:
            return True
        elif None is not self._torlist and 0 < len(self._torlist):
            return True
        elif None is not self._torlist and 0 < len(self._proxy):
            return True

        return False

    @property
    def is_random_user_agent(self):
        """
        If ua randomize and is available
        :return: bool
        """

        return self._is_random_user_agent

    @property
    def is_random_list(self):
        """
        If scan list randomize and is available
        :return: bool
        """

        return self._is_random_list

    @property
    def is_extension_filter(self):
        """
        If scan list filtered by extensions
        :return: bool
        """

        return self._is_extension_filter

    @property
    def is_standalone_proxy(self):
        """
        If standalone proxy is available
        :return: bool
        """

        if True is self.is_proxy and 0 < len(self._proxy):
            self._torlist = ''

            return True
        return False

    @property
    def is_internal_torlist(self):
        """
        If internal torlist is available
        :return: bool
        """

        if True is self._is_tor and 0 >= len(self._torlist):
            return True
        return False

    @property
    def is_external_torlist(self):
        """
        If external torlist is available
        :return: bool
        """

        if None is not self._torlist and 0 < len(self._torlist):
            return True
        return False

    @property
    def torlist(self):
        """
        Torlist property
        :return: bool
        """

        return self._torlist

    @property
    def is_external_wordlist(self):
        """
        If exteranl word list is available
        :return: bool
        """

        if None is self._wordlist:
            return False
        return True

    @property
    def is_external_reports_dir(self):
        """
        If exteranl reports directory selected
        :return: bool
        """

        if None is self._reports_dir:
            return False
        return True

    @property
    def reports_dir(self):
        """
        Get reports dir
        :return: str
        """

        return self._reports_dir

    @property
    def extensions(self):
        """
        Extensions resolver
        :return: list
        """

        if None is not self._extensions:
            self._extensions = self._extensions.split(",")
        return self._extensions

    @property
    def reports(self):
        """
        Reports resolver
        :return: list
        """

        reports = self._reports.split(",")
        if self.DEFAULT_REPORT not in reports:
            reports.append(self.DEFAULT_REPORT)
        return reports

    @property
    def user_agent(self):
        """
        User agent property
        :return: str
        """

        return self._user_agent

    def set_threads(self, threads):
        """
        Threads setter
        :param int threads: threads
        :return: int
        """

        self._threads = threads

    @property
    def threads(self):
        """
        Threads property
        :return: int
        """

        return self._threads

    @property
    def accept_cookies(self):
        """
        Accept cookies property
        :return: bool
        """

        return self._accept_cookies
