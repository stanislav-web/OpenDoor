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

import collections
import json
import webbrowser
from urllib.parse import urlparse
from distutils.version import LooseVersion


class Helper(object):

    """Helper class"""

    @staticmethod
    def counter():
        """
        Provide counter collection
        :return: collections.Counter
        """

        return collections.Counter()

    @staticmethod
    def list():
        """
        Provide dictionary collection
        :return: dict
        """

        container = collections.defaultdict(list)
        return container

    @staticmethod
    def parse_url(url):
        """
        Parse url

        :param str url: input url
        :return: dict
        """

        return urlparse(url)

    @staticmethod
    def to_json(data, sort=True, indents=4):
        """
        Json pretty print
        :param dict data: mixed data params
        :param bool sort: use sort
        :param int indents: space indents
        :return: str
        """

        json_data = json.dumps(data, sort_keys=sort, indent=indents)
        return json_data

    @staticmethod
    def openbrowser(target):
        """
        Open target path in local browser
        :param string target: url or local path
        :return: bool
        """

        return webbrowser.open(target)

    @staticmethod
    def percent(counter=0, total=1):
        """
        Return percentage
        :param int counter: current value
        :param int total: total value
        :return: str
        """

        return "{percent}%".format(percent=round(100.0 * counter / float(total), 1))

    @staticmethod
    def is_less(arg1, arg2):
        """
        Compare two numbers (< less)
        :param int arg1: right version
        :param int arg2: left version
        :return: bool
        """

        return LooseVersion(arg1) < LooseVersion(arg2)

    @staticmethod
    def is_more(arg1, arg2):
        """
        Compare two numbers (great >)
        :param int arg1: right version
        :param int arg2: left version
        :return: bool
        """

        return LooseVersion(arg1) > LooseVersion(arg2)

    @staticmethod
    def is_callable(func):
        """
        Check if function is callable

        :param callable func:
        :return: bool
        """

        return isinstance(func, collections.Callable)
