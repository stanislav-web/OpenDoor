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

from .cookies import CookiesProvider
from .header import HeaderProvider
from .user_agent import UserAgentHeaderProvider
from .connection import ConnectionHeaderProvider


class RequestProvider(CookiesProvider, HeaderProvider, UserAgentHeaderProvider, ConnectionHeaderProvider):
    """ RequestProvider class"""

    _HTTP_DBG_LEVEL = 2

    def __init__(self, config, agent_list):
        """
        Init interface
        :param src.lib.browser.config.Config config: configurations
        :param dict agent_list: list of user agents
        """

        HeaderProvider.__init__(self, config)
        ConnectionHeaderProvider.__init__(self, config)
        UserAgentHeaderProvider.__init__(self, config, agent_list)
        CookiesProvider.__init__(self)
        self._request_body = getattr(config, 'request_body', None)
        self._apply_custom_headers(config)
        self._apply_custom_cookies(config)

    def _initialize_request_backend(self, config, agent_list=None):
        """Initialize shared request provider state for request backends.

        HTTP, HTTPS and proxy backends all need the same base request
        providers, effective headers, explicit User-Agent state and
        Connection header policy. Keeping that contract here prevents
        backend-specific drift.

        :param src.lib.browser.config.Config config: configurations
        :param dict | list | None agent_list: list of user agents
        :return: effective headers, managed User-Agent flag and Connection header value
        :rtype: tuple[dict, bool, str]
        """

        RequestProvider.__init__(self, config, agent_list=agent_list)
        headers = self._headers
        connection_header = self._keep_alive if True is config.keep_alive else 'default'

        return headers, headers.get('User-Agent') is None, connection_header

    def _apply_custom_headers(self, config):
        """
        Apply custom request headers from cli/config.

        :param src.lib.browser.config.Config config: configurations
        :return: None
        """

        raw_headers = getattr(config, 'headers', None)
        if raw_headers is None:
            raw_headers = getattr(config, 'header', [])

        for raw_header in raw_headers or []:
            if ':' not in str(raw_header):
                continue

            key, value = str(raw_header).split(':', 1)
            key = key.strip()
            value = value.strip()

            if key and value:
                self.add_header(key, value)

    def _apply_custom_cookies(self, config):
        """
        Apply custom request cookies from cli/config.

        :param src.lib.browser.config.Config config: configurations
        :return: None
        """

        raw_cookies = getattr(config, 'cookies', None)
        if raw_cookies is None:
            raw_cookies = getattr(config, 'cookie', [])

        cookies = [
            str(item).strip()
            for item in (raw_cookies or [])
            if str(item).strip()
        ]

        if cookies:
            self.add_header('Cookie', '; '.join(cookies))

    @staticmethod
    def _iter_extra_headers(extra_headers):
        """
        Normalize temporary per-request headers.

        :param dict | list | tuple | None extra_headers: temporary headers
        :return: list[tuple[str, str]]
        """

        if extra_headers is None:
            return []

        if isinstance(extra_headers, dict):
            items = extra_headers.items()
        else:
            items = extra_headers

        headers = []

        for item in items:
            if isinstance(item, str):
                if ':' not in item:
                    continue

                key, value = item.split(':', 1)
            else:
                try:
                    key, value = item
                except (TypeError, ValueError):
                    continue

            key = str(key).strip()
            value = str(value).strip()

            if not key or not value:
                continue

            if '\r' in key or '\n' in key or '\r' in value or '\n' in value:
                continue

            headers.append((key, value))

        return headers

    def _build_request_headers(self, base_headers, extra_headers=None):
        """
        Build request headers without mutating the shared provider headers.

        :param dict base_headers: shared request headers
        :param dict | list | tuple | None extra_headers: temporary headers
        :return: dict
        """

        try:
            headers = base_headers.copy()
        except AttributeError:
            headers = dict(base_headers)

        for key, value in self._iter_extra_headers(extra_headers):
            headers.update({key: value})

        return headers

    def _prepare_request_headers(
            self,
            config,
            debug,
            base_headers,
            is_user_agent_managed,
            connection_header,
            url,
            extra_headers=None
    ):
        """Build effective request headers and emit request diagnostics.

        HTTP, HTTPS and proxy backends share the same User-Agent,
        temporary-header, Connection-header and request-debug contract.
        Keeping it here prevents backend-specific drift.

        :param src.lib.browser.config.Config config: configurations
        :param DebugProvider debug: debugger
        :param dict base_headers: shared request headers
        :param bool is_user_agent_managed: whether OpenDoor owns User-Agent updates
        :param str connection_header: configured Connection header policy
        :param str url: request uri
        :param dict | list | tuple | None extra_headers: temporary per-request headers
        :return: request headers and updated managed User-Agent state
        :rtype: tuple[dict, bool]
        """

        if True is config.is_random_user_agent and True is is_user_agent_managed:
            base_headers.update({'User-Agent': self._user_agent})
        elif base_headers.get('User-Agent') is None:
            base_headers.update({'User-Agent': self._user_agent})
            is_user_agent_managed = True

        request_headers = self._build_request_headers(base_headers, extra_headers)
        if connection_header != 'default' and request_headers.get('Connection') is None:
            request_headers.update({'Connection': connection_header})

        getattr(debug, 'debug_cookie_attached', lambda *args, **kwargs: True)(request_headers)
        getattr(debug, 'debug_request', lambda *args, **kwargs: True)(request_headers, url, config.method)

        return request_headers, is_user_agent_managed

    @staticmethod
    def _build_response_debug_headers(response):
        """Build response headers for response-level debug output.

        The request layer sees every HTTP response, including fingerprint,
        calibration and dictionary requests. Keeping response header debug here
        makes --debug 3 consistently more informative than --debug 2.

        :param urllib3.response.BaseHTTPResponse response: response object
        :return: serializable response headers with Status when available
        :rtype: dict
        """

        if not hasattr(response, 'headers'):
            return {}

        try:
            headers = dict(response.headers)
        except (TypeError, ValueError):
            headers = getattr(response.headers, '__dict__', {})

        if hasattr(response, 'status'):
            headers.update({'Status': str(response.status)})

        return headers

    def _debug_response_received(self, debug, response):
        """Emit response-level diagnostics for a received HTTP response.

        :param DebugProvider debug: debugger
        :param urllib3.response.BaseHTTPResponse response: response object
        :return: always True
        :rtype: bool
        """

        if hasattr(response, 'headers'):
            getattr(debug, 'debug_response', lambda *args, **kwargs: True)(
                self._build_response_debug_headers(response)
            )

        return True

    def _debug_cookie_middleware(self, debug, accept_cookies, response):
        """Route response cookies and emit request-level cookie diagnostics.

        :param DebugProvider debug: debugger
        :param bool accept_cookies: whether response cookies should be accepted
        :param urllib3.response.BaseHTTPResponse response: response object
        :return: None
        """

        if True is accept_cookies:
            getattr(debug, 'debug_cookie_accept_enabled', lambda *args, **kwargs: True)()

        self.cookies_middleware(is_accept=accept_cookies, response=response)

        if True is accept_cookies and True is self._is_cookie_fetched:
            getattr(debug, 'debug_cookie_accepted', lambda *args, **kwargs: True)(self._push_cookies())


    @staticmethod
    def _close_connection_resource(resource):
        """Release urllib3 connection pools/managers when a backend is closed.

        urllib3 connection pools expose ``close()``, while pool/proxy managers
        expose ``clear()``. Centralizing that small compatibility contract keeps
        HTTP, HTTPS and proxy backends aligned and avoids leaking idle sockets
        across repeated scans in one Python process.

        :param object resource: urllib3 pool or manager instance
        :return: whether a cleanup method was called
        :rtype: bool
        """

        if resource is None:
            return False

        close = getattr(resource, 'close', None)
        if callable(close):
            close()
            return True

        clear = getattr(resource, 'clear', None)
        if callable(clear):
            clear()
            return True

        return False

    def request(self, url, extra_headers=None):
        """
        Client request

        :param str url: request uri
        :param dict | list | tuple | None extra_headers: temporary per-request headers
        :return: None
        """


    def cookies_middleware(self, is_accept, response):
        """
        Route fetched cookies from first response to the next requests
        :param is_accept: Is cookies was accepted
        :param urllib3.response.BaseHTTPResponse response: Http response
        :return: None
        """

        if True is is_accept and hasattr(response, 'headers'):
            self._fetch_cookies(response.headers)
            if True is self._is_cookie_fetched:
                self.add_header('Cookie', self._push_cookies())
