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

# noinspection PyCompatibility
from argparse import ArgumentParser


class ArgumentParserError(Exception):

    """ArgumentParserError class"""
    pass


class ThrowingArgumentParser(ArgumentParser):

    """ThrowingArgumentParser class"""

    @classmethod
    def error(cls, message):
        """
        Error message
        :param message: message
        :raise ArgumentParserError
        :return: None
        """

        raise ArgumentParserError(message)


class OptionsError(Exception):

    """OptionsError class"""

    def __init__(self, message):
        """
        Error message
        :param message: message
        :return: None
        """

        super(OptionsError, self).__init__(message)


class FilterError(Exception):

    """FilterError class"""

    def __init__(self, message):
        """
         Error message
         :param message: message
         :return: None
         """

        super(FilterError, self).__init__(message)
