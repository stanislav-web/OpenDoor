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
        Check if cookies have been fetched from response
        :return: bool
        """

        return False if None is self._cookies else True

    @staticmethod
    def _extract_cookie_pair(raw_cookie):
        """
        Extract request-safe cookie pair from Set-Cookie header value.

        :param str raw_cookie: raw Set-Cookie header value
        :return: str
        """

        if raw_cookie is None:
            return ''

        cookie = str(raw_cookie).strip()
        if not cookie:
            return ''

        cookie = cookie.split(';', 1)[0].strip()
        if '=' not in cookie:
            return ''

        name, value = cookie.split('=', 1)
        name = name.strip()
        value = value.strip()

        if not name:
            return ''

        return '='.join([name, value])

    @staticmethod
    def _get_set_cookie_values(headers):
        """
        Get Set-Cookie values from case-insensitive urllib3/dict headers.

        :param dict headers: response headers
        :return: list[str]
        """

        if hasattr(headers, 'getlist'):
            values = headers.getlist('set-cookie')
            if len(values) > 0:
                return values

        values = []
        for key, value in getattr(headers, 'items', list)():
            if str(key).lower() == 'set-cookie':
                values.append(value)

        return values

    def _fetch_cookies(self, headers):
        """
        Fetch cookies from response
        :param dict headers:  header
        :return: None
        """

        cookies = []
        for raw_cookie in self._get_set_cookie_values(headers):
            cookie = self._extract_cookie_pair(raw_cookie)
            if cookie:
                cookies.append(cookie)

        if len(cookies) > 0:
            self._cookies = '; '.join(cookies)

    def _push_cookies(self):
        """
        Push cookies to request
        :return: str cookies
        """

        return '' if self._cookies is None else self._cookies.strip()
