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

from src.lib.tpl import Tpl as tpl


class Debug:
    """Debug class"""

    def __init__(self, Config):
        """
        Debug constructor
        :param Config: Config
        """

        self.__config = Config

        if 0 < self.__config.debug:
            tpl.debug(key='debug', level=self.__config.debug)
        pass

    def _debug_user_agents(self):
        """
        Debug info for user agent
        :return: None
        """

        if 0 >= self.__config.debug:
            pass
        else:
            if True is self.__config.is_random_user_agent:
                tpl.debug(key='random_browser')
            else:
                tpl.debug(key='browser', browser=self.__config.user_agent)

    def _debug_proxy(self):
        """
        Debug info for proxy
        :return: None
        """

        if 0 < self.__config.debug:
            if True is self.__config.is_proxy:
                tpl.debug(key='proxy')
        else:
            pass

    def _debug_randomizing_list(self):
        """
        Debug randomizing list process
        :return: None
        """

        if 0 < self.__config.debug:
            tpl.debug(key='randomizing')

    def _debug_list(self, total_lines):
        """
        Debug list process
        :param int total_lines: list lines
        :return: None
        """

        if 0 < self.__config.debug:
            if self.__config.default_scan is self.__config.scan:
                tpl.debug(key='directories', total=total_lines)
            else:
                tpl.debug(key='subdomains', total=total_lines)
            tpl.debug(key='create_queue', threads=self.__config.threads)

    def _debug_line(self, line):
        """
        Debug info for target line
        :param str line
        :return: None
        """

        if 0 < self.__config.debug:
            tpl.info(line)
        else:
            tpl.line_log(line)

    def _debug_progress(self, i, total):
        """
        Progress bar
        :param int i: current counter
        :param int total: total counter
        :return: None
        """

        if 0 < self.__config.debug:
            tpl.progress(i, total)
