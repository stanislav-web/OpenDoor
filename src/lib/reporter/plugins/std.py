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

        total = self._data.get('total')
        if not isinstance(total, dict):
            total = {}
        data = list(total.items())
        fingerprint = self._data.get('fingerprint')

        if isinstance(fingerprint, dict) and len(fingerprint) > 0:
            data += [
                ('fingerprint_category', fingerprint.get('category', 'custom')),
                ('fingerprint_name', fingerprint.get('name', 'Unknown custom stack')),
                ('fingerprint_confidence', '{0}%'.format(fingerprint.get('confidence', 0))),
            ]


            fingerprint_signals = fingerprint.get('signals')
            if isinstance(fingerprint_signals, (list, tuple)) and len(fingerprint_signals) > 0:
                data += [('fingerprint_signals', len(fingerprint_signals))]
            runtime = fingerprint.get('runtime')
            if isinstance(runtime, dict) and len(runtime) > 0:
                data += [('fingerprint_runtime', runtime.get('name', 'unknown')), ('fingerprint_runtime_confidence', '{0}%'.format(runtime.get('confidence', 0)))]
                runtime_signals = runtime.get('signals')
                if isinstance(runtime_signals, (list, tuple)) and len(runtime_signals) > 0:
                    data += [('fingerprint_runtime_signals', len(runtime_signals))]

            infrastructure = fingerprint.get('infrastructure')
            if isinstance(infrastructure, dict) and len(infrastructure) > 0:
                data += [
                    ('fingerprint_infra', infrastructure.get('provider', 'unknown')),
                    ('fingerprint_infra_confidence', '{0}%'.format(infrastructure.get('confidence', 0))),
                ]

                infrastructure_signals = infrastructure.get('signals')
                if isinstance(infrastructure_signals, (list, tuple)) and len(infrastructure_signals) > 0:
                    data += [('fingerprint_infra_signals', len(infrastructure_signals))]

            hsts = fingerprint.get('security_headers', {}).get('hsts', {})
            if isinstance(hsts, dict) and len(hsts) > 0:
                data += [
                    ('hsts', hsts.get('grade', 'missing')),
                    ('hsts_max_age', '-' if hsts.get('max_age') is None else hsts.get('max_age')),
                    ('hsts_include_subdomains', hsts.get('include_subdomains', False)),
                    ('hsts_preload_ready', hsts.get('preload_ready', False)),
                ]

            supercookie = fingerprint.get('privacy_risks', {}).get('supercookie', {})
            if isinstance(supercookie, dict) and len(supercookie) > 0:
                data += [
                    ('privacy_supercookie_risk', supercookie.get('risk', 'none')),
                    ('privacy_supercookie_score', supercookie.get('score', 0)),
                    ('privacy_supercookie_hsts', supercookie.get('hsts_tracking_surface', False)),
                    ('privacy_supercookie_etag', supercookie.get('etag_tracking_surface', False)),
                    ('privacy_supercookie_cache', supercookie.get('cache_tracking_surface', False)),
                    ('privacy_supercookie_cookie', supercookie.get('persistent_cookie_surface', False)),
                ]

                warnings = supercookie.get('warnings')
                if isinstance(warnings, (list, tuple)) and len(warnings) > 0:
                    data += [('privacy_supercookie_warnings', len(warnings))]

        title = 'Statistics ({0})'.format(self._target)
        sys.writeln(tabulate(data, headers=[title, 'Summary'], tablefmt="psql"))
