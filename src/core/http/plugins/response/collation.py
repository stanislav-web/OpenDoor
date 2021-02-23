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

from difflib import SequenceMatcher
from .provider import ResponsePluginProvider


class CollationResponsePlugin(ResponsePluginProvider):
    """ CollationResponsePlugin class"""

    DESCRIPTION = 'Collation (detect and ignore false positive success pages)'
    RESPONSE_INDEX = 'failed'
    DEFAULT_STATUSES = [100, 101, 200, 201, 202, 203, 204, 205, 206, 207, 208]
    MIN_RATIO_INDEX = 0.98
    MIN_CONTENT_LENGTH = 100

    def __init__(self):
        """
        ResponsePluginProvider constructor
        """

        ResponsePluginProvider.__init__(self)
        self.strong_false_item = {}
        self.previous_item = {}
        self.current_item = {}

    def process(self, response):
        """
        Process data
        :return: str
        """

        if response.status in self.DEFAULT_STATUSES:
            super().process(response)
            length = self.__get_content_length()
            if self.MIN_CONTENT_LENGTH < length:
                # the page is allowed for comparison

                if not self.previous_item:
                    # 1st match. Push items for next compare step
                    self.previous_item.update({'length': length, 'text': self._body})
                    return None
                else:
                    if length == self.previous_item.get('length') and self.MIN_CONTENT_LENGTH < length:
                        # identical, seems to drop failed for success
                        return self.RESPONSE_INDEX
                    else:
                        matcher = SequenceMatcher(a=self.previous_item['text'], b=self._body)
                        matcher.get_matching_blocks()

                        if 'length' in self.current_item:
                            next_matcher = SequenceMatcher(a=self.current_item['text'], b=self._body)
                            if next_matcher.ratio() == matcher.ratio():
                                return self.RESPONSE_INDEX
                        if self.MIN_RATIO_INDEX < matcher.ratio():
                            return self.RESPONSE_INDEX
                        else:
                            self.current_item.update({'length': length, 'text': self._body})

                    if self.MIN_CONTENT_LENGTH < length:
                        self.previous_item.update({'length': length, 'text': self._body})
        return None

    def __get_content_length(self):
        """
        Get content length
        :return: int
        """

        length = 0
        if 'Content-Length' in self._headers:
            if 0 < int(self._headers['Content-Length']):
                length = self._headers['Content-Length']
        else:
            length = len(self._body)
        return int(length)
