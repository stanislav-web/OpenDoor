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


class Config(object):

    """Config class"""

    DEFAULT_SOCKET_TIMEOUT = 10
    DEFAULT_MIN_THREADS = 1
    DEFAULT_MAX_THREADS = 25
    DEFAULT_DEBUG_LEVEL = 1
    DEFAULT_REPORT = 'std'
    DEFAULT_SCAN = 'directories'
    SUBDOMAINS_SCAN = 'subdomains'
    DEFAULT_SCHEME = 'http://'
    DEFAULT_HTTP_PORT = 80
    DEFAULT_SSL_PORT = 443
    DEFAULT_HTTP_METHOD = 'HEAD'
    DEFAULT_USER_AGENT = 'PostmanRuntime/7.29.0'

    def __init__(self, params):
        """
        Read filtered input params.

        :param dict params: input cli arguments
        """

        self._scan = params.get('scan')
        self._scheme = self.DEFAULT_SCHEME if params.get('scheme') is None else params.get('scheme')
        self._ssl = params.get('ssl')
        self._host = params.get('host')
        self._proxy = '' if params.get('proxy') is None else params.get('proxy')
        self._headers = params.get('header')
        self._cookies = params.get('cookie')
        self._accept_cookies = params.get('accept_cookies') is not None
        self._keep_alive = params.get('keep_alive') is not None
        self._port = params.get('port')
        self._wordlist = params.get('wordlist')
        self._reports_dir = params.get('reports_dir')
        self._prefix = '' if params.get('prefix') is None else params.get('prefix')
        self._reports = self._normalize_csv(params.get('reports'))
        self._extensions = self._normalize_csv(params.get('extensions'))
        self._ignore_extensions = self._normalize_csv(params.get('ignore_extensions'))
        self._is_recursive = params.get('recursive') is True
        self._recursive_depth = 1 if params.get('recursive_depth') is None else int(params.get('recursive_depth'))
        self._recursive_status = self._normalize_csv(params.get('recursive_status'))
        self._recursive_exclude = self._normalize_csv(params.get('recursive_exclude'))
        self._retries = False if params.get('retries') is None else params.get('retries')
        self._method = params.get('method')
        self._delay = params.get('delay')
        self._timeout = self.DEFAULT_SOCKET_TIMEOUT if params.get('timeout') is None else float(params.get('timeout'))
        self._debug = self.DEFAULT_DEBUG_LEVEL if params.get('debug') is None else params.get('debug')
        self._is_tor = params.get('tor')
        self._torlist = '' if 'torlist' not in params or params.get('torlist') is None else params.get('torlist')
        self._is_random_user_agent = params.get('random_agent')
        self._sniff = self._normalize_csv(params.get('sniff'))
        self._is_random_list = params.get('random_list') is not None
        self._is_extension_filter = params.get('extensions') is not None
        self._is_ignore_extension_filter = params.get('ignore_extensions') is not None
        self._user_agent = self.DEFAULT_USER_AGENT
        self._threads = self.DEFAULT_MIN_THREADS if params.get('threads') is None else params.get('threads')

    @staticmethod
    def _normalize_csv(value):
        """
        Normalize comma separated values into a list.

        :param value:
        :return: list | None
        """

        if value is None:
            return None
        if isinstance(value, list):
            return value
        return [item.strip() for item in str(value).split(',') if item.strip()]

    @property
    def scan(self):
        """Scan property."""

        return self.DEFAULT_SCAN if self._scan is None else self._scan

    @scan.setter
    def scan(self, value):
        """scan param setter."""

        self._scan = value

    @property
    def scheme(self):
        """Protocol property."""

        return self._scheme

    @property
    def is_ssl(self):
        """If using ssl."""

        return self._ssl

    @property
    def prefix(self):
        """Paths prefix."""

        return self._prefix.lstrip('/')

    @property
    def host(self):
        """Hostname property."""

        return self._host

    @property
    def port(self):
        """Port property."""

        if self._ssl is True and self._port == self.DEFAULT_HTTP_PORT:
            self._port = self.DEFAULT_SSL_PORT
        return self._port

    @property
    def method(self):
        """Scan method property."""

        if self.is_sniff is True:
            if len(self.sniffers) == 1 and self.sniffers[0] == 'file':
                return 'HEAD'
            return 'GET'
        return self.DEFAULT_HTTP_METHOD if self._method is None else self._method

    @property
    def delay(self):
        """Delay property."""

        if self._delay is None:
            self._delay = 0
        elif self._delay >= 1:
            self._delay = int(self._delay)
        return self._delay

    @property
    def timeout(self):
        """Timeout property."""

        return self._timeout

    @timeout.setter
    def timeout(self, value):
        """Timeout param setter."""

        self._timeout = float(value)
        return self._timeout

    @property
    def retries(self):
        """Retries property."""

        return self._retries

    @property
    def debug(self):
        """Debug level property."""

        return self._debug

    @property
    def proxy(self):
        """Standalone proxy property."""

        return self._proxy

    @property
    def is_proxy(self):
        """If proxy is available."""

        if self._is_tor is True:
            return True
        if self._torlist is not None and len(self._torlist) > 0:
            return True
        if self._proxy is not None and len(self._proxy) > 0:
            return True
        return False

    @property
    def is_random_user_agent(self):
        """If ua randomizing is available."""

        return self._is_random_user_agent

    @property
    def is_sniff(self):
        """If sniffers are available."""

        return self._sniff is not None and len(self._sniff) > 0

    @property
    def sniffers(self):
        """Get sniffers."""

        return self._sniff

    @property
    def is_random_list(self):
        """If scan lists randomize and are available."""

        return self._is_random_list

    @property
    def is_extension_filter(self):
        """If scan list filtered by extensions."""

        return self._is_extension_filter

    @property
    def is_ignore_extension_filter(self):
        """If a scan list filtered by ignore extensions."""

        return self._is_ignore_extension_filter

    @property
    def is_standalone_proxy(self):
        """If standalone proxy is available."""

        if self.is_proxy is True and len(self._proxy) > 0:
            self._torlist = ''
            return True
        return False

    @property
    def is_internal_torlist(self):
        """If internal torlist is available."""

        return self._is_tor is True and len(self._torlist) <= 0

    @property
    def is_external_torlist(self):
        """If external torlist is available."""

        return self._torlist is not None and len(self._torlist) > 0

    @property
    def torlist(self):
        """Torlist property."""

        return self._torlist

    @property
    def is_external_wordlist(self):
        """If external word list is available."""

        return self._wordlist is not None

    @property
    def is_external_reports_dir(self):
        """If external reports directory selected."""

        return self._reports_dir is not None

    @property
    def reports_dir(self):
        """Get reports dir."""

        return self._reports_dir

    @property
    def wordlist(self):
        """Get external wordlist."""

        return self._wordlist

    @property
    def extensions(self):
        """Extensions resolver."""

        return self._extensions

    @property
    def ignore_extensions(self):
        """Ignore extensions resolver."""

        return self._ignore_extensions

    @property
    def is_recursive(self):
        """If recursive scan is enabled."""

        return self._is_recursive

    @property
    def recursive_depth(self):
        """Maximum recursive scan depth."""

        return self._recursive_depth

    @property
    def recursive_status(self):
        """Statuses allowed for recursive expansion."""

        return [] if self._recursive_status is None else [str(item).strip() for item in self._recursive_status if str(item).strip()]

    @property
    def recursive_exclude(self):
        """Extensions excluded from recursive expansion."""

        if self._recursive_exclude is None:
            return []

        return [
            str(item).strip().lstrip('.').lower()
            for item in self._recursive_exclude
            if str(item).strip()
        ]

    @property
    def reports(self):
        """Reports resolver."""

        reports = [] if self._reports is None else list(self._reports)
        if self.DEFAULT_REPORT not in reports:
            reports.append(self.DEFAULT_REPORT)
        return reports

    @property
    def user_agent(self):
        """User agent property."""

        return self._user_agent

    def set_threads(self, threads):
        """Threads setter."""

        self._threads = threads

    @property
    def threads(self):
        """Threads property."""

        return self._threads

    @property
    def headers(self):
        """Custom request headers."""

        return [] if self._headers is None else [str(item).strip() for item in self._headers if str(item).strip()]

    @property
    def cookies(self):
        """Custom request cookies."""

        return [] if self._cookies is None else [str(item).strip() for item in self._cookies if str(item).strip()]

    @property
    def accept_cookies(self):
        """Accept cookies property."""

        return self._accept_cookies

    @property
    def keep_alive(self):
        """If connection keep-alive."""

        return self._keep_alive