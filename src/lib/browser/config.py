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

class Config:
    """Config class"""

    def __init__(self, params):
        """
        Read filtered input params

        :param params:
        """

        self._default_scan = 'directories'
        self._scan = params.get('scan')
        self._scheme = params.get('scheme')
        self._host = params.get('host')
        self._port = params.get('port')
        self._is_indexof = params.get('indexof')
        self._method = params.get('method') if params.get('indexof') is None else 'GET'
        self._threads = params.get('threads')
        self._delay = 0 if params.get('delay')is None else params.get('delay')
        self._timeout =  0 if params.get('timeout')is None else params.get('timeout')
        self._threads = params.get('threads')
        self._debug = 0 if params.get('debug')is None else params.get('debug')
        self._is_proxy = params.get('tor')
        self._is_random_user_agent = params.get('random_agent')
        self._is_random_list = params.get('random_list')
        self._user_agent = 'Opera/9.0 (Windows NT 5.1; U; en)'



