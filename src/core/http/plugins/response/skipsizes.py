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

from .provider import ResponsePluginProvider
from src.core.filesystem import FileSystem
from src.core.helper import Helper


class SkipSizesResponsePlugin(ResponsePluginProvider):
    """ SkipSizesResponsePlugin class"""

    DESCRIPTION = 'SkipSizesStatuses (skip target sizes of page: {} kbs for 200 OK redirects)'
    RESPONSE_INDEX = 'skip'
    DEFAULT_STATUSES = [200]
    SIZE_VALUES = None

    def __init__(self, values):
        """
        ResponsePluginProvider constructor
        """
        if values is not None:
            self.SIZE_VALUES = Helper.to_list(values, ':')
            size_list = list(map(lambda x: str(x)+'KB', self.SIZE_VALUES))
            size_string = ','.join(self.SIZE_VALUES)
            self.DESCRIPTION = self.DESCRIPTION.format(size_string)
            self.SIZE_VALUES = size_list
        ResponsePluginProvider.__init__(self)

    def process(self, response):
        """
        Process the given response data.

        :param response: The response object to be processed.
        :type response: object
        :return: The response index if the data meets the specified conditions, otherwise None.
        :rtype: str or None
        """
        if hasattr(response, 'status') and response.status in self.DEFAULT_STATUSES:
            super().process(response)
            if 'Content-Length' in self._headers:
                for size in self.SIZE_VALUES:
                    if size == FileSystem.human_size(int(self._headers['Content-Length']), 0):
                        return self.RESPONSE_INDEX
            else:
                for size in self.SIZE_VALUES:
                    if size == FileSystem.human_size(len(self._body), 0):
                        return self.RESPONSE_INDEX
        return None
