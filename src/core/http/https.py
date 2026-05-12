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

from urllib3 import HTTPSConnectionPool, PoolManager, HTTPResponse, Timeout, disable_warnings
from urllib3.exceptions import MaxRetryError, ReadTimeoutError, ConnectTimeoutError, \
    HostChangedError, SSLError, InsecureRequestWarning
from src.core import helper
from .exceptions import HttpsRequestError
from .providers import DebugProvider
from .providers import RequestProvider


class HttpsRequest(RequestProvider, DebugProvider):
    """HttpsRequest class"""

    DEFAULT_SSL_CERT_REQUIRED_STATUSES = 496

    def __init__(self, config, debug, **kwargs):
        """
        HttpsRequest instance
        :param src.lib.browser.config.Config config: global configurations
        :param DebugProvider debug: debugger
        """

        try:
            self.__tpl = kwargs.get('tpl')
            RequestProvider.__init__(self, config, agent_list=kwargs.get('agent_list'))
            self.__headers = self._headers
            self.__is_user_agent_managed = self.__headers.get('User-Agent') is None
            self.__connection_header = 'default'
            if True is config.keep_alive:
                self.__connection_header = self._keep_alive
        except (TypeError, ValueError) as error:
            raise HttpsRequestError(error)

        self.__cfg = config
        self.__debug = debug
        self.__manager = None

        if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:
            self.__pool = self.__https_pool()
        else:
            self.__manager = self.__pool_manager()

    def _provide_ssl_auth_required(self):
        """
        Provide ssl auth response
        :return: urllib3.HTTPResponse
        """

        response = HTTPResponse()
        response.status = self.DEFAULT_SSL_CERT_REQUIRED_STATUSES
        response.__setattr__('_body', ' ')
        return response

    def __https_pool(self):
        """
        Create HTTP connection pool
        :raise HttpsRequestError
        :return: urllib3.HTTPConnectionPool
        """

        try:
            pool = HTTPSConnectionPool(
                host=self.__cfg.host,
                port=self.__cfg.port,
                maxsize=self.__cfg.threads,
                timeout=Timeout(connect=self.__cfg.timeout, read=self.__cfg.timeout),
                cert_reqs='CERT_NONE',
                block=True,
            )
            getattr(self.__debug, 'debug_connection_pool', lambda *args, **kwargs: True)(
                'https_pool_start', pool, self.__connection_header)

            return pool
        except Exception as error:
            raise HttpsRequestError(str(error))

    def __pool_manager(self):
        """
        Create reusable HTTPS pool manager for non-default scans.

        :raise HttpsRequestError
        :return: urllib3.PoolManager
        """

        try:
            return PoolManager(
                num_pools=self.__cfg.threads,
                maxsize=self.__cfg.threads,
                timeout=Timeout(connect=self.__cfg.timeout, read=self.__cfg.timeout),
                block=True,
                cert_reqs='CERT_NONE',
            )
        except Exception as error:
            raise HttpsRequestError(str(error))

    def __debug_cookie_middleware(self, response):
        """Route response cookies and emit request-level cookie diagnostics."""

        if True is self.__cfg.accept_cookies:
            getattr(self.__debug, 'debug_cookie_accept_enabled', lambda *args, **kwargs: True)()

        self.cookies_middleware(is_accept=self.__cfg.accept_cookies, response=response)

        if True is self.__cfg.accept_cookies and True is self._is_cookie_fetched:
            getattr(self.__debug, 'debug_cookie_accepted', lambda *args, **kwargs: True)(self._push_cookies())

    def request(self, url, extra_headers=None):
        """
        Client request SSL

        :param str url: request uri
        :param dict | list | tuple | None extra_headers: temporary per-request headers
        :return: urllib3.HTTPResponse
        """

        if True is self.__cfg.is_random_user_agent and True is self.__is_user_agent_managed:
            self.__headers.update({'User-Agent': self._user_agent})
        elif self.__headers.get('User-Agent') is None:
            self.__headers.update({'User-Agent': self._user_agent})
            self.__is_user_agent_managed = True

        request_headers = self._build_request_headers(self.__headers, extra_headers)
        if 'default' != self.__connection_header and request_headers.get('Connection') is None:
            request_headers.update({'Connection': self.__connection_header})

        getattr(self.__debug, 'debug_cookie_attached', lambda *args, **kwargs: True)(request_headers)
        getattr(self.__debug, 'debug_request', lambda *args, **kwargs: True)(request_headers, url, self.__cfg.method)
        try:
            disable_warnings(InsecureRequestWarning)
            if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:  # directories requests
                response = self.__pool.request(self.__cfg.method,
                                               helper.parse_url(url).path,
                                               headers=request_headers,
                                               body=self._request_body,
                                               retries=self.__cfg.retries,
                                               assert_same_host=False,
                                               redirect=False)
            else:  # subdomains
                response = self.__manager.request(self.__cfg.method, url,
                                                  headers=request_headers,
                                                  body=self._request_body,
                                                  retries=self.__cfg.retries,
                                                  assert_same_host=False,
                                                  redirect=False)
            self._debug_response_received(self.__debug, response)
            self.__debug_cookie_middleware(response)
            return response

        except MaxRetryError:
            if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:
                self.__tpl.warning(key='max_retry_error', url=helper.parse_url(url).path)

        except HostChangedError as error:
            self.__tpl.warning(key='host_changed_error', details=error)

        except ReadTimeoutError:
            self.__tpl.warning(key='read_timeout_error', url=url)

        except ConnectTimeoutError:
            self.__tpl.warning(key='connection_timeout_error', url=url)

        except SSLError:
            if self.__cfg.DEFAULT_SCAN != self.__cfg.scan:
                return self._provide_ssl_auth_required()
