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

from .providers import ResponseProvider
from src.core import helper
from .exceptions import ResponseError

class Response(ResponseProvider):
    """Response class"""

    def __init__(self, config, debug, **kwargs):
        """
        Response instance
        :param src.lib.browser.config.Config config: configurations
        :param src.lib.browser.debug.Debug debug: debugger
        """

        ResponseProvider.__init__(self)

        self.__cfg = config
        self.__debug = debug
        self.__tpl = kwargs.get('tpl')

        pass

    def handle(self, response, request_url, items_size, total_size):
        """
        Handle response
        :param urllib3.response.HTTPResponse response: response object
        :param str request_url: url from request
        :param int items_size: current items sizes
        :param int total_size: response object
        :raise ResponseError
        :return: dict
        """

        if self._HTTP_DBG_LEVEL <= self.__debug.level:
            self.__debug.debug_response(response.headers.items())

        if hasattr(response, 'status'):
            status = super(Response, self).detect(response.status)

            self.__debug.debug_request_uri(
                status=status,
                request_uri=request_url,
                items_size=items_size,
                total_size=total_size,
                content_size=self._get_content_size(response)
            )

            return (status , request_url)

        else:
            raise ResponseError('Unable to get response from {url}'.format(url=request_url))
        pass