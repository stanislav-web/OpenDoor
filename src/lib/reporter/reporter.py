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

import importlib

from src.core import filesystem, FileSystemError
from .exceptions import ReporterError


class Reporter(object):
    """Reporter class"""

    default = 'std'
    config = 'setup.cfg'

    @staticmethod
    def is_reported(resource):
        """
        Check if session is already reported
        :param str resource: target report
        :return: bool
        """

        try:
            config = filesystem.readcfg(Reporter.config)
            return filesystem.is_exist(config.get('opendoor', 'reports'), resource)
        except FileSystemError as e:
            raise ReporterError(e.message)

    @staticmethod
    def load(plugin_name, target, data):
        """
        Load report plugin
        :param str plugin_name: plugin name
        :param str target: target host
        :param dict data: report data
        :raise ReporterError
        :return: src.lib.reporter.plugins.provider.provider.PluginProvider
        """

        try:
            module = importlib.import_module('src.lib.reporter.plugins')

            try:
                report = getattr(module, plugin_name)
                return report(target, data)
            except (TypeError, AttributeError, Exception):
                raise ReporterError('Unable to get reporter `{plugin}`'.format(plugin=plugin_name))
        except ImportError:
            raise ReporterError('Unable to get report\'s plugins`')
