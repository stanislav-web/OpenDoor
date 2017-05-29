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

from http.cookies import SimpleCookie


class CookiesProvider(object):
    """ CookiesProvider class"""

    def __init__(self):
        """
        Init interface
        """

        self._cookies = None

    @property
    def _is_cookie_fetched(self):
        """
        Check if cookies has been fetched from response
        :return: bool
        """

        return False if None is self._cookies else True

    def _fetch_cookies(self, headers):
        """
        Fetch cookies from response
        :param dict headers: response header
        :return: None
        """

        if 'set-cookie' in headers:
            self._cookies = SimpleCookie(headers['set-cookie'])

    def _push_cookies(self):
        """
        Push cookies to request
        :return: str cookies
        """

        return self._cookies.output(attrs=[], header='').strip()
