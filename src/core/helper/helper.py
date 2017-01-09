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

from distutils.version import LooseVersion

class Helper:
    """Helper class"""

    @staticmethod
    def is_less(arg1, arg2):
        """
        Compare two numbers

        :param int arg1:
        :param int arg2:
        :return: bool
        """
        if LooseVersion(arg1) < LooseVersion(arg2):
            return True
        else:
            return False

