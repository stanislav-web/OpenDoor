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
from urllib3.exceptions import DecodeError, DependencyWarning, MaxRetryError, ProxySchemeUnknown, ReadTimeoutError, InsecureRequestWarning

from src.core import helper
from .exceptions import ProxyRequestError
from .tls import emit_tls_legacy_policy, maybe_build_ssl_context, tls_pool_kwargs, warn_tls_transport_error
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
            self.__headers, self.__is_user_agent_managed, self.__connection_header = self._initialize_request_backend(
                config,
                kwargs.get('agent_list'),
            )
            self.__server = None
            self.__pm = None
            self.__proxy_pools = {}
            self.__dead_proxies = set()
            self.__proxy_sequence_index = 0
            self.__cfg = config
            self.__debug = debug
            self.__ssl_context = maybe_build_ssl_context(getattr(self.__cfg, 'is_tls_legacy', False))
            self.__debug.debug_proxy_pool()
            self.__debug_tls_policy()

            if False is config.is_standalone_proxy and 0 == len(self.__proxylist):
                raise TypeError('Proxy list empty or has invalid format')

        except (TypeError, ValueError) as error:
            raise ProxyRequestError(error)


    def __debug_tls_policy(self):
        """Emit debug output for opt-in legacy TLS compatibility."""

        emit_tls_legacy_policy(self.__cfg, self.__tpl)


    def __pool_tls_kwargs(self):
        """Return urllib3 TLS kwargs only when legacy mode is enabled.

        :return: TLS keyword arguments for urllib3 proxy managers.
        :rtype: dict
        """

        return tls_pool_kwargs(self.__ssl_context)

    def __record_tls_transport_error(self, error):
        """Store and print a helpful TLS transport diagnostic when possible.

        :param Exception error: Source urllib3/OpenSSL exception.
        :return: None
        """

        warn_tls_transport_error(
            self.__cfg,
            self.__tpl,
            error,
            line_finisher=self.__finish_active_terminal_line,
        )

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
            server = self.__cfg.proxy if True is self.__cfg.is_standalone_proxy else self.__get_next_proxy()
            self.__server = self.__normalize_proxy_server(server)

            if self.__server in self.__proxy_pools:
                return self.__proxy_pools[self.__server]

            if True is not self.__cfg.is_standalone_proxy:
                getattr(self.__debug, 'debug_proxy_selected', lambda *args, **kwargs: True)(
                    self.__server,
                    getattr(self.__cfg, 'proxy_rotation', 'random'),
                )

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
                    **self.__pool_tls_kwargs()
                )
            else:
                pool = ProxyManager(
                    self.__server,
                    num_pools=self.__cfg.threads,
                    proxy_headers=self.__build_proxy_headers(self.__server),
                    timeout=Timeout(connect=self.__cfg.timeout, read=self.__cfg.timeout),
                    block=True,
                    **self.__pool_tls_kwargs()
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

    def close(self):
        """Release proxy managers cached during this scan runtime.

        :return: None
        """

        for pool in list(getattr(self, '_Proxy__proxy_pools', {}).values()):
            self._close_connection_resource(pool)

        self.__proxy_pools.clear()

    def prepare_connection_pool(self):
        """Create the first rotating proxy pool before transient progress starts.

        Fingerprinting renders an in-place progress line. If the first proxied
        request creates a pool during that progress, the proxy-selection debug
        line interrupts the progress row. Preparing the pool before the
        fingerprint detector starts keeps both outputs readable while preserving
        the normal lazy request path for scans without fingerprinting.

        :raise ProxyRequestError: when proxy pool initialization fails
        :return: True
        :rtype: bool
        """

        if True is self.__cfg.is_standalone_proxy:
            return True

        self.__proxy_pool()
        return True

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

    def request(self, url, extra_headers=None, absolute=False):
        """
        Client request using Proxy

        :param str url: request uri
        :param dict | list | tuple | None extra_headers: temporary per-request headers
        :return: urllib3.HTTPResponse
        """

        request_headers, self.__is_user_agent_managed = self._prepare_request_headers(
            self.__cfg,
            self.__debug,
            self.__headers,
            self.__is_user_agent_managed,
            self.__connection_header,
            url,
            extra_headers,
        )

        try:
            response = self.__pool_request(url, headers=request_headers)
            return response

        except MaxRetryError as error:
            self.__record_tls_transport_error(error)
            if self.__is_directory_like_scan() is True:
                self.__finish_active_terminal_line()
                self.__tpl.warning(
                    key='proxy_max_retry_error',
                    url=helper.parse_url(url).path,
                    proxy=self.__mask_proxy_server(self.__server),
                )
                return self.__retry_after_max_retry(url, request_headers)

        except ReadTimeoutError as error:
            self.__record_tls_transport_error(error)
            if self.__is_directory_like_scan() is True:
                self.__finish_active_terminal_line()
                self.__tpl.warning(key='read_timeout_error', url=helper.parse_url(url).path)

        except DecodeError:
            if self.__is_directory_like_scan() is True:
                self.__finish_active_terminal_line()
                self.__tpl.warning(key='decode_error', url=helper.parse_url(url).path)

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
            self.__record_tls_transport_error(error)
            self.__warn_proxy_retry_failed(url, error)
        except ReadTimeoutError as error:
            self.__record_tls_transport_error(error)
            self.__warn_proxy_retry_failed(url, error)
        except DecodeError:
            self.__finish_active_terminal_line()
            self.__tpl.warning(key='decode_error', url=helper.parse_url(url).path)

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

        setattr(self.__cfg, 'last_transport_error', None)
        self.__mark_proxy_alive(self.__server)
        self._debug_response_received(self.__debug, response)
        self._debug_cookie_middleware(self.__debug, self.__cfg.accept_cookies, response)
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

    def __get_next_proxy(self):
        """Return the next rotating proxy using the configured policy.

        :return: normalized proxy URL
        :rtype: str
        """

        if getattr(self.__cfg, 'proxy_rotation', 'random') == 'sequential':
            return self.__get_sequential_proxy()

        return self.__get_random_proxy()

    def __get_random_proxy(self):
        """
        Get random server from proxy list
        :return: str
        """

        proxy_list = self.__get_available_proxies()
        index = random.randrange(0, len(proxy_list))  # nosec B311
        server = proxy_list[index]
        return self.__normalize_proxy_server(server)

    def __get_sequential_proxy(self):
        """Return proxies in stable list order while skipping runtime-dead entries.

        :raise ProxyRequestError:
        :return: normalized proxy URL
        :rtype: str
        """

        self.__get_available_proxies()

        for _ in range(len(self.__proxylist)):
            index = self.__proxy_sequence_index % len(self.__proxylist)
            self.__proxy_sequence_index = (self.__proxy_sequence_index + 1) % len(self.__proxylist)
            server = self.__normalize_proxy_server(self.__proxylist[index])

            if server not in self.__dead_proxies:
                return server

        raise ProxyRequestError('All rotating proxies are unavailable for this scan runtime')

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
