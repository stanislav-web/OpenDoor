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
                'size TEXT NOT NULL'
                ')'
            )
            cursor.execute(
                'CREATE TABLE fingerprint ('
                'id INTEGER PRIMARY KEY CHECK (id = 1), '
                'category TEXT NOT NULL, '
                'name TEXT NOT NULL, '
                'confidence INTEGER NOT NULL, '
                'infrastructure_provider TEXT, '
                'infrastructure_confidence INTEGER'
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
                    rows.append(
                        (
                            str(status),
                            str(item.get('url', '')),
                            str(item.get('code', '-')),
                            str(item.get('size', '0B')),
                        )
                    )

            if len(rows) > 0:
                cursor.executemany(
                    'INSERT INTO items(status, url, code, size) VALUES(?, ?, ?, ?)',
                    rows
                )

            fingerprint = self._data.get('fingerprint')
            if isinstance(fingerprint, dict) and len(fingerprint) > 0:
                infrastructure = fingerprint.get('infrastructure')
                infrastructure_provider = None
                infrastructure_confidence = None

                if isinstance(infrastructure, dict) and len(infrastructure) > 0:
                    infrastructure_provider = infrastructure.get('provider')
                    infrastructure_confidence = infrastructure.get('confidence')

                cursor.execute(
                    'INSERT INTO fingerprint('
                    'id, category, name, confidence, infrastructure_provider, infrastructure_confidence'
                    ') VALUES(1, ?, ?, ?, ?, ?)',
                    (
                        str(fingerprint.get('category', 'custom')),
                        str(fingerprint.get('name', 'Unknown custom stack')),
                        int(fingerprint.get('confidence', 0)),
                        None if infrastructure_provider is None else str(infrastructure_provider),
                        None if infrastructure_confidence is None else int(infrastructure_confidence),
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

            connection.commit()
            tpl.info(key='report', plugin=self.PLUGIN_NAME, dest=filesystem.getabsname(database_path))
        except (sqlite3.Error, FileSystemError, ValueError, TypeError) as error:
            raise Exception(error)
        finally:
            if connection is not None:
                connection.close()
