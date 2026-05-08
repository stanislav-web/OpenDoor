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

import copy

from src.core import filesystem, FileSystemError
from src.lib import tpl


class PluginProvider(object):
    """"PluginProvider class"""

    PLUGIN_NAME = 'PluginProvider'
    EXTENSION_SET = '.pp'

    def __init__(self, target, data):
        """
        PluginProvider constructor
        :param str target: target host
        :param dict data: result set
        """

        self._target = str(target)
        self._data = {}
        self.__set_data(data)

    def __set_data(self, data):
        """
        Set report data
        :param dict data:
        :return:
        """

        if False is isinstance(data, dict):
            raise TypeError("Report data has a wrong type")
        self._data = data

    def get_report_items(self, status):
        """
        Return detailed report items for the requested status.
        Falls back to legacy URL-only buckets when detailed metadata is absent.
        :param str status: bucket status
        :return: list
        """

        report_items = self._data.get('report_items', {})
        items = report_items.get(status)
        if items is None:
            items = [
                {'url': url, 'size': '0B', 'code': '-'}
                for url in self._data.get('items', {}).get(status, [])
            ]
        return copy.deepcopy(items)

    @staticmethod
    def format_report_item(item):
        """
        Format one report item for plain text reports.

        :param dict | str item: report item
        :return: str
        """

        if not isinstance(item, dict):
            return str(item)

        value = '{0} - {1} - {2}'.format(
            item.get('url', ''),
            item.get('code', '-'),
            item.get('size', '0B')
        )

        if item.get('waf'):
            waf_value = 'WAF: {0}'.format(item.get('waf'))

            if item.get('waf_confidence') is not None:
                waf_value = '{0} ({1}%)'.format(waf_value, item.get('waf_confidence'))

            value = '{0} - {1}'.format(value, waf_value)

        if item.get('bypass'):
            details = [
                'bypass={0}'.format(item.get('bypass')),
            ]

            if item.get('bypass_header'):
                details.append('header={0}'.format(item.get('bypass_header')))

            if item.get('bypass_value'):
                details.append('value={0}'.format(item.get('bypass_value')))

            if item.get('bypass_from_code') is not None and item.get('bypass_to_code') is not None:
                details.append('{0}->{1}'.format(
                    item.get('bypass_from_code'),
                    item.get('bypass_to_code')
                ))

            value = '{0} | {1}'.format(value, ', '.join(details))

        debug_detection = item.get('debug_detection')
        if isinstance(debug_detection, dict):
            details = ['debug={0}'.format(debug_detection.get('type', 'debug'))]

            if debug_detection.get('runtime'):
                details.append('runtime={0}'.format(debug_detection.get('runtime')))

            if debug_detection.get('signal'):
                details.append('signal={0}'.format(debug_detection.get('signal')))

            if debug_detection.get('confidence') is not None:
                details.append('confidence={0}%'.format(debug_detection.get('confidence')))

            value = '{0} | {1}'.format(value, ', '.join(details))

        return value

    def process(self):
        """
        Process data
        :return: mixed
        """

        pass

    @classmethod
    def record(cls, dirname, filename, resultset, separator=''):
        """
        Record data process
        :param str dirname: report directory
        :param str filename: report filename
        :param list resultset: report result
        :param str separator: result separator
        :raise Exception
        :return: None
        """

        try:
            filename = "".join((dirname, filesystem.sep, filename, cls.EXTENSION_SET))
            filename = filesystem.makefile(filename)
            filesystem.writelist(filename, resultset, separator)
            tpl.info(key='report', plugin=cls.PLUGIN_NAME, dest=filesystem.getabsname(filename))
        except FileSystemError as error:
            raise Exception(error)