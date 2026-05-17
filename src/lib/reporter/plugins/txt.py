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

import os

from .provider import PluginProvider
from src.core import CoreConfig
from src.core import filesystem, FileSystemError


class TextReportPlugin(PluginProvider):
    """ TextReportPlugin class"""

    PLUGIN_NAME = 'TextReport'
    EXTENSION_SET = '.txt'

    def __init__(self, target, data, directory=None):
        """
        PluginProvider constructor
        :param str target: target host
        :param dict data: result set
        :param str directory: custom directory
        """
        PluginProvider.__init__(self, target, data)
        try:
            if None is directory:
                directory = CoreConfig.get('data').get('reports')
            self.__target_dir = filesystem.makedir(os.path.join(directory, self._target))
        except FileSystemError as error:
            raise Exception(error)

    @staticmethod
    def __format_signal_item(signal):
        """
        Format one fingerprint signal into a compact txt-report value.

        :param dict|mixed signal: signal payload
        :return: formatted signal
        :rtype: str
        """

        if isinstance(signal, dict):
            signal_type = signal.get('type') or signal.get('source') or signal.get('kind') or 'signal'
            signal_value = signal.get('value') or signal.get('name') or signal.get('marker') or signal.get('header') or ''
            signal_weight = signal.get('weight') or signal.get('score')

            value = '{0}:{1}'.format(signal_type, signal_value) if signal_value else str(signal_type)

            if signal_weight is not None:
                value = '{0}({1})'.format(value, signal_weight)

            return value

        return str(signal)

    @classmethod
    def __format_signal_list(cls, value):
        """
        Format fingerprint evidence lists for plain txt reports.

        :param list|tuple|mixed value: signal list or scalar value
        :return: formatted signal list
        :rtype: str
        """

        if value is None:
            return ''

        if isinstance(value, (list, tuple)):
            items = [
                cls.__format_signal_item(item)
                for item in value
                if item is not None and str(item) != ''
            ]

            return '; '.join(items)

        return str(value)

    def format_fingerprint_summary(self):
        fingerprint = self._data.get('fingerprint')
        if not isinstance(fingerprint, dict) or len(fingerprint) == 0:
            return []
        rows = [
            'category: {0}'.format(fingerprint.get('category', 'custom')),
            'name: {0}'.format(fingerprint.get('name', 'Unknown custom stack')),
            'confidence: {0}%'.format(fingerprint.get('confidence', 0)),
        ]
        fingerprint_signals = self.__format_signal_list(fingerprint.get('signals'))
        if fingerprint_signals:
            rows.append('signals: {0}'.format(fingerprint_signals))
        runtime = fingerprint.get('runtime')
        if isinstance(runtime, dict) and len(runtime) > 0:
            rows.extend(['runtime: {0}'.format(runtime.get('name', 'unknown')), 'runtime_confidence: {0}%'.format(runtime.get('confidence', 0))])
            runtime_signals = self.__format_signal_list(runtime.get('signals'))
            if runtime_signals:
                rows.append('runtime_signals: {0}'.format(runtime_signals))
        infrastructure = fingerprint.get('infrastructure')
        if isinstance(infrastructure, dict) and len(infrastructure) > 0:
            rows.extend(['infrastructure: {0}'.format(infrastructure.get('provider', 'unknown')), 'infrastructure_confidence: {0}%'.format(infrastructure.get('confidence', 0))])
            infrastructure_signals = self.__format_signal_list(infrastructure.get('signals'))
            if infrastructure_signals:
                rows.append('infrastructure_signals: {0}'.format(infrastructure_signals))
        hsts = fingerprint.get('security_headers', {}).get('hsts', {})
        if isinstance(hsts, dict) and len(hsts) > 0:
            rows.extend([
                'hsts: {0}'.format(hsts.get('grade', 'missing')),
                'hsts_max_age: {0}'.format('-' if hsts.get('max_age') is None else hsts.get('max_age')),
                'hsts_include_subdomains: {0}'.format(hsts.get('include_subdomains', False)),
                'hsts_preload_ready: {0}'.format(hsts.get('preload_ready', False)),
            ])
        hsts_warnings = self.__format_signal_list(hsts.get('warnings'))
        if hsts_warnings:
            rows.append('hsts_warnings: {0}'.format(hsts_warnings))
        supercookie = fingerprint.get('privacy_risks', {}).get('supercookie', {})
        if isinstance(supercookie, dict) and len(supercookie) > 0:
            rows.extend([
                'supercookie_risk: {0}'.format(supercookie.get('risk', 'none')),
                'supercookie_score: {0}'.format(supercookie.get('score', 0)),
                'supercookie_hsts_tracking_surface: {0}'.format(
                    supercookie.get('hsts_tracking_surface', False)
                ),
                'supercookie_etag_tracking_surface: {0}'.format(
                    supercookie.get('etag_tracking_surface', False)
                ),
                'supercookie_cache_tracking_surface: {0}'.format(
                    supercookie.get('cache_tracking_surface', False)
                ),
                'supercookie_persistent_surface: {0}'.format(
                    supercookie.get('persistent_cookie_surface', False)
                ),
            ])
            supercookie_warnings = self.__format_signal_list(supercookie.get('warnings'))
            if supercookie_warnings:
                rows.append('privacy_supercookie_warnings: {0}'.format(supercookie_warnings))
            supercookie_signals = self.__format_signal_list(supercookie.get('signals'))
            if supercookie_signals:
                rows.append('supercookie_signals: {0}'.format(supercookie_signals))
        return rows

    def process(self):
        """
        Process data
        :return: str
        """
        items = self._data.get('items')
        if not isinstance(items, dict):
            items = {}
        resultset = items.items()
        try:
            filesystem.clear(self.__target_dir, extension=self.EXTENSION_SET)
            for status, _ in resultset:
                if status not in ['failed']:
                    data = [self.format_report_item(item) for item in self.get_report_items(status)]
                    self.record(self.__target_dir, status, data, '\n')
            fingerprint_data = self.format_fingerprint_summary()
            if len(fingerprint_data) > 0:
                self.record(self.__target_dir, 'fingerprint', fingerprint_data, '\n')
        except (Exception, FileSystemError) as error:
            raise Exception(error)
