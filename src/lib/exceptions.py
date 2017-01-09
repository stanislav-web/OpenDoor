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

from src.core import exception

class LibError(Exception):
    """LibError class"""

    def __init__(self, message):
        """
        LibError class constructor

        :param str message: error message
        """

        class_name = type(message).__name__

        if self.__class__.__name__ is not class_name:
            exception.log(class_name=class_name, message=message)

        super(LibError, self).__init__("{}: {}".format(class_name,message))
