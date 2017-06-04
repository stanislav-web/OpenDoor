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


class DebugProvider(object):
    """ DebugProvider class"""

    @property
    def level(self):
        """
        Get debug level
        :return: int
        """

        return None

    def debug_user_agents(self):
        """
        Debug info for user agent
        :return: bool
        """

        pass

    def debug_connection_pool(self, keymsg, pool):
        """
        Debug connection pool message
        :param str keymsg: tpl key
        :param object pool: pool object
        :return: bool
        """

        pass

    def debug_proxy_pool(self):
        """
        Debug proxy pool message
        :return: bool
        """

        pass

    def debug_list(self, total_lines):
        """
        Debug scan list
        :param int total_lines: total list lines
        :return: bool
        """

        pass

    def debug_request(self, request_header, url, method):
        """
        Debug request
        :param dict request_header: request header
        :param str url: request url
        :param str method: request method
        :return: bool
        """

        pass

    def debug_response(self, response_header):
        """
        Debug response
        :param dict response_header: response header
        :return: bool
        """

        pass

    def debug_request_uri(self, status, request_uri, **kwargs):
        """
        Debug request_uri
        :param int status: response status
        :param str request_uri: request urli
        :return: bool
        """

        pass

