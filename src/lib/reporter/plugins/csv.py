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

import csv
import os

from .provider import PluginProvider
from src.core import CoreConfig
from src.core import filesystem, FileSystemError
from src.lib import tpl


class CsvReportPlugin(PluginProvider):
    """CsvReportPlugin class."""

    PLUGIN_NAME = 'CsvReport'
    EXTENSION_SET = '.csv'
    FAILED_STATUS = 'failed'
    COLUMNS = [
        'target',
        'status',
        'url',
        'code',
        'size',
        'waf',
        'waf_confidence',
        'waf_signals',
        'bypass',
        'bypass_profile',
        'bypass_header',
        'bypass_value',
        'bypass_variant',
        'bypass_url',
        'bypass_from_status',
        'bypass_to_status',
        'bypass_from_code',
        'bypass_to_code',
        'bypass_score',
        'bypass_reasons',
        'stacktrace_detection',
        'stacktrace_runtime',
        'stacktrace_signal',
        'stacktrace_confidence',
        'fingerprint_category',
        'fingerprint_name',
        'fingerprint_confidence',
        'runtime_name',
        'runtime_confidence',
        'infrastructure_provider',
        'infrastructure_confidence',
        'hsts_present',
        'hsts_grade',
        'hsts_max_age',
        'hsts_include_subdomains',
        'hsts_preload',
        'hsts_preload_ready',
        'hsts_http_to_https_redirect',
        'hsts_warnings',
        'privacy_supercookie_risk',
        'privacy_supercookie_score',
        'privacy_supercookie_hsts_tracking_surface',
        'privacy_supercookie_etag_tracking_surface',
        'privacy_supercookie_cache_tracking_surface',
        'privacy_supercookie_persistent_cookie_surface',
        'privacy_supercookie_warnings',
        'privacy_supercookie_signals',
    ]

    def __init__(self, target, data, directory=None):
        """
        PluginProvider constructor.

        :param str target: target host
        :param dict data: result set
        :param str directory: custom directory
        """

        PluginProvider.__init__(self, target, data)

        try:
            if directory is None:
                directory = CoreConfig.get('data').get('reports')
            self.__target_dir = filesystem.makedir(os.path.join(directory, self._target))
        except FileSystemError as error:
            raise Exception(error)

    @staticmethod
    def __format_list(value):
        """
        Convert list values into a stable CSV cell value.

        :param list|mixed value: source value
        :return: str
        """

        if isinstance(value, list):
            return ';'.join([str(item) for item in value])
        if value is None:
            return ''
        return str(value)

    def __fingerprint_fields(self):
        """
        Build target-level fingerprint columns shared by all CSV item rows.

        :return: dict
        """

        fingerprint = self._data.get('fingerprint')
        if not isinstance(fingerprint, dict) or len(fingerprint) == 0:
            return {
                'fingerprint_category': '',
                'fingerprint_name': '',
                'fingerprint_confidence': '',
                'runtime_name': '',
                'runtime_confidence': '',
                'infrastructure_provider': '',
                'infrastructure_confidence': '',
                'hsts_present': '',
                'hsts_grade': '',
                'hsts_max_age': '',
                'hsts_include_subdomains': '',
                'hsts_preload': '',
                'hsts_preload_ready': '',
                'hsts_http_to_https_redirect': '',
                'hsts_warnings': '',
                'privacy_supercookie_risk': '',
                'privacy_supercookie_score': '',
                'privacy_supercookie_hsts_tracking_surface': '',
                'privacy_supercookie_etag_tracking_surface': '',
                'privacy_supercookie_cache_tracking_surface': '',
                'privacy_supercookie_persistent_cookie_surface': '',
                'privacy_supercookie_warnings': '',
                'privacy_supercookie_signals': '',
            }

        runtime = fingerprint.get('runtime')
        if not isinstance(runtime, dict):
            runtime = {}

        infrastructure = fingerprint.get('infrastructure')
        if not isinstance(infrastructure, dict):
            infrastructure = {}

        security_headers = fingerprint.get('security_headers')
        if not isinstance(security_headers, dict):
            security_headers = {}
        hsts = security_headers.get('hsts')
        if not isinstance(hsts, dict):
            hsts = {}

        privacy_risks = fingerprint.get('privacy_risks')
        if not isinstance(privacy_risks, dict):
            privacy_risks = {}
        supercookie = privacy_risks.get('supercookie')
        if not isinstance(supercookie, dict):
            supercookie = {}

        return {
            'fingerprint_category': str(fingerprint.get('category', 'custom')),
            'fingerprint_name': str(fingerprint.get('name', 'Unknown custom stack')),
            'fingerprint_confidence': str(fingerprint.get('confidence', 0)),
            'runtime_name': str(runtime.get('name', '')),
            'runtime_confidence': str(runtime.get('confidence', '')),
            'infrastructure_provider': str(infrastructure.get('provider', '')),
            'infrastructure_confidence': str(infrastructure.get('confidence', '')),
            'hsts_present': str(hsts.get('present', '')),
            'hsts_grade': str(hsts.get('grade', '')),
            'hsts_max_age': '' if hsts.get('max_age') is None else str(hsts.get('max_age')),
            'hsts_include_subdomains': str(hsts.get('include_subdomains', '')),
            'hsts_preload': str(hsts.get('preload', '')),
            'hsts_preload_ready': str(hsts.get('preload_ready', '')),
            'hsts_http_to_https_redirect': str(hsts.get('http_to_https_redirect', '')),
            'hsts_warnings': self.__format_list(hsts.get('warnings', [])),
            'privacy_supercookie_risk': str(supercookie.get('risk', '')),
            'privacy_supercookie_score': '' if supercookie.get('score') is None else str(supercookie.get('score')),
            'privacy_supercookie_hsts_tracking_surface': str(supercookie.get('hsts_tracking_surface', '')),
            'privacy_supercookie_etag_tracking_surface': str(supercookie.get('etag_tracking_surface', '')),
            'privacy_supercookie_cache_tracking_surface': str(supercookie.get('cache_tracking_surface', '')),
            'privacy_supercookie_persistent_cookie_surface': str(supercookie.get('persistent_cookie_surface', '')),
            'privacy_supercookie_warnings': self.__format_list(supercookie.get('warnings', [])),
            'privacy_supercookie_signals': self.__format_list(supercookie.get('signals', [])),
        }

    def __build_rows(self):
        """
        Build CSV rows from detailed report items.

        :return: list
        """

        rows = []
        fingerprint_fields = self.__fingerprint_fields()

        for status in self._data.get('items', {}).keys():
            if status == self.FAILED_STATUS:
                continue

            for item in self.get_report_items(status):
                if not isinstance(item, dict):
                    item = {'url': str(item), 'code': '-', 'size': '0B'}

                row = {
                    'target': self._target,
                    'status': str(status),
                    'url': str(item.get('url', '')),
                    'code': str(item.get('code', '-')),
                    'size': str(item.get('size', '0B')),
                    'waf': str(item.get('waf', '')),
                    'waf_confidence': '' if item.get('waf_confidence') is None else str(item.get('waf_confidence')),
                    'waf_signals': self.__format_list(item.get('waf_signals', [])),
                    'bypass': str(item.get('bypass', '')),
                    'bypass_profile': str(item.get('bypass_profile', '')),
                    'bypass_header': str(item.get('bypass_header', '')),
                    'bypass_value': str(item.get('bypass_value', '')),
                    'bypass_variant': str(item.get('bypass_variant', '')),
                    'bypass_url': str(item.get('bypass_url', '')),
                    'bypass_from_status': str(item.get('bypass_from_status', '')),
                    'bypass_to_status': str(item.get('bypass_to_status', '')),
                    'bypass_from_code': '' if item.get('bypass_from_code') is None else str(
                        item.get('bypass_from_code')
                    ),
                    'bypass_to_code': '' if item.get('bypass_to_code') is None else str(item.get('bypass_to_code')),
                    'bypass_score': '' if item.get('bypass_score') is None else str(item.get('bypass_score')),
                    'bypass_reasons': self.__format_list(item.get('bypass_reasons', [])),
                    'stacktrace_detection': '',
                    'stacktrace_runtime': '',
                    'stacktrace_signal': '',
                    'stacktrace_confidence': '',
                }
                stacktrace_detection = item.get('stacktrace_detection')
                if isinstance(stacktrace_detection, dict):
                    row.update({
                        'stacktrace_detection': str(stacktrace_detection.get('type', '')),
                        'stacktrace_runtime': str(stacktrace_detection.get('runtime', '')),
                        'stacktrace_signal': str(stacktrace_detection.get('signal', '')),
                        'stacktrace_confidence': '' if stacktrace_detection.get('confidence') is None else str(
                            stacktrace_detection.get('confidence')
                        ),
                    })
                row.update(fingerprint_fields)
                rows.append(row)

        return rows

    def process(self):
        """
        Persist report data into a CSV file with stable columns.

        :return: None
        """

        report_path = os.path.join(self.__target_dir, self._target + self.EXTENSION_SET)

        try:
            filesystem.clear(self.__target_dir, extension=self.EXTENSION_SET)
            report_path = filesystem.makefile(report_path)

            with open(report_path, 'w', newline='', encoding='utf-8') as handler:
                writer = csv.DictWriter(handler, fieldnames=self.COLUMNS)
                writer.writeheader()
                writer.writerows(self.__build_rows())

            tpl.info(key='report', plugin=self.PLUGIN_NAME, dest=filesystem.getabsname(report_path))
        except (csv.Error, OSError, FileSystemError, TypeError, ValueError) as error:
            raise Exception(error)