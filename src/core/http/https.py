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
from urllib3.exceptions import DecodeError, MaxRetryError, ReadTimeoutError, ConnectTimeoutError, \
    HostChangedError, SSLError, InsecureRequestWarning
from src.core import helper
from .exceptions import HttpsRequestError
from .tls import emit_tls_legacy_policy, build_target_ssl_context, tls_pool_kwargs, warn_tls_transport_error
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
            self.__headers, self.__is_user_agent_managed, self.__connection_header = self._initialize_request_backend(
                config,
                kwargs.get('agent_list'),
            )
        except (TypeError, ValueError) as error:
            raise HttpsRequestError(error)

        self.__cfg = config
        self.__debug = debug
        self.__manager = None
        self.__ssl_context = build_target_ssl_context(
            tls_legacy=getattr(self.__cfg, 'is_tls_legacy', False),
            client_cert=getattr(self.__cfg, 'client_cert', None),
            client_key=getattr(self.__cfg, 'client_key', None),
            client_key_password_env=getattr(self.__cfg, 'client_key_password_env', None),
        )
        self.__debug_tls_policy()

        if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:
            self.__pool = self.__https_pool()
        else:
            self.__manager = self.__pool_manager()


    def __debug_tls_policy(self):
        """Emit debug output for opt-in legacy TLS compatibility."""

        emit_tls_legacy_policy(self.__cfg, self.__tpl)


    def __pool_tls_kwargs(self):
        """Return urllib3 TLS kwargs only when legacy mode is enabled.

        :return: TLS keyword arguments for urllib3 pool constructors.
        :rtype: dict
        """

        return tls_pool_kwargs(self.__ssl_context)

    def __record_tls_transport_error(self, error):
        """Store and print a helpful TLS transport diagnostic when possible.

        :param Exception error: Source urllib3/OpenSSL exception.
        :return: None
        """

        warn_tls_transport_error(self.__cfg, self.__tpl, error)

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
                **self.__pool_tls_kwargs()
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
                **self.__pool_tls_kwargs()
            )
        except Exception as error:
            raise HttpsRequestError(str(error))

    def close(self):
        """Release HTTPS connection pools owned by this request backend.

        :return: None
        """

        self._close_connection_resource(getattr(self, '_HttpsRequest__pool', None))
        self._close_connection_resource(getattr(self, '_HttpsRequest__manager', None))

    def request(self, url, extra_headers=None, absolute=False):
        """
        Client request SSL

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
            disable_warnings(InsecureRequestWarning)
            if self.__cfg.DEFAULT_SCAN == self.__cfg.scan and absolute is not True:  # directories requests
                response = self.__pool.request(self.__cfg.method,
                                               helper.parse_url(url).path,
                                               headers=request_headers,
                                               body=self._request_body,
                                               retries=self.__cfg.retries,
                                               assert_same_host=False,
                                               redirect=False)
            else:  # absolute follow-up or subdomains
                if self.__manager is None:
                    self.__manager = self.__pool_manager()

                response = self.__manager.request(self.__cfg.method, url,
                                                  headers=request_headers,
                                                  body=self._request_body,
                                                  retries=self.__cfg.retries,
                                                  assert_same_host=False,
                                                  redirect=False)
            setattr(self.__cfg, 'last_transport_error', None)
            self._debug_response_received(self.__debug, response)
            self._debug_cookie_middleware(self.__debug, self.__cfg.accept_cookies, response)
            return response

        except MaxRetryError as error:
            self.__record_tls_transport_error(error)

        except HostChangedError as error:
            self.__tpl.warning(key='host_changed_error', details=error)

        except ReadTimeoutError:
            self.__tpl.warning(key='read_timeout_error', url=url)

        except DecodeError:
            self.__tpl.warning(key='decode_error', url=url)

        except ConnectTimeoutError:
            self.__tpl.warning(key='connection_timeout_error', url=url)

        except SSLError as error:
            self.__record_tls_transport_error(error)
            if self.__cfg.DEFAULT_SCAN != self.__cfg.scan:
                return self._provide_ssl_auth_required()
