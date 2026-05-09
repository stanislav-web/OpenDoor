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

    def request(self, url, extra_headers=None):
        """
        Client request

        :param str url: request uri
        :param dict | list | tuple | None extra_headers: temporary per-request headers
        :return: None
        """

        pass

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
