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

    Development: Stanislav WEB
"""

import importlib
import random
import re
import sys
from urllib.parse import unquote, urlsplit, urlunsplit

from urllib3 import ProxyManager, Timeout, disable_warnings
from urllib3.util import make_headers
from urllib3.exceptions import DependencyWarning, MaxRetryError, ProxySchemeUnknown, ReadTimeoutError, InsecureRequestWarning

from src.core import helper
from .exceptions import ProxyRequestError
from .providers import DebugProvider
from .providers import RequestProvider


class Proxy(RequestProvider, DebugProvider):
    """Proxy class"""

    def __init__(self, config, debug, **kwargs):
        """
        Proxy instance
        :param src.lib.browser.config.Config config: global configurations
        :param DebugProvider debug: debugger
        """

        try:
            self.__tpl = kwargs.get('tpl')
            self.__proxylist = kwargs.get('proxy_list')
            RequestProvider.__init__(self, config, agent_list=kwargs.get('agent_list'))
            self.__headers = self._headers
            self.__connection_header = 'default'
            if True is config.keep_alive:
                self.__connection_header = self._keep_alive
            self.__server = None
            self.__pm = None
            self.__proxy_pools = {}
            self.__dead_proxies = set()
            self.__cfg = config
            self.__debug = debug
            self.__debug.debug_proxy_pool()

            if False is config.is_standalone_proxy and 0 == len(self.__proxylist):
                raise TypeError('Proxy list empty or has invalid format')

        except (TypeError, ValueError) as error:
            raise ProxyRequestError(error)

    @classmethod
    def __build_proxy_headers(cls, server):
        """
        Build proxy authentication headers for HTTP CONNECT proxies.

        urllib3 does not reliably convert user-info in proxy URLs into
        Proxy-Authorization for CONNECT tunnels, so authenticated HTTP proxies
        must receive explicit proxy headers.

        :param str server: normalized proxy server URL
        :return: dict
        """

        parsed = urlsplit(server)
        if not parsed.username or parsed.password is None:
            return {}

        credentials = '{0}:{1}'.format(unquote(parsed.username), unquote(parsed.password))
        return make_headers(proxy_basic_auth=credentials)

    @classmethod
    def __mask_proxy_server(cls, server):
        """
        Mask proxy credentials for logs and terminal diagnostics.

        :param str|None server: proxy server URL
        :return: str
        """

        if not server:
            return '-'

        try:
            parsed = urlsplit(server)
        except (TypeError, ValueError):
            return str(server)

        if not parsed.username and parsed.password is None:
            return server

        host = parsed.hostname or ''
        if ':' in host and not host.startswith('['):
            host = '[{0}]'.format(host)

        netloc = host
        if parsed.port is not None:
            netloc = '{0}:{1}'.format(netloc, parsed.port)

        username = unquote(parsed.username or '')
        if username:
            netloc = '{0}:*****@{1}'.format(username, netloc)
        else:
            netloc = '*****@{0}'.format(netloc)

        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))

    def __proxy_pool(self):
        """
        Create or reuse Proxy connection pool.

        :raise ProxyRequestError
        :return: urllib3.HTTPConnectionPool
        """

        try:
            server = self.__cfg.proxy if True is self.__cfg.is_standalone_proxy else self.__get_random_proxy()
            self.__server = self.__normalize_proxy_server(server)

            if True is not self.__cfg.is_standalone_proxy:
                getattr(self.__debug, 'debug_proxy_selected', lambda *args, **kwargs: True)(self.__server)

            if self.__server in self.__proxy_pools:
                return self.__proxy_pools[self.__server]

            if self.__get_proxy_type(self.__server) == 'socks':
                disable_warnings(InsecureRequestWarning)

                if self.__pm is None:
                    package_module = importlib.import_module('urllib3.contrib.socks')
                    self.__pm = getattr(package_module, 'SOCKSProxyManager')

                pool = self.__pm(
                    self.__server,
                    num_pools=self.__cfg.threads,
                    timeout=Timeout(connect=self.__cfg.timeout, read=self.__cfg.timeout),
                    block=True,
                )
            else:
                pool = ProxyManager(
                    self.__server,
                    num_pools=self.__cfg.threads,
                    proxy_headers=self.__build_proxy_headers(self.__server),
                    timeout=Timeout(connect=self.__cfg.timeout, read=self.__cfg.timeout),
                    block=True,
                )

            self.__proxy_pools[self.__server] = pool
            return pool
        except (DependencyWarning, ProxySchemeUnknown) as error:
            raise ProxyRequestError(error)
        except ImportError as error:
            if self.__server is not None and self.__get_proxy_type(self.__server) == 'socks':
                raise ProxyRequestError(
                    'SOCKS proxy support requires PySocks. Install dependencies with pip install -r requirements.txt'
                ) from error
            raise ProxyRequestError(error)

    def __debug_cookie_middleware(self, response):
        """Route response cookies and emit request-level cookie diagnostics."""

        if True is self.__cfg.accept_cookies:
            getattr(self.__debug, 'debug_cookie_accept_enabled', lambda *args, **kwargs: True)()

        self.cookies_middleware(is_accept=self.__cfg.accept_cookies, response=response)

        if True is self.__cfg.accept_cookies and True is self._is_cookie_fetched:
            getattr(self.__debug, 'debug_cookie_accepted', lambda *args, **kwargs: True)(self._push_cookies())

    def __is_directory_like_scan(self):
        """Return True for directory scans and their runtime filtered variants.

        ``--random-list`` combined with extension filters mutates config.scan to
        ``extensionlist`` or ``ignore_extensionlist`` before queue processing.
        These modes still execute target-path dictionary requests and must keep
        the same proxy timeout/retry diagnostics as the default directory scan.

        :return: whether current scan mode is directory-like
        :rtype: bool
        """

        return self.__cfg.scan in (self.__cfg.DEFAULT_SCAN, 'extensionlist', 'ignore_extensionlist')

    def request(self, url, extra_headers=None):
        """
        Client request using Proxy

        :param str url: request uri
        :param dict | list | tuple | None extra_headers: temporary per-request headers
        :return: urllib3.HTTPResponse
        """

        self.__headers.update({'User-Agent': self._user_agent})
        request_headers = self._build_request_headers(self.__headers, extra_headers)

        if self.__connection_header != 'default' and request_headers.get('Connection') is None:
            request_headers.update({'Connection': self.__connection_header})

        getattr(self.__debug, 'debug_cookie_attached', lambda *args, **kwargs: True)(request_headers)
        getattr(self.__debug, 'debug_request', lambda *args, **kwargs: True)(request_headers, url, self.__cfg.method)

        try:
            response = self.__pool_request(url, headers=request_headers)
            return response

        except MaxRetryError:
            if self.__is_directory_like_scan() is True:
                self.__finish_active_terminal_line()
                self.__tpl.warning(
                    key='proxy_max_retry_error',
                    url=helper.parse_url(url).path,
                    proxy=self.__mask_proxy_server(self.__server),
                )
                return self.__retry_after_max_retry(url, request_headers)

        except ReadTimeoutError:
            if self.__is_directory_like_scan() is True:
                self.__finish_active_terminal_line()
                self.__tpl.warning(key='read_timeout_error', url=helper.parse_url(url).path)

    def __retry_after_max_retry(self, url, request_headers):
        """
        Retry a proxy request once after MaxRetryError without leaking raw urllib3 tracebacks.

        :param str url: request uri
        :param dict request_headers: request headers
        :return: urllib3.HTTPResponse|None
        """

        try:
            return self.__pool_request(url, headers=request_headers)
        except MaxRetryError as error:
            self.__warn_proxy_retry_failed(url, error)
        except ReadTimeoutError as error:
            self.__warn_proxy_retry_failed(url, error)

        return None

    def __warn_proxy_retry_failed(self, url, error):
        """
        Emit a concise warning or fatal error when the one-shot proxy retry still fails.

        :param str url: request uri
        :param Exception error: retry failure
        :raise ProxyRequestError: when a standalone proxy is unavailable
        :return: None
        """

        message = 'Proxy {0} unavailable after retry for {1}: {2}'.format(
            self.__mask_proxy_server(self.__server),
            helper.parse_url(url).path,
            self.__format_proxy_error(error),
        )

        if True is self.__cfg.is_standalone_proxy:
            self.__tpl.error(msg=message)
            raise ProxyRequestError(message)

        self.__mark_proxy_dead(self.__server)
        self.__tpl.warning(msg=message)

    @staticmethod
    def __finish_active_terminal_line():
        """
        Move persistent warnings/errors to a clean line after rotating progress output.

        :return: None
        """

        try:
            sys.stdout.write('\n')
            sys.stdout.flush()
        except (AttributeError, OSError, ValueError):
            return

    @staticmethod
    def __format_proxy_error(error):
        """
        Format nested urllib3/PySocks errors for a compact terminal message.

        :param Exception error: proxy request error
        :return: str
        """

        message = str(getattr(error, 'reason', None) or error)
        message = re.sub(r'\s+', ' ', message).strip()

        lowered = message.lower()
        if 'connection refused' in lowered:
            return 'connection refused'
        if 'timed out' in lowered or 'timeout' in lowered:
            return 'connection timed out'
        if 'connection reset' in lowered:
            return 'connection reset'
        if 'name or service not known' in lowered or 'nodename nor servname' in lowered:
            return 'name resolution failed'

        max_length = 180
        if len(message) > max_length:
            return '{0}...'.format(message[:max_length - 3])

        return message

    def __pool_request(self, url, headers=None):
        """
        Shadow pool request

        :param string url: target url
        :param dict | None headers: request headers
        :return: urllib3.HTTPResponse
        """

        pool = self.__proxy_pool()
        response = pool.request(
            self.__cfg.method,
            url,
            headers=self.__headers if headers is None else headers,
            retries=self.__cfg.retries,
            redirect=False,
        )

        self.__mark_proxy_alive(self.__server)
        self._debug_response_received(self.__debug, response)
        self.__debug_cookie_middleware(response)
        return response

    def __mark_proxy_dead(self, server):
        """Remember a failed rotating proxy for the current scan runtime.

        :param str|None server: proxy server URL
        :return: None
        """

        if True is self.__cfg.is_standalone_proxy or not server:
            return

        normalized = self.__normalize_proxy_server(server)
        self.__dead_proxies.add(normalized)
        self.__proxy_pools.pop(normalized, None)

    def __mark_proxy_alive(self, server):
        """Clear stale dead-proxy state after a successful request.

        :param str|None server: proxy server URL
        :return: None
        """

        if not server:
            return

        self.__dead_proxies.discard(self.__normalize_proxy_server(server))

    def __get_available_proxies(self):
        """Return rotating proxies that are not marked dead.

        :raise ProxyRequestError:
        :return: list[str]
        """

        proxies = [
            self.__normalize_proxy_server(server)
            for server in self.__proxylist
            if self.__normalize_proxy_server(server) not in self.__dead_proxies
        ]

        if not proxies:
            raise ProxyRequestError('All rotating proxies are unavailable for this scan runtime')

        return proxies

    def __get_random_proxy(self):
        """
        Get random server from proxy list
        :return: str
        """

        proxy_list = self.__get_available_proxies()
        index = random.randrange(0, len(proxy_list))
        server = proxy_list[index]
        return self.__normalize_proxy_server(server)

    @classmethod
    def __normalize_proxy_server(cls, server):
        """
        Normalize proxy server aliases.

        :param str server: input proxy server
        :return: str
        """

        server = server.strip()
        return re.sub(r'^socks://', 'socks5://', server, count=1, flags=re.IGNORECASE)

    @classmethod
    def __get_proxy_type(cls, server):
        """
        Set proxy type
        :param str server: input proxy server
        :return: str
        """

        if 'socks' in server:
            return 'socks'
        elif 'https' in server:
            return 'https'
        else:
            return 'http'
