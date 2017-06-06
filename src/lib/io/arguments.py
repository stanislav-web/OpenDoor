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

from src.core import options, OptionsError
from src.core import helper
from .exceptions import ArgumentsError


class Arguments(object):

    """Arguments class"""
    
    @staticmethod
    def get_arguments():
        """
        Get input arguments with their options
        :raise ArgumentsError
        :return: dict
        """

        try:
            args = options().get_arg_values()
            return args
        except OptionsError as error:
            raise ArgumentsError(str(error))

    @staticmethod
    def is_arg_callable(arg):
        """
        Check if argument is callable

        :param callable arg:
        :return: bool
        """

        return helper.is_callable(arg)
