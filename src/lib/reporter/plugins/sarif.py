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

import json
import os

from .provider import PluginProvider
from src.core import CoreConfig
from src.core import filesystem, FileSystemError
from src.core.core import read_version
from src.lib import tpl


class SarifReportPlugin(PluginProvider):
    """SARIF 2.1.0 report plugin for CI/CD code scanning integrations."""

    PLUGIN_NAME = 'SarifReport'
    EXTENSION_SET = '.sarif'
    SARIF_SCHEMA = 'https://json.schemastore.org/sarif-2.1.0.json'
    SARIF_VERSION = '2.1.0'
    INFORMATION_URI = 'https://github.com/stanislav-web/OpenDoor'
    FAILED_STATUS = 'failed'
    FINGERPRINT_RULE_ID = 'opendoor.fingerprint.detected'
    LEVEL_BY_STATUS = {
        'success': 'warning',
        'file': 'warning',
        'index': 'warning',
        'indexof': 'warning',
        'auth': 'warning',
        'forbidden': 'note',
        'blocked': 'warning',
        'bypass': 'warning',
        'redirect': 'note',
        'bad': 'note',
        'certificate': 'warning',
        'calibrated': 'note',
    }
    SECURITY_SEVERITY_BY_STATUS = {
        'success': '5.0',
        'file': '5.0',
        'index': '5.0',
        'indexof': '5.0',
        'auth': '4.0',
        'forbidden': '2.0',
        'blocked': '3.0',
        'bypass': '6.0',
        'redirect': '1.0',
        'bad': '1.0',
        'certificate': '4.0',
        'calibrated': '0.1',
    }
    RULE_NAMES = {
        'success': 'Exposed HTTP resource',
        'file': 'Exposed file-like resource',
        'index': 'Directory index resource',
        'indexof': 'Directory listing resource',
        'auth': 'Authentication-protected resource',
        'forbidden': 'Forbidden resource',
        'blocked': 'WAF-like response',
        'bypass': 'Access bypass candidate',
        'redirect': 'Redirecting resource',
        'bad': 'Unusual HTTP response',
        'certificate': 'Certificate-related finding',
        'calibrated': 'Auto-calibrated baseline match',
    }

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
    def safe_token(value, fallback='unknown'):
        """
        Normalize arbitrary values into stable SARIF id fragments.

        :param mixed value: source value
        :param str fallback: fallback token
        :return: normalized token
        :rtype: str
        """

        token = str(value or '').strip().lower().replace('-', '_').replace(' ', '_')
        token = ''.join([char for char in token if char.isalnum() or char == '_']).strip('_')
        return token or fallback

    @staticmethod
    def maybe_int(value):
        """
        Convert numeric-looking values to int while preserving unknown values.

        :param mixed value: source value
        :return: int|None
        """

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def clean_properties(properties):
        """
        Remove empty values from a SARIF property bag without losing false-like evidence.

        :param dict properties: source properties
        :return: cleaned properties
        :rtype: dict
        """

        clean = {}
        for key, value in properties.items():
            if value is None or value == '' or value == [] or value == {}:
                continue
            clean[key] = value
        return clean

    @classmethod
    def rule_id(cls, status, item=None):
        """
        Build a stable SARIF rule id for an OpenDoor bucket.

        :param str status: OpenDoor result bucket
        :param dict|None item: report item metadata
        :return: SARIF rule id
        :rtype: str
        """

        if isinstance(item, dict) and item.get('bypass'):
            return 'opendoor.finding.bypass'
        return 'opendoor.finding.{0}'.format(cls.safe_token(status))

    @classmethod
    def rule_for_status(cls, status, item=None):
        """
        Build a SARIF reportingDescriptor for an OpenDoor bucket.

        :param str status: OpenDoor result bucket
        :param dict|None item: optional report item metadata
        :return: SARIF rule descriptor
        :rtype: dict
        """

        rule_id = cls.rule_id(status, item=item)
        normalized_status = 'bypass' if rule_id == 'opendoor.finding.bypass' else cls.safe_token(status)
        name = cls.RULE_NAMES.get(normalized_status, 'OpenDoor finding')

        return {
            'id': rule_id,
            'name': name,
            'shortDescription': {'text': name},
            'fullDescription': {
                'text': 'OpenDoor classified this web resource in the `{0}` result bucket.'.format(
                    cls.safe_token(status)
                ),
            },
            'helpUri': 'https://opendoor.readthedocs.io/',
            'properties': {
                'category': 'external-exposure',
                'precision': 'medium',
                'security-severity': cls.SECURITY_SEVERITY_BY_STATUS.get(normalized_status, '1.0'),
                'tags': ['opendoor', 'web-reconnaissance', normalized_status],
            },
        }

    @classmethod
    def fingerprint_rule(cls):
        """
        Build the SARIF rule descriptor for passive fingerprint findings.

        :return: SARIF rule descriptor
        :rtype: dict
        """

        return {
            'id': cls.FINGERPRINT_RULE_ID,
            'name': 'Technology fingerprint detected',
            'shortDescription': {'text': 'Technology fingerprint detected'},
            'fullDescription': {
                'text': 'OpenDoor detected target technology or infrastructure fingerprint metadata.',
            },
            'helpUri': 'https://opendoor.readthedocs.io/en/latest/detection/fingerprinting/',
            'properties': {
                'category': 'fingerprint',
                'precision': 'medium',
                'security-severity': '0.1',
                'tags': ['opendoor', 'fingerprint', 'reconnaissance'],
            },
        }

    def fingerprint_properties(self):
        """
        Build target-level fingerprint metadata for SARIF properties.

        :return: fingerprint metadata
        :rtype: dict
        """

        fingerprint = self._data.get('fingerprint')
        if not isinstance(fingerprint, dict) or len(fingerprint) == 0:
            return {}

        infrastructure = fingerprint.get('infrastructure')
        if not isinstance(infrastructure, dict):
            infrastructure = {}

        return self.clean_properties({
            'fingerprintCategory': fingerprint.get('category', 'custom'),
            'fingerprintName': fingerprint.get('name', 'Unknown custom stack'),
            'fingerprintConfidence': self.maybe_int(fingerprint.get('confidence')),
            'fingerprintSignals': fingerprint.get('signals', []),
            'infrastructureProvider': infrastructure.get('provider'),
            'infrastructureConfidence': self.maybe_int(infrastructure.get('confidence')),
        })

    def item_properties(self, status, item):
        """
        Build SARIF property metadata for one OpenDoor report item.

        :param str status: OpenDoor result bucket
        :param dict|str item: report item
        :return: SARIF properties
        :rtype: dict
        """

        if not isinstance(item, dict):
            item = {'url': str(item), 'code': '-', 'size': '0B'}

        properties = {
            'target': self._target,
            'bucket': str(status),
            'url': str(item.get('url', '')),
            'statusCode': self.maybe_int(item.get('code')),
            'statusCodeRaw': None if item.get('code') is None else str(item.get('code')),
            'responseSize': str(item.get('size', '0B')),
            'waf': item.get('waf'),
            'wafConfidence': self.maybe_int(item.get('waf_confidence')),
            'wafSignals': item.get('waf_signals', []),
            'bypass': item.get('bypass'),
            'bypassHeader': item.get('bypass_header'),
            'bypassValue': item.get('bypass_value'),
            'bypassVariant': item.get('bypass_variant'),
            'bypassUrl': item.get('bypass_url'),
            'bypassFromCode': self.maybe_int(item.get('bypass_from_code')),
            'bypassToCode': self.maybe_int(item.get('bypass_to_code')),
        }
        properties.update(self.fingerprint_properties())
        return self.clean_properties(properties)

    def message_for_item(self, status, item):
        """
        Build a readable SARIF result message for one item.

        :param str status: OpenDoor result bucket
        :param dict|str item: report item
        :return: SARIF message text
        :rtype: str
        """

        if not isinstance(item, dict):
            item = {'url': str(item)}

        url = str(item.get('url', ''))
        normalized_status = self.safe_token(status)
        if item.get('bypass'):
            return 'OpenDoor detected an access bypass candidate for {0}'.format(url)
        if normalized_status == 'blocked':
            return 'OpenDoor detected a WAF-like response for {0}'.format(url)
        if normalized_status == 'indexof':
            return 'OpenDoor detected a directory listing candidate at {0}'.format(url)
        return 'OpenDoor classified {0} as {1}'.format(url, normalized_status)

    def result_for_item(self, status, item):
        """
        Build a SARIF result object for one report item.

        :param str status: OpenDoor result bucket
        :param dict|str item: report item
        :return: SARIF result
        :rtype: dict
        """

        if not isinstance(item, dict):
            item = {'url': str(item), 'code': '-', 'size': '0B'}

        normalized_status = self.safe_token(status)
        level = self.LEVEL_BY_STATUS.get(normalized_status, 'note')
        if item.get('bypass'):
            level = self.LEVEL_BY_STATUS['bypass']

        return {
            'ruleId': self.rule_id(status, item=item),
            'level': level,
            'message': {'text': self.message_for_item(status, item)},
            'locations': [
                {
                    'physicalLocation': {
                        'artifactLocation': {
                            'uri': str(item.get('url', '')),
                        },
                    },
                }
            ],
            'properties': self.item_properties(status, item),
        }

    def fingerprint_result(self):
        """
        Build an optional SARIF result for target-level fingerprint metadata.

        :return: SARIF result or None
        :rtype: dict|None
        """

        fingerprint = self._data.get('fingerprint')
        if not isinstance(fingerprint, dict) or len(fingerprint) == 0:
            return None

        return {
            'ruleId': self.FINGERPRINT_RULE_ID,
            'level': 'note',
            'message': {
                'text': 'OpenDoor detected target fingerprint: {0}'.format(
                    fingerprint.get('name', 'Unknown custom stack')
                ),
            },
            'locations': [
                {
                    'physicalLocation': {
                        'artifactLocation': {'uri': self._target},
                    },
                }
            ],
            'properties': self.clean_properties({'target': self._target, **self.fingerprint_properties()}),
        }

    def build_sarif_log(self):
        """
        Build a SARIF 2.1.0 log payload from OpenDoor report data.

        :return: SARIF log
        :rtype: dict
        """

        rules = {}
        results = []

        for status in self._data.get('items', {}).keys():
            if status == self.FAILED_STATUS:
                continue
            for item in self.get_report_items(status):
                rule_id = self.rule_id(status, item=item if isinstance(item, dict) else None)
                if rule_id not in rules:
                    rules[rule_id] = self.rule_for_status(status, item=item if isinstance(item, dict) else None)
                results.append(self.result_for_item(status, item))

        fingerprint_result = self.fingerprint_result()
        if fingerprint_result is not None:
            rules[fingerprint_result['ruleId']] = self.fingerprint_rule()
            results.append(fingerprint_result)

        return {
            '$schema': self.SARIF_SCHEMA,
            'version': self.SARIF_VERSION,
            'runs': [
                {
                    'tool': {
                        'driver': {
                            'name': 'OpenDoor',
                            'version': read_version(),
                            'informationUri': self.INFORMATION_URI,
                            'rules': list(rules.values()),
                        },
                    },
                    'results': results,
                    'properties': self.clean_properties({
                        'target': self._target,
                        'reporter': self.PLUGIN_NAME,
                        'total': self._data.get('total', {}),
                    }),
                }
            ],
        }

    def process(self):
        """
        Persist report data into a SARIF 2.1.0 file.

        :return: None
        """

        report_path = os.path.join(self.__target_dir, self._target + self.EXTENSION_SET)

        try:
            filesystem.clear(self.__target_dir, extension=self.EXTENSION_SET)
            report_path = filesystem.makefile(report_path)
            with open(report_path, 'w', encoding='utf-8') as handler:
                json.dump(self.build_sarif_log(), handler, ensure_ascii=False, indent=2)
                handler.write('\n')
            tpl.info(key='report', plugin=self.PLUGIN_NAME, dest=filesystem.getabsname(report_path))
        except (OSError, FileSystemError, TypeError, ValueError) as error:
            raise Exception(error)
