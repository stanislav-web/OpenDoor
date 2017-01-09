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

    Development Team: Stanislav Menshov
"""

from src.lib import tpl

class Debug:
    """Debug class"""

    def __init__(self):
        if 0 < self._debug:
            tpl.debug(key='debug', level=self._debug)
        pass


    def _debug_user_agents(self):
        if 0 >= self._debug:
            pass
        else:
            if True is self._is_random_user_agent:
                tpl.debug(key='random_browser')
            else:
                tpl.debug(key='browser', browser=self._user_agent)


    def _debug_proxy(self):
        if 0 >= self._debug:
            pass
        else:
            if True is self._is_proxy:
                tpl.debug(key='proxy')

    def _debug_list(self):
        if 0 >= self._debug:
            pass
        else:
            if self._default_scan is self._scan:
                tpl.debug(key='directories')
            else :
                tpl.debug(key='subdomains')


    def _debug_line(self, line):
        if 0 >= self._debug:
            tpl.line(line)
        else:
            tpl.info(line)

