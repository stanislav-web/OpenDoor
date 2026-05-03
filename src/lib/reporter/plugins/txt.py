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

    def format_fingerprint_summary(self):
        fingerprint = self._data.get('fingerprint')
        if not isinstance(fingerprint, dict) or len(fingerprint) == 0:
            return []
        rows = [
            'category: {0}'.format(fingerprint.get('category', 'custom')),
            'name: {0}'.format(fingerprint.get('name', 'Unknown custom stack')),
            'confidence: {0}%'.format(fingerprint.get('confidence', 0)),
        ]
        runtime = fingerprint.get('runtime')
        if isinstance(runtime, dict) and len(runtime) > 0:
            rows.extend(['runtime: {0}'.format(runtime.get('name', 'unknown')), 'runtime_confidence: {0}%'.format(runtime.get('confidence', 0))])
        infrastructure = fingerprint.get('infrastructure')
        if isinstance(infrastructure, dict) and len(infrastructure) > 0:
            rows.extend(['infrastructure: {0}'.format(infrastructure.get('provider', 'unknown')), 'infrastructure_confidence: {0}%'.format(infrastructure.get('confidence', 0))])
        return rows

    def process(self):
        """
        Process data
        :return: str
        """
        resultset = self._data.get('items').items()
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
