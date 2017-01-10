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

    default = 'white'

    @staticmethod
    def get(key):
        """
        Get color num

        :param str key: color name
        :return: int
        """

        colorlist = {
            'black' : 0,
            'red' : 1,
            'green' : 2,
            'yellow' : 3,
            'blue' : 4,
            'magenta' : 5,
            'cyan' : 6,
            'white' : 7
        }

        if key in colorlist:
            return colorlist[key]
        else:
            return colorlist[Config.default]


