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

from distutils.version import StrictVersion
import urlparse

class Helper:
    """Helper class"""

    @staticmethod
    def parse_url(url):
        """
        Parse url

        :param str url:
        :return: dict
        """
        return urlparse.urlparse(url)

    @staticmethod
    def percent(counter, total):
        """
        Return percentage
        :param int counter:
        :param int total:
        :return: str
        """
        return "{percent}%".format(percent=round(100.0 * counter / float(total), 1))

    @staticmethod
    def is_less(arg1, arg2):
        """
        Compare two numbers (< less)
        :param int arg1:
        :param int arg2:
        :return: bool
        """
        if StrictVersion(arg1) < StrictVersion(arg2):
            return True
        else:
            return False

    @staticmethod
    def is_more(arg1, arg2):
        """
        Compare two numbers (great >)
        :param int arg1:
        :param int arg2:
        :return: bool
        """

        if StrictVersion(arg1) > StrictVersion(arg2):
            return True
        else:
            return False
