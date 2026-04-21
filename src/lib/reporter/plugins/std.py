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

from tabulate import tabulate

from .provider import PluginProvider
from src.core import sys


class StdReportPlugin(PluginProvider):
    """ StdReportPlugin class"""

    def __init__(self, target, data, directory=None):
        """
        PluginProvider constructor
        :param str target: target host
        :param dict data: result set
        """

        PluginProvider.__init__(self, target, data)
        self.directory = directory

    def process(self):
        """
        Process data
        :return: str
        """

        data = list(self._data.get('total').items())
        fingerprint = self._data.get('fingerprint')

        if isinstance(fingerprint, dict) and len(fingerprint) > 0:
            data += [
                ('fingerprint_category', fingerprint.get('category', 'custom')),
                ('fingerprint_name', fingerprint.get('name', 'Unknown custom stack')),
                ('fingerprint_confidence', '{0}%'.format(fingerprint.get('confidence', 0))),
            ]

            infrastructure = fingerprint.get('infrastructure')
            if isinstance(infrastructure, dict) and len(infrastructure) > 0:
                data += [
                    ('fingerprint_infra', infrastructure.get('provider', 'unknown')),
                    ('fingerprint_infra_confidence', '{0}%'.format(infrastructure.get('confidence', 0))),
                ]

        title = 'Statistics ({0})'.format(self._target)
        sys.writeln(tabulate(data, headers=[title, 'Summary'], tablefmt="psql"))
