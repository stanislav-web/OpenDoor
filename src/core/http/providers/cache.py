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

class CacheControlProvider(object):
    """ CacheControlProvider class"""

    def __init__(self):
        """
        Init interface
        """

        self.__cache_control = 'max-age=0'

    @property
    def _cache_control(self):
        """
        Get 'Cache-Control' Header
        :return: str
        """

        return self.__cache_control
