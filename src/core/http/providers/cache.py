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

    Development: Stanislav WEB
"""

class CacheControlProvider(object):
    """Cache-Control request header provider."""

    DEFAULT_CACHE_CONTROL = 'max-age=0'

    @property
    def _cache_control(self):
        """
        Get the default Cache-Control request header value.

        :return: Cache-Control header value.
        :rtype: str
        """

        return self.DEFAULT_CACHE_CONTROL
