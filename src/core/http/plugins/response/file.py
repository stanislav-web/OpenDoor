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


class FileResponsePlugin(ResponsePluginProvider):
    """ FileResponsePlugin class"""

    DESCRIPTION = 'File (detect large files)'
    RESPONSE_INDEX = 'file'
    DEFAULT_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    DEFAULT_SOURCE_DETECT_MIN_SIZE = 1000000

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
            if 'Content-Length' in self._headers:
                if self.DEFAULT_SOURCE_DETECT_MIN_SIZE <= int(self._headers['Content-Length']):
                    return self.RESPONSE_INDEX
                elif self.DEFAULT_SOURCE_DETECT_MIN_SIZE <= len(self._body):
                    return self.RESPONSE_INDEX
        return None
