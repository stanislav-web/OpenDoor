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

from urllib3 import HTTPConnectionPool, PoolManager, Timeout
from urllib3.exceptions import DecodeError, MaxRetryError, ReadTimeoutError, ConnectTimeoutError, HostChangedError
from src.core import helper
from .exceptions import HttpRequestError
from .providers import DebugProvider
from .providers import RequestProvider


class HttpRequest(RequestProvider, DebugProvider):

    """HttpRequest class"""

    def __init__(self, config, debug, **kwargs):
        """
        HttpRequest instance
        :param src.lib.browser.config.Config config: global configurations
        :param DebugProvider debug: debugger
        """

        try:
            self.__tpl = kwargs.get('tpl')
            self.__headers, self.__is_user_agent_managed, self.__connection_header = self._initialize_request_backend(
                config,
                kwargs.get('agent_list'),
            )
        except (TypeError, ValueError) as error:
            raise HttpRequestError(error)

        self.__cfg = config
        self.__debug = debug
        self.__manager = None

        if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:
            self.__pool = self.__http_pool()
        else:
            self.__manager = self.__pool_manager()

    def __http_pool(self):
        """
        Create HTTP connection pool
        :raise HttpRequestError
        :return: urllib3.HTTPConnectionPool
        """

        try:
            pool = HTTPConnectionPool(
                self.__cfg.host,
                port=self.__cfg.port,
                maxsize=self.__cfg.threads,
                timeout=Timeout(connect=self.__cfg.timeout, read=self.__cfg.timeout),
                block=True,
            )
            getattr(self.__debug, 'debug_connection_pool', lambda *args, **kwargs: True)(
                'http_pool_start', pool, self.__connection_header)
            return pool
        except Exception as error:
            raise HttpRequestError(str(error))

    def __pool_manager(self):
        """
        Create reusable HTTP pool manager for non-default scans.

        :raise HttpRequestError
        :return: urllib3.PoolManager
        """

        try:
            return PoolManager(
                num_pools=self.__cfg.threads,
                maxsize=self.__cfg.threads,
                timeout=Timeout(connect=self.__cfg.timeout, read=self.__cfg.timeout),
                block=True,
            )
        except Exception as error:
            raise HttpRequestError(str(error))

    def close(self):
        """Release HTTP connection pools owned by this request backend.

        :return: None
        """

        self._close_connection_resource(getattr(self, '_HttpRequest__pool', None))
        self._close_connection_resource(getattr(self, '_HttpRequest__manager', None))

    def request(self, url, extra_headers=None, absolute=False):
        """
        Client request HTTP

        :param str url: request uri
        :param dict | list | tuple | None extra_headers: temporary per-request headers
        :param bool absolute: use an absolute URL through a pool manager
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
            if self.__cfg.DEFAULT_SCAN == self.__cfg.scan and absolute is not True:
                response = self.__pool.request(
                    self.__cfg.method,
                    helper.parse_url(url).path,
                    headers=request_headers,
                    body=self._request_body,
                    retries=self.__cfg.retries,
                    assert_same_host=True,
                    redirect=False,
                )
            else:
                if self.__manager is None:
                    self.__manager = self.__pool_manager()

                response = self.__manager.request(
                    self.__cfg.method,
                    url,
                    headers=request_headers,
                    body=self._request_body,
                    retries=self.__cfg.retries,
                    assert_same_host=False,
                    redirect=False,
                )
            self._debug_response_received(self.__debug, response)
            self._debug_cookie_middleware(self.__debug, self.__cfg.accept_cookies, response)
            return response

        except MaxRetryError:
            pass

        except HostChangedError as error:
            self.__tpl.warning(key='host_changed_error', details=error)

        except ReadTimeoutError:
            self.__tpl.warning(key='read_timeout_error', url=url)

        except DecodeError:
            self.__tpl.warning(key='decode_error', url=url)

        except ConnectTimeoutError:
            self.__tpl.warning(key='connection_timeout_error', url=url)
