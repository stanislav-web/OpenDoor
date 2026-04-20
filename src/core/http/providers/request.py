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

    def request(self, url):
        """
        Client request
        :param str url: request uri
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
