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

from src.core import filesystem
from .exceptions import ReporterError
import importlib

class Reporter():
    """Reporter class"""

    @staticmethod
    def is_reported(resource):
        """
        Check if session is already reported
        :param str resource: target report
        :return: bool
        """

        config = filesystem.readcfg('setup.cfg')
        return filesystem.is_exist(config.get('opendoor', 'reports'), resource)

    @staticmethod
    def get(plugin_name):
        """
        Get report plugin
        :param str plugin_name: plugin name
        :return: src.lib.reporter.plugins.provider.provider.PluginProvider
        """

        try:

            module = importlib.import_module('src.lib.reporter.plugins')
            reporter = getattr(module, plugin_name)

            return reporter

        except AttributeError:
            raise ReporterError('Unable to get reporter`{plugin}`'.format(plugin=plugin_name))
