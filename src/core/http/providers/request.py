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

from .cookies import CookiesProvider
from .header import HeaderProvider


class RequestProvider(CookiesProvider, HeaderProvider):
    """ RequestProvider class"""

    _HTTP_DBG_LEVEL = 2

    def __init__(self, config, agent_list):
        """
        Init interface
        :param src.lib.browser.config.Config config: configurations
        :param dict agent_list: list of user agents
        """

        HeaderProvider.__init__(self, config, agent_list)
        CookiesProvider.__init__(self)

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
        :param urllib3.response.HTTPResponse response: Http response
        :return: None
        """

        if True is is_accept and hasattr(response, 'headers'):
            self._fetch_cookies(response.headers)
            if True is self._is_cookie_fetched:
                self.add_header('Cookie', self._push_cookies())
