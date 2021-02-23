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

import re
from .provider import ResponsePluginProvider


class IndexofResponsePlugin(ResponsePluginProvider):
    """ IndexofResponsePlugin class"""

    DESCRIPTION = 'IndexOf (detect Index Of/ Apache directories)'
    RESPONSE_INDEX = 'indexof'
    DEFAULT_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    INDEX_OF_TITLE = 'Index of /'

    def __init__(self):
        """
        ResponsePluginProvider constructor
        """

        ResponsePluginProvider.__init__(self)

    def process(self, response):
        """
        Process data
        :return: str
        """

        if response.status in self.DEFAULT_STATUSES:
            super().process(response)

            if 0 < len(self._body):
                title = re.search('<title>(.+?)</title>', self._body, re.IGNORECASE | re.DOTALL)
                if None is not title and None is not re.search(self.INDEX_OF_TITLE, title.group(1), re.IGNORECASE):
                    return self.RESPONSE_INDEX
            return None
