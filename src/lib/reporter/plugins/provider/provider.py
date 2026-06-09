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
    def __join_detail_list(values):
        """
        Join a report detail list while preserving legacy string conversion.

        :param list values: raw detail values
        :return: compact semicolon-separated value
        """

        return ';'.join([str(value) for value in values])

    @staticmethod
    def __append_detail(details, key, value):
        """
        Append a truthy ``key=value`` detail.

        :param list details: mutable report details
        :param str key: detail key
        :param mixed value: detail value
        :return: None
        """

        if value:
            details.append('{0}={1}'.format(key, value))

    @staticmethod
    def __append_optional_detail(details, key, value, suffix=''):
        """
        Append a ``key=value`` detail when value is not None.

        :param list details: mutable report details
        :param str key: detail key
        :param mixed value: detail value
        :param str suffix: optional value suffix
        :return: None
        """

        if value is not None:
            details.append('{0}={1}{2}'.format(key, value, suffix))

    @classmethod
    def __append_list_detail(cls, details, key, values):
        """
        Append a truthy semicolon-joined list detail.

        :param list details: mutable report details
        :param str key: detail key
        :param list values: raw detail values
        :return: None
        """

        if values:
            details.append('{0}={1}'.format(key, cls.__join_detail_list(values)))

    @staticmethod
    def __append_detail_block(value, details):
        """
        Append a formatted report detail block to a base value.

        :param str value: base report item value
        :param list details: formatted detail entries
        :return: formatted report item value
        """

        return '{0} | {1}'.format(value, ', '.join(details))

    @staticmethod
    def __endpoint_samples(endpoint_detection):
        """
        Return up to three endpoint samples for text report output.

        :param dict endpoint_detection: endpoint detection metadata
        :return: list
        """

        samples = []
        for endpoint in endpoint_detection.get('endpoints', []) or []:
            if not isinstance(endpoint, dict) or not endpoint.get('endpoint'):
                continue

            sample = str(endpoint.get('endpoint'))
            if endpoint.get('method'):
                sample = '{0} {1}'.format(endpoint.get('method'), sample)

            samples.append(sample)
            if len(samples) >= 3:
                break

        return samples

    @classmethod
    def format_report_item(cls, item):
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
            details = ['bypass={0}'.format(item.get('bypass'))]
            cls.__append_detail(details, 'profile', item.get('bypass_profile'))
            cls.__append_detail(details, 'header', item.get('bypass_header'))
            cls.__append_detail(details, 'variant', item.get('bypass_variant'))
            cls.__append_detail(details, 'value', item.get('bypass_value'))

            if item.get('bypass_from_code') is not None and item.get('bypass_to_code') is not None:
                details.append('{0}->{1}'.format(item.get('bypass_from_code'), item.get('bypass_to_code')))

            cls.__append_optional_detail(details, 'score', item.get('bypass_score'))
            cls.__append_list_detail(details, 'reasons', item.get('bypass_reasons'))
            value = cls.__append_detail_block(value, details)

        stacktrace_detection = item.get('stacktrace_detection')
        if isinstance(stacktrace_detection, dict):
            details = ['stacktrace={0}'.format(stacktrace_detection.get('type', 'stacktrace'))]
            cls.__append_detail(details, 'runtime', stacktrace_detection.get('runtime'))
            cls.__append_detail(details, 'signal', stacktrace_detection.get('signal'))
            cls.__append_optional_detail(details, 'confidence', stacktrace_detection.get('confidence'), '%')
            value = cls.__append_detail_block(value, details)

        secret_detection = item.get('secret_detection')
        if isinstance(secret_detection, dict):
            details = ['secret={0}'.format(secret_detection.get('type', 'secret'))]
            cls.__append_detail(details, 'redacted', secret_detection.get('redacted'))
            cls.__append_optional_detail(details, 'confidence', secret_detection.get('confidence'), '%')
            cls.__append_optional_detail(details, 'count', secret_detection.get('count'))
            cls.__append_list_detail(details, 'types', secret_detection.get('types'))
            value = cls.__append_detail_block(value, details)

        malware_detection = item.get('malware_detection')
        if isinstance(malware_detection, dict):
            details = ['malware={0}'.format(malware_detection.get('type', 'malware'))]
            cls.__append_detail(details, 'subtype', malware_detection.get('subtype'))
            cls.__append_detail(details, 'family', malware_detection.get('family'))
            cls.__append_detail(details, 'signal', malware_detection.get('signal'))
            cls.__append_optional_detail(details, 'confidence', malware_detection.get('confidence'), '%')
            cls.__append_optional_detail(details, 'count', malware_detection.get('count'))
            cls.__append_list_detail(details, 'signals', malware_detection.get('signals'))
            value = cls.__append_detail_block(value, details)

        shadow_detection = item.get('shadow_detection')
        if isinstance(shadow_detection, dict):
            details = ['shadow={0}'.format(shadow_detection.get('type', 'backup_copy'))]
            cls.__append_detail(details, 'variant', shadow_detection.get('variant'))
            cls.__append_detail(details, 'base', shadow_detection.get('base_url'))
            cls.__append_optional_detail(details, 'confidence', shadow_detection.get('confidence'), '%')
            cls.__append_optional_detail(details, 'similarity', shadow_detection.get('similarity'))
            value = cls.__append_detail_block(value, details)

        endpoint_detection = item.get('endpoint_detection')
        if isinstance(endpoint_detection, dict):
            details = ['endpoint={0}'.format(endpoint_detection.get('type', 'endpoint'))]
            cls.__append_optional_detail(details, 'confidence', endpoint_detection.get('confidence'), '%')
            cls.__append_optional_detail(details, 'count', endpoint_detection.get('count'))
            cls.__append_list_detail(details, 'types', endpoint_detection.get('types'))
            cls.__append_list_detail(details, 'samples', cls.__endpoint_samples(endpoint_detection))
            value = cls.__append_detail_block(value, details)

        redirect_classification = item.get('redirect_classification')
        if isinstance(redirect_classification, dict):
            details = ['redirect={0}'.format(redirect_classification.get('type', 'unknown'))]
            cls.__append_detail(details, 'reason', redirect_classification.get('reason'))
            cls.__append_detail(details, 'location', redirect_classification.get('location'))
            cls.__append_detail(details, 'target_host', redirect_classification.get('target_host'))
            cls.__append_detail(details, 'confidence', redirect_classification.get('confidence'))
            value = cls.__append_detail_block(value, details)

        openredirect_detection = item.get('openredirect_detection')
        if isinstance(openredirect_detection, dict):
            details = ['openredirect={0}'.format(openredirect_detection.get('type', 'open_redirect'))]
            cls.__append_detail(details, 'param', openredirect_detection.get('parameter'))
            cls.__append_detail(details, 'variant', openredirect_detection.get('variant'))
            cls.__append_detail(details, 'family', openredirect_detection.get('payload_family'))
            cls.__append_detail(details, 'location', openredirect_detection.get('location'))
            cls.__append_optional_detail(details, 'confidence', openredirect_detection.get('confidence'), '%')
            value = cls.__append_detail_block(value, details)

        passive_finding = item.get('passive_finding')
        if isinstance(passive_finding, dict):
            details = ['finding={0}'.format(passive_finding.get('type', 'finding'))]
            cls.__append_detail(details, 'severity', passive_finding.get('severity'))
            cls.__append_detail(details, 'reason', passive_finding.get('reason'))
            cls.__append_detail(details, 'confidence', passive_finding.get('confidence'))
            value = cls.__append_detail_block(value, details)

        return value

    def process(self):
        """
        Process data
        :return: mixed
        """


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
