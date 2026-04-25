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
    """Skip responses matching exact KB sizes or KB ranges."""

    DESCRIPTION = 'SkipSizesStatuses (skip target sizes of page: {} kbs for 200 OK redirects)'
    RESPONSE_INDEX = 'skip'
    DEFAULT_STATUSES = [200]
    SIZE_VALUES = None

    def __init__(self, values):
        """
        ResponsePluginProvider constructor.

        :param values: exact KB values and/or ranges separated by ":"
        :type values: str | None
        """

        self.SIZE_VALUES = []
        self.RANGE_VALUES = []

        if values is not None:
            raw_values = Helper.to_list(values, ':')

            for raw_value in raw_values:
                item = str(raw_value).strip()

                if '-' in item:
                    bounds = item.split('-', 1)
                    if len(bounds) == 2 and bounds[0].strip().isdigit() and bounds[1].strip().isdigit():
                        start_kb = int(bounds[0].strip())
                        end_kb = int(bounds[1].strip())

                        if end_kb < start_kb:
                            start_kb, end_kb = end_kb, start_kb

                        self.RANGE_VALUES.append((start_kb * 1024, end_kb * 1024))
                        continue

                self.SIZE_VALUES.append(str(item) + 'KB')

            size_string = ','.join(raw_values)
            self.DESCRIPTION = self.DESCRIPTION.format(size_string)

        ResponsePluginProvider.__init__(self)

    def _extract_content_length(self):
        """
        Extract effective response length.

        :return: content length from header or None when unavailable/invalid
        :rtype: int | None
        """

        if 'Content-Length' not in self._headers:
            return None

        try:
            return int(self._headers['Content-Length'])
        except Exception:
            return None

    def _matches_exact_size(self, size_bytes):
        """
        Check whether byte size matches any exact configured KB size.

        :param size_bytes: effective response size in bytes
        :type size_bytes: int
        :return: True when exact size matches
        :rtype: bool
        """

        for size in self.SIZE_VALUES:
            if size == FileSystem.human_size(size_bytes, 0):
                return True

        return False

    def _matches_range_size(self, size_bytes):
        """
        Check whether byte size matches any configured KB range.

        :param size_bytes: effective response size in bytes
        :type size_bytes: int
        :return: True when size is within any configured range
        :rtype: bool
        """

        for min_size, max_size in self.RANGE_VALUES:
            if min_size <= size_bytes <= max_size:
                return True

        return False

    def process(self, response):
        """
        Process the given response data.

        :param response: The response object to be processed.
        :type response: object
        :return: The response index if the data meets the specified conditions, otherwise None.
        :rtype: str or None
        """

        if not hasattr(response, 'status') or response.status not in self.DEFAULT_STATUSES:
            return None

        super().process(response)

        size_bytes = self._extract_content_length()
        if size_bytes is None:
            size_bytes = len(self._body)

        if self._matches_exact_size(size_bytes):
            return self.RESPONSE_INDEX

        if self._matches_range_size(size_bytes):
            return self.RESPONSE_INDEX

        return None