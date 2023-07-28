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

from urllib3 import HTTPHeaderDict

from .accept import AcceptHeaderProvider
from .cache import CacheControlProvider


class HeaderProvider(AcceptHeaderProvider, CacheControlProvider):
    """ HeaderProvider class"""

    def __init__(self, config):
        """
        Init interface.
        Accept external params
        :param src.lib.browser.config.Config config: browser configurations
        """

        self.__headers = HTTPHeaderDict()

        self.__cfg = config

        AcceptHeaderProvider.__init__(self)
        CacheControlProvider.__init__(self)

    def add_header(self, key, value):
        """
        Add custom header

        :param str key: header name
        :param str value: header value
        :return: HeaderProvider
        """

        self.__headers.update({key.strip(): value.strip()})
        return self

    @property
    def _headers(self):
        """
        Get Headers
        :return: dict headers
        """

        origin = ''.join([self.__cfg.scheme, self.__cfg.host])
        referer = ''.join([self.__cfg.scheme, self.__cfg.host]) + ':' + str(self.__cfg.port)
        self.add_header('Accept', self._accept) \
            .add_header('Accept-Encoding', self._accept_encoding) \
            .add_header('Accept-Language', self._accept_language) \
            .add_header('Origin', origin) \
            .add_header('Referer', referer) \
            .add_header('Cache-Control', self._cache_control) \
            .add_header('Upgrade-Insecure-Requests', '1') \
            .add_header('Pragma', 'no-cache')
        return self.__headers
