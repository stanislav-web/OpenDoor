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


class SocketError(Exception):

    """SocketError class"""

    def __init__(self, message):
        """
        SocketError class constructor
        :param str message: error message
        """

        super(SocketError, self).__init__(message)


class ProxyRequestError(Exception):
    """ProxyRequestError class"""

    def __init__(self, message):
        """
        ProxyRequestError class constructor
        :param str message: error message
        """

        super(ProxyRequestError, self).__init__(message)


class HttpRequestError(Exception):
    """HttpRequestError class"""

    def __init__(self, message):
        """
        HttpRequestError class constructor
        :param str message: error message
        """

        super(HttpRequestError, self).__init__(message)


class HttpsRequestError(Exception):
    """HttpsRequestError class"""

    def __init__(self, message):
        """
        HttpsRequestError class constructor
        :param str message: error message
        """

        super(HttpsRequestError, self).__init__(message)


class ResponseError(Exception):
    """ResponseError class"""

    def __init__(self, message):
        """
        ResponseError class constructor
        :param str message: error message
        """

        super(ResponseError, self).__init__(message)
