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

import importlib
from .exceptions import ResponsePluginError


class ResponsePlugin(object):
    """ResponsePlugin class"""

    @staticmethod
    def load(plugin_name):
        """
        Load response plugin
        :param str plugin_name:  response plugin name
        :raise ResponsePluginError
        :return: src.core.http.plugins.response.provider.provider.ResponsePluginProvider
        """

        try:
            package_module = importlib.import_module('src.core.http.plugins.response')

            try:
                response_plugin = getattr(package_module, plugin_name)
                return response_plugin()
            except (TypeError, AttributeError, Exception) as error:
                raise ResponsePluginError('Unable to get response plugin `{plugin}`. Reason: {error}'
                                          .format(plugin=plugin_name, error=error))
        except ImportError:
            raise ResponsePluginError('Unable to get response\'s plugins')
