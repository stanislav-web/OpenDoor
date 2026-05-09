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
import sqlite3

from .provider import PluginProvider
from src.core import CoreConfig
from src.core import filesystem, FileSystemError
from src.lib import tpl


class SqliteReportPlugin(PluginProvider):
    """SqliteReportPlugin class."""

    PLUGIN_NAME = 'SqliteReport'
    EXTENSION_SET = '.sqlite'

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

    def process(self):
        """
        Persist report data into a SQLite database.

        :return: None
        """

        database_path = os.path.join(self.__target_dir, self._target + self.EXTENSION_SET)
        connection = None

        try:
            filesystem.clear(self.__target_dir, extension=self.EXTENSION_SET)
            filesystem.makefile(database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            cursor.execute('CREATE TABLE summary (status TEXT PRIMARY KEY, total INTEGER NOT NULL)')
            cursor.execute(
                'CREATE TABLE items ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'status TEXT NOT NULL, '
                'url TEXT NOT NULL, '
                'code TEXT NOT NULL, '
                'size TEXT NOT NULL, '
                'bypass TEXT, '
                'bypass_profile TEXT, '
                'bypass_header TEXT, '
                'bypass_value TEXT, '
                'bypass_variant TEXT, '
                'bypass_url TEXT, '
                'bypass_from_status TEXT, '
                'bypass_to_status TEXT, '
                'bypass_from_code TEXT, '
                'bypass_to_code TEXT, '
                'bypass_score INTEGER, '
                'bypass_reasons TEXT, '
                'debug_detection TEXT, '
                'debug_runtime TEXT, '
                'debug_signal TEXT, '
                'debug_confidence INTEGER'
                ')'
            )
            cursor.execute(
                'CREATE TABLE fingerprint ('
                'id INTEGER PRIMARY KEY CHECK (id = 1), '
                'category TEXT NOT NULL, '
                'name TEXT NOT NULL, '
                'confidence INTEGER NOT NULL, '
                'runtime_name TEXT, '
                'runtime_confidence INTEGER, '
                'infrastructure_provider TEXT, '
                'infrastructure_confidence INTEGER, '
                'hsts_present INTEGER, '
                'hsts_grade TEXT, '
                'hsts_max_age INTEGER, '
                'hsts_include_subdomains INTEGER, '
                'hsts_preload INTEGER, '
                'hsts_preload_ready INTEGER, '
                'hsts_http_to_https_redirect INTEGER, '
                'hsts_warnings TEXT, '
                'privacy_supercookie_risk TEXT, '
                'privacy_supercookie_score INTEGER, '
                'privacy_supercookie_hsts_tracking_surface INTEGER, '
                'privacy_supercookie_etag_tracking_surface INTEGER, '
                'privacy_supercookie_cache_tracking_surface INTEGER, '
                'privacy_supercookie_persistent_cookie_surface INTEGER, '
                'privacy_supercookie_warnings TEXT, '
                'privacy_supercookie_signals TEXT'
                ')'
            )
            cursor.execute(
                'CREATE TABLE runtime_signals ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'type TEXT NOT NULL, '
                'value TEXT NOT NULL'
                ')'
            )
            cursor.execute(
                'CREATE TABLE fingerprint_signals ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'type TEXT NOT NULL, '
                'value TEXT NOT NULL'
                ')'
            )

            cursor.executemany(
                'INSERT INTO metadata(key, value) VALUES(?, ?)',
                [
                    ('target', self._target),
                    ('plugin', self.PLUGIN_NAME),
                ]
            )

            cursor.executemany(
                'INSERT INTO summary(status, total) VALUES(?, ?)',
                [
                    (str(status), int(total))
                    for status, total in self._data.get('total', {}).items()
                ]
            )

            rows = []
            for status in self._data.get('items', {}).keys():
                for item in self.get_report_items(status):
                    debug_detection = item.get('debug_detection')
                    if not isinstance(debug_detection, dict):
                        debug_detection = {}

                    rows.append(
                        (
                            str(status),
                            str(item.get('url', '')),
                            str(item.get('code', '-')),
                            str(item.get('size', '0B')),
                            None if item.get('bypass') is None else str(item.get('bypass')),
                            None if item.get('bypass_profile') is None else str(item.get('bypass_profile')),
                            None if item.get('bypass_header') is None else str(item.get('bypass_header')),
                            None if item.get('bypass_value') is None else str(item.get('bypass_value')),
                            None if item.get('bypass_variant') is None else str(item.get('bypass_variant')),
                            None if item.get('bypass_url') is None else str(item.get('bypass_url')),
                            None if item.get('bypass_from_status') is None else str(item.get('bypass_from_status')),
                            None if item.get('bypass_to_status') is None else str(item.get('bypass_to_status')),
                            None if item.get('bypass_from_code') is None else str(item.get('bypass_from_code')),
                            None if item.get('bypass_to_code') is None else str(item.get('bypass_to_code')),
                            None if item.get('bypass_score') is None else int(item.get('bypass_score')),
                            None if item.get('bypass_reasons') is None else ';'.join([
                                str(reason) for reason in item.get('bypass_reasons', [])
                            ]),
                            None if debug_detection.get('type') is None else str(debug_detection.get('type')),
                            None if debug_detection.get('runtime') is None else str(debug_detection.get('runtime')),
                            None if debug_detection.get('signal') is None else str(debug_detection.get('signal')),
                            None if debug_detection.get('confidence') is None else int(debug_detection.get('confidence')),
                        )
                    )

            if len(rows) > 0:
                cursor.executemany(
                    'INSERT INTO items('
                    'status, url, code, size, '
                    'bypass, bypass_profile, bypass_header, bypass_value, bypass_variant, bypass_url, '
                    'bypass_from_status, bypass_to_status, bypass_from_code, bypass_to_code, '
                    'bypass_score, bypass_reasons, debug_detection, debug_runtime, debug_signal, debug_confidence'
                    ') VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    rows
                )

            fingerprint = self._data.get('fingerprint')
            if isinstance(fingerprint, dict) and len(fingerprint) > 0:
                runtime = fingerprint.get('runtime')
                runtime_name = runtime.get('name') if isinstance(runtime, dict) else None
                runtime_confidence = runtime.get('confidence') if isinstance(runtime, dict) else None

                infrastructure = fingerprint.get('infrastructure')
                infrastructure_provider = None
                infrastructure_confidence = None

                if isinstance(infrastructure, dict) and len(infrastructure) > 0:
                    infrastructure_provider = infrastructure.get('provider')
                    infrastructure_confidence = infrastructure.get('confidence')

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

                cursor.execute(
                    'INSERT INTO fingerprint('
                    'id, category, name, confidence, runtime_name, runtime_confidence, '
                    'infrastructure_provider, infrastructure_confidence, hsts_present, hsts_grade, '
                    'hsts_max_age, hsts_include_subdomains, hsts_preload, hsts_preload_ready, '
                    'hsts_http_to_https_redirect, hsts_warnings, privacy_supercookie_risk, '
                    'privacy_supercookie_score, privacy_supercookie_hsts_tracking_surface, '
                    'privacy_supercookie_etag_tracking_surface, privacy_supercookie_cache_tracking_surface, '
                    'privacy_supercookie_persistent_cookie_surface, privacy_supercookie_warnings, '
                    'privacy_supercookie_signals'
                    ') VALUES(1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (
                        str(fingerprint.get('category', 'custom')),
                        str(fingerprint.get('name', 'Unknown custom stack')),
                        int(fingerprint.get('confidence', 0)),
                        None if runtime_name is None else str(runtime_name),
                        None if runtime_confidence is None else int(runtime_confidence),
                        None if infrastructure_provider is None else str(infrastructure_provider),
                        None if infrastructure_confidence is None else int(infrastructure_confidence),
                        None if hsts.get('present') is None else int(bool(hsts.get('present'))),
                        None if hsts.get('grade') is None else str(hsts.get('grade')),
                        None if hsts.get('max_age') is None else int(hsts.get('max_age')),
                        None if hsts.get('include_subdomains') is None else int(bool(hsts.get('include_subdomains'))),
                        None if hsts.get('preload') is None else int(bool(hsts.get('preload'))),
                        None if hsts.get('preload_ready') is None else int(bool(hsts.get('preload_ready'))),
                        None if hsts.get('http_to_https_redirect') is None else int(bool(hsts.get('http_to_https_redirect'))),
                        ';'.join([str(item) for item in hsts.get('warnings', [])]) if isinstance(hsts.get('warnings'), list) else None,
                        None if supercookie.get('risk') is None else str(supercookie.get('risk')),
                        None if supercookie.get('score') is None else int(supercookie.get('score')),
                        None if supercookie.get('hsts_tracking_surface') is None else int(
                            bool(supercookie.get('hsts_tracking_surface'))
                        ),
                        None if supercookie.get('etag_tracking_surface') is None else int(
                            bool(supercookie.get('etag_tracking_surface'))
                        ),
                        None if supercookie.get('cache_tracking_surface') is None else int(
                            bool(supercookie.get('cache_tracking_surface'))
                        ),
                        None if supercookie.get('persistent_cookie_surface') is None else int(
                            bool(supercookie.get('persistent_cookie_surface'))
                        ),
                        ';'.join([str(item) for item in supercookie.get('warnings', [])])
                        if isinstance(supercookie.get('warnings'), list) else None,
                        ';'.join([str(item) for item in supercookie.get('signals', [])])
                        if isinstance(supercookie.get('signals'), list) else None,
                    )
                )

                signals = fingerprint.get('signals', [])
                if isinstance(signals, list) and len(signals) > 0:
                    cursor.executemany(
                        'INSERT INTO fingerprint_signals(type, value) VALUES(?, ?)',
                        [
                            (
                                str(signal.get('type', 'unknown')),
                                str(signal.get('value', '')),
                            )
                            for signal in signals
                            if isinstance(signal, dict)
                        ]
                    )

                runtime_signals = runtime.get('signals', []) if isinstance(runtime, dict) else []
                if isinstance(runtime_signals, list) and len(runtime_signals) > 0:
                    cursor.executemany('INSERT INTO runtime_signals(type, value) VALUES(?, ?)', [(str(s.get('type', 'unknown')), str(s.get('value', ''))) for s in runtime_signals if isinstance(s, dict)])

            connection.commit()
            tpl.info(key='report', plugin=self.PLUGIN_NAME, dest=filesystem.getabsname(database_path))
        except (sqlite3.Error, FileSystemError, ValueError, TypeError) as error:
            raise Exception(error)
        finally:
            if connection is not None:
                connection.close()
