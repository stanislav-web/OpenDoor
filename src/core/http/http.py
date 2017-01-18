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

from urllib3 import HTTPConnectionPool

from .exceptions import HttpRequestError


class HttpRequest():
    """HttpRequest class"""

    __debug = False
    __cfg = False
    __pool = None
    __tpl = None

    def __init__(self, config, debug=0, **kwargs):
        """
        Request instance
        :param src.lib.browser.config.Config config:
        :param int debug: debug flag
        """

        if 'tpl' in kwargs:
            self.__tpl = kwargs.get('tpl')

        self.__cfg = config
        self.__debug = False if debug < 2 else True
        self.__pool = self.__http_pool()

    def __http_pool(self):
        """
        Create HTTP connection pool
        :raise HttpRequestError
        :return: urllib3.HTTPConnectionPool
        """

        try:
            if True is self.__debug:
                self.__tpl.debug(key='http_pool_start')

            pool = HTTPConnectionPool(self.__cfg.host, port=self.__cfg.port, maxsize=self.__cfg.threads,
                                      timeout=self.__cfg.timeout, block=True)
            return pool
        except Exception as e:
            raise HttpRequestError(e)
