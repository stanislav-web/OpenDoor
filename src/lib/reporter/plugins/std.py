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

from .provider import PluginProvider
from src.core import sys


class StdReportPlugin(PluginProvider):
    """ StdReportPlugin class"""

    @staticmethod
    def format_summary_table(rows, headers):
        """
        Render a small psql-like summary table without external dependencies.

        :param list[tuple] rows: summary rows
        :param list[str] headers: table headers
        :return: formatted table
        :rtype: str
        """

        safe_headers = [str(value) for value in headers]
        safe_rows = [(str(key), str(value)) for key, value in rows]

        first_width = max([len(safe_headers[0])] + [len(row[0]) for row in safe_rows])
        second_width = max([len(safe_headers[1])] + [len(row[1]) for row in safe_rows])

        border = '+-{0}-+-{1}-+'.format('-' * first_width, '-' * second_width)

        def render_row(first, second):
            """
            Render a padded summary row.

            :param str first: first column value
            :param str second: second column value
            :return: formatted row
            :rtype: str
            """

            return '| {0} | {1} |'.format(first.ljust(first_width), second.ljust(second_width))

        lines = [
            border,
            render_row(safe_headers[0], safe_headers[1]),
            border,
        ]

        for row in safe_rows:
            lines.append(render_row(row[0], row[1]))

        lines.append(border)

        return '\n'.join(lines)

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

        total = self._data.get('total')
        if not isinstance(total, dict):
            total = {}

        hidden_summary_keys = {'calibrated', 'ignored', 'bad', 'skip', 'items', 'workers'}
        data = [(key, value) for key, value in total.items() if key not in hidden_summary_keys]
        fingerprint = self._data.get('fingerprint')

        if isinstance(fingerprint, dict) and len(fingerprint) > 0:
            data += [
                ('fingerprint_name', fingerprint.get('name', 'Unknown custom stack')),
                ('fingerprint_confidence', '{0}%'.format(fingerprint.get('confidence', 0))),
            ]
            runtime = fingerprint.get('runtime')
            if isinstance(runtime, dict) and len(runtime) > 0:
                data += [('fingerprint_runtime', runtime.get('name', 'unknown'))]

            infrastructure = fingerprint.get('infrastructure')
            if isinstance(infrastructure, dict) and len(infrastructure) > 0:
                data += [('fingerprint_infra', infrastructure.get('provider', 'unknown'))]

            hsts = fingerprint.get('security_headers', {}).get('hsts', {})
            if isinstance(hsts, dict) and len(hsts) > 0:
                data += [('hsts', hsts.get('grade', 'missing'))]

            supercookie = fingerprint.get('privacy_risks', {}).get('supercookie', {})
            if isinstance(supercookie, dict) and len(supercookie) > 0:
                data += [('supercookie_risk', supercookie.get('risk', 'none'))]

                warnings = supercookie.get('warnings')
                if isinstance(warnings, (list, tuple)) and len(warnings) > 0:
                    data += [('privacy_supercookie_warnings', len(warnings))]

        title = 'Statistics ({0})'.format(self._target)
        sys.writeln(self.format_summary_table(data, [title, 'Summary']))
