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


class DebugProvider(object):
    """ DebugProvider class"""

    @property
    def level(self):
        """
        Get debug level
        :return: int
        """

        return None


    def is_scan_debug(self):
        """Return True for scanner decision debug output."""

        return False

    def is_request_debug(self):
        """Return True for outgoing request debug output."""

        return False

    def is_response_debug(self):
        """Return True for incoming response debug output."""

        return False

    def debug_user_agents(self):
        """
        Debug info for user agent
        :return: bool
        """

        pass

    def debug_connection_pool(self, keymsg, pool, connection_type):
        """
        Debug connection pool message
        :param str keymsg: tpl key
        :param object pool: pool object
        :param object connection_type: type string
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

    def debug_load_sniffer_plugin(self, description):
        """
        Debug load sniffers plugin
        :param str description: plugin description
        :return: bool
        """

        pass
    def debug_cookie_accept_enabled(self):
        """Debug active cookie routing."""

        pass

    def debug_cookie_accepted(self, cookies):
        """Debug accepted response cookies."""

        pass

    def debug_cookie_attached(self, headers):
        """Debug attached request cookies."""

        pass

    def debug_auto_calibration_enabled(self):
        """Debug auto-calibration configuration."""

        pass

    def debug_header_bypass_skipped(self, status):
        """Debug skipped header-bypass probe."""

        pass

    def debug_header_bypass_probing(self, status, variants):
        """Debug header-bypass probe start."""

        pass

    def debug_header_bypass_candidate(self, metadata):
        """Debug promising header-bypass candidate."""

        pass

    def debug_header_bypass_finished(self):
        """Debug header-bypass probe completion."""

        pass

    def debug_recursive_expansion(self, parent_url, child_count, next_depth):
        """Debug recursive queue expansion."""

        pass

    def debug_classification(self, status, **kwargs):
        """Debug response classification summary."""

        pass
