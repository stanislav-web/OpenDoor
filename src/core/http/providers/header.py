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

import random

from .accept import AcceptHeaderProvider


class HeaderProvider(AcceptHeaderProvider):
    """ HeaderProvider class"""

    def __init__(self, config, agent_list=()):
        """
        Accept external params
        :param src.lib.browser.config.Config config: browser configurations
        :param dict agent_list: user agent list
        """
        self.__headers = {}
        self.__config = config
        self.__agent_list = agent_list

        AcceptHeaderProvider.__init__(self)

    @property
    def __user_agent(self):
        """
        Get user agent
        :return: str user-agent
        """

        if True is self.__config._is_random_user_agent:
            index = random.randrange(0, len(self.__agent_list))
            user_agent = self.__agent_list[index].strip()
        else:
            user_agent = self.__config.user_agent
        return user_agent

    def _add_header(self, key, value):
        """
        Add custom header

        :param str key: header name
        :param str value: header value
        :return: HeaderProvider
        """
        self.__headers[key] = value

        return self

    @property
    def _headers(self):
        """
        Get Headers
        :return: dict headers
        """

        self._add_header('Accept', self._accept)._add_header('Accept-Encoding', self._accept_encoding)._add_header(
            'Accept-Language', self._accept_language)._add_header('Referer', ''.join(
            [self.__config.scheme, self.__config.host]))._add_header('User-Agent', self.__user_agent)._add_header(
            'Cache-Conrol', 'no-cache')._add_header('Pragma', 'no-cache')

        return self.__headers
