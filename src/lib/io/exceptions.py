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

from src.core import exception


class ArgumentsError(Exception):

    """ArgumentsError class"""

    def __init__(self, error):
        """
        ArgumentsError class constructor
        :param str error: error message
        """

        class_name = type(error).__name__

        if self.__class__.__name__ is not class_name:
            exception.log(class_name=class_name, message=error)

        super(ArgumentsError, self).__init__("{0}: {1}".format(str(class_name), str(error)))
