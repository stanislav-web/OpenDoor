# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from urllib3.response import HTTPResponse

from src.core.http.plugins.response_plugin import ResponsePlugin
from src.core.http.response import Response
from src.core.http.providers.response import ResponseProvider
from src.lib.browser.browser import Browser
from src.lib.browser.sniffers import PassiveFinding, SnifferResult
from src.lib.browser.sniffers.result import (
    bounded_passive_evidence,
    normalize_passive_confidence,
    normalize_passive_severity,
    passive_finding_source,
)


class TestSnifferArchitectureBaseline(unittest.TestCase):
    """Regression safety net for the legacy response-sniffer architecture."""

    @staticmethod
    def make_response(status=200, body=b'', headers=None):
        """Create a response object for sniffer classification tests."""

        return HTTPResponse(status=status, body=body, headers=headers or {})

    @staticmethod
    def make_cfg(**overrides):
        """Create a minimal Response configuration object."""

        base = {
            'is_sniff': True,
            'sniffers': [],
            'SUBDOMAINS_SCAN': 'subdomains',
            'scan': 'directories',
            'is_waf_detect': False,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @staticmethod
    def make_debug(level=0):
        """Create a debug stub accepted by Response."""

        return SimpleNamespace(
            level=level,
            debug_load_sniffer_plugin=MagicMock(),
            debug_response=MagicMock(),
            debug_request_uri=MagicMock(),
            debug_classification=MagicMock(),
        )

    def test_all_public_sniffer_aliases_load_without_cli_renames(self):
        """Every documented --sniff alias should resolve through the legacy plugin loader."""

        aliases = {
            'file': 'file',
            'secret': 'secret',
            'indexof': 'indexof',
            'stacktrace': 'stacktrace',
            'malware': 'malware',
            'endpoint': 'endpoint',
            'skipempty': 'skip',
            'collation': 'failed',
            'shadow': 'shadow',
            'openredirect': 'openredirect',
            'skipsizes=1:2': 'skip',
        }

        for alias, expected_index in aliases.items():
            with self.subTest(alias=alias):
                plugin = ResponsePlugin.load(alias)

                self.assertEqual(plugin.RESPONSE_INDEX, expected_index)
                self.assertTrue(callable(plugin.process))

    def test_response_loads_enabled_sniffers_in_requested_cli_order(self):
        """Response should preserve selected --sniff aliases while loading plugin instances."""

        sniffers = [
            'file',
            'secret',
            'indexof',
            'stacktrace',
            'malware',
            'endpoint',
            'skipempty',
            'collation',
            'shadow',
            'openredirect',
            'skipsizes=1:2',
        ]
        response = Response(self.make_cfg(sniffers=sniffers), self.make_debug(level=1), tpl=MagicMock())

        self.assertEqual(
            [plugin.RESPONSE_INDEX for plugin in response._response_plugins],
            ['file', 'secret', 'indexof', 'stacktrace', 'malware', 'endpoint', 'skip', 'failed', 'shadow', 'openredirect', 'skip'],
        )


    def test_endpoint_sniffer_classifies_explicit_client_api_calls(self):
        """Endpoint sniffer should classify explicit client-side API calls."""

        provider = ResponseProvider(self.make_cfg())
        provider._response_plugins = [ResponsePlugin.load('endpoint')]
        response = self.make_response(
            body=b'fetch("/api/users");',
            headers={'Content-Type': 'application/javascript'},
        )

        self.assertEqual(provider.detect('https://example.com/app.js', response), 'endpoint')
        self.assertEqual(response.opendoor_endpoint_detection['type'], 'ajax')

    def test_active_marker_sniffers_do_not_passively_block_later_detectors(self):
        """Active-only sniffers should return None and let passive sniffers classify the response."""

        provider = ResponseProvider(self.make_cfg())
        provider._response_plugins = [
            ResponsePlugin.load('shadow'),
            ResponsePlugin.load('openredirect'),
            ResponsePlugin.load('secret'),
        ]
        response = self.make_response(
            body=b'window.__cfg = {"aws_key":"AKIAABCDEFGHIJKLMNOP"};',
            headers={'Content-Type': 'text/html'},
        )

        self.assertEqual(provider.detect('https://example.com/config.js', response), 'secret')
        self.assertIsNotNone(getattr(response, 'opendoor_secret_detection', None))

    def test_legacy_passive_sniffer_chain_is_currently_first_match(self):
        """Document current first-match behavior before the multi-finding engine migration."""

        body = b'window.__cfg = {"aws_key":"AKIAABCDEFGHIJKLMNOP"};'
        headers = {'Content-Length': '1000000'}

        file_first = ResponseProvider(self.make_cfg())
        file_first._response_plugins = [ResponsePlugin.load('file'), ResponsePlugin.load('secret')]
        self.assertEqual(
            file_first.detect('https://example.com/download.js', self.make_response(body=body, headers=headers)),
            'file',
        )

        secret_first = ResponseProvider(self.make_cfg())
        secret_first._response_plugins = [ResponsePlugin.load('secret'), ResponsePlugin.load('file')]
        response = self.make_response(body=body, headers=headers)

        self.assertEqual(secret_first.detect('https://example.com/download.js', response), 'secret')
        self.assertIsNotNone(getattr(response, 'opendoor_secret_detection', None))


class TestPassiveFindingContract(unittest.TestCase):
    """Passive finding contract scaffolding tests."""

    def test_passive_finding_normalizes_severity_and_confidence(self):
        """Contract values should use stable normalized vocabulary."""

        self.assertEqual(normalize_passive_severity('warning'), 'medium')
        self.assertEqual(normalize_passive_severity('ERROR'), 'high')
        self.assertEqual(normalize_passive_severity('unknown'), 'info')
        self.assertEqual(normalize_passive_confidence('strong'), 'high')
        self.assertEqual(normalize_passive_confidence('weak'), 'low')
        self.assertEqual(normalize_passive_confidence('unknown'), 'medium')

    def test_passive_finding_bounds_and_redacts_evidence(self):
        """Evidence should be bounded and never expose sensitive values."""

        evidence = bounded_passive_evidence(
            {
                'header': 'content-security-policy',
                'token': 'ghp_secret_value',
                'cookie_name': 'grav-site-123',
                'cookie': 'session=secret',
                'long_value': 'x' * 260,
                'items': list(range(12)),
                'nested': {
                    'password': 'secret-password',
                    'safe': 'value',
                },
                'drop_none': None,
            }
        )

        self.assertEqual(evidence['header'], 'content-security-policy')
        self.assertEqual(evidence['token'], '[redacted]')
        self.assertEqual(evidence['cookie_name'], 'grav-site-123')
        self.assertEqual(evidence['cookie'], '[redacted]')
        self.assertEqual(len(evidence['long_value']), 240)
        self.assertTrue(evidence['long_value'].endswith('...'))
        self.assertEqual(evidence['items'], list(range(10)))
        self.assertEqual(evidence['nested']['password'], '[redacted]')
        self.assertEqual(evidence['nested']['safe'], 'value')
        self.assertNotIn('drop_none', evidence)
        self.assertEqual(bounded_passive_evidence('raw body dump'), {})

    def test_passive_source_and_depth_limits_are_deterministic(self):
        """Source and nested evidence limits should stay deterministic."""

        source = passive_finding_source('response_header', status='blocked')
        evidence = bounded_passive_evidence(
            {
                'level1': {
                    'level2': {
                        'level3': {
                            'value': 'too deep',
                        },
                    },
                },
            },
            max_depth=1,
        )

        self.assertEqual(source, {'signal': 'response_header', 'status': 'blocked'})

        method_only_source = passive_finding_source('response_body', request_method='head')
        self.assertEqual(method_only_source, {'signal': 'response_body', 'request_method': 'HEAD'})
        self.assertEqual(evidence, {'level1': {'level2': {}}})

    def test_passive_finding_builds_stable_dict_without_mutating_inputs(self):
        """PassiveFinding should produce the future report shape without side effects."""

        evidence = {
            'header': 'content-security-policy',
            'directive': 'script-src',
            'value': "'unsafe-inline'",
            'authorization': 'Bearer secret',
        }
        source = passive_finding_source('response_header', request_method='get', status=200)

        finding = PassiveFinding(
            bucket='security_headers',
            finding_type='csp',
            url='https://example.com/admin/',
            severity='warning',
            reason='Unsafe Inline',
            confidence='strong',
            evidence=evidence,
            source=source,
        )

        self.assertEqual(
            finding.to_dict(),
            {
                'bucket': 'security_headers',
                'type': 'csp',
                'url': 'https://example.com/admin/',
                'severity': 'medium',
                'reason': 'unsafe_inline',
                'confidence': 'high',
                'evidence': {
                    'header': 'content-security-policy',
                    'directive': 'script-src',
                    'value': "'unsafe-inline'",
                    'authorization': '[redacted]',
                },
                'source': {
                    'signal': 'response_header',
                    'request_method': 'GET',
                    'status': 200,
                },
            },
        )
        self.assertEqual(evidence['authorization'], 'Bearer secret')
        self.assertEqual(source['request_method'], 'GET')

    def test_passive_contract_does_not_change_existing_sniffer_result_shape(self):
        """SnifferResult should remain backward-compatible while the contract is introduced."""

        result = SnifferResult(
            bucket='secret',
            url='https://example.com/config.js',
            code=200,
            size='1KB',
            metadata={'evidence': 'aws_access_key'},
            suppress_normal=True,
        )

        self.assertEqual(result.dedupe_key(), ('secret', 'https://example.com/config.js', 'aws_access_key'))
        self.assertEqual(result.code, '200')
        self.assertEqual(result.size, '1KB')
        self.assertEqual(result.metadata, {'evidence': 'aws_access_key'})
        self.assertTrue(result.suppress_normal)


class TestStructuredSecurityFindingContract(unittest.TestCase):
    """Contract lock for existing security findings that emit passive_finding metadata."""

    REQUIRED_FIELDS = {
        'bucket',
        'type',
        'url',
        'severity',
        'reason',
        'confidence',
        'evidence',
        'source',
    }
    EXPECTED_FINDINGS = (
        {
            'name': 'secret',
            'builder': Browser._Browser__passive_secret_metadata,
            'url': 'https://secret.local/config.js',
            'code': 200,
            'method': 'get',
            'detection': {
                'type': 'aws_access_key',
                'redacted': 'AKIA****CDEF',
                'confidence': 95,
                'count': 1,
                'types': ['aws_access_key'],
                'matches': [
                    {
                        'type': 'aws_access_key',
                        'redacted': 'AKIA****CDEF',
                        'confidence': 95,
                        'position': 12,
                    }
                ],
            },
            'expected': {
                'bucket': 'secret',
                'type': 'aws_access_key',
                'severity': 'high',
                'reason': 'secret_exposed',
                'confidence': 'high',
                'source_signal': 'response_body',
            },
            'forbidden': ['AKIA1234567890ABCDEF'],
        },
        {
            'name': 'malware',
            'builder': Browser._Browser__passive_malware_metadata,
            'url': 'https://api.example.com/shell.php',
            'code': 200,
            'method': 'GET',
            'detection': {
                'type': 'malware',
                'subtype': 'webshell',
                'family': 'known-webshell-marker',
                'signal': 'known-webshell-name',
                'confidence': 98,
                'count': 1,
                'signals': ['known-webshell-name'],
                'families': ['known-webshell-marker'],
            },
            'expected': {
                'bucket': 'malware',
                'type': 'webshell',
                'severity': 'critical',
                'reason': 'malware_indicator_detected',
                'confidence': 'high',
                'source_signal': 'response_body',
            },
            'forbidden': [],
        },
        {
            'name': 'stacktrace',
            'builder': Browser._Browser__passive_stacktrace_metadata,
            'url': 'https://debug.local/error',
            'code': 500,
            'method': 'GET',
            'detection': {
                'type': 'stacktrace',
                'runtime': 'python',
                'signal': 'python-traceback',
                'confidence': 95,
            },
            'expected': {
                'bucket': 'stacktrace',
                'type': 'stacktrace',
                'severity': 'medium',
                'reason': 'stacktrace_exposed',
                'confidence': 'high',
                'source_signal': 'response_body',
            },
            'forbidden': [],
        },
        {
            'name': 'shadow',
            'builder': Browser._Browser__passive_shadow_metadata,
            'url': 'https://shadow.local/index.php.bak',
            'code': 200,
            'method': 'GET',
            'detection': {
                'type': 'backup_copy',
                'confidence': 90,
                'reason': 'content_diff',
                'base_url': 'https://shadow.local/index.php',
                'url': 'https://shadow.local/index.php.bak',
                'variant': '.bak',
                'variant_type': 'suffix',
                'similarity': 0.96,
                'base_size': 21,
                'shadow_size': 21,
                'content_type': 'text/html',
            },
            'expected': {
                'bucket': 'shadow',
                'type': 'backup_copy',
                'severity': 'high',
                'reason': 'backup_copy_exposed',
                'confidence': 'high',
                'source_signal': 'active_followup_response',
            },
            'forbidden': [],
        },
        {
            'name': 'openredirect',
            'builder': Browser._Browser__passive_openredirect_metadata,
            'url': 'https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F',
            'code': 302,
            'method': 'GET',
            'detection': {
                'type': 'open_redirect',
                'confidence': 100,
                'source_url': 'https://api.example.com/login?next=/home',
                'probe_url': 'https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F',
                'parameter': 'next',
                'payload': 'https://redirect.invalid/',
                'variant': 'absolute-external-url',
                'location': 'https://redirect.invalid/',
                'marker_host': 'redirect.invalid',
            },
            'expected': {
                'bucket': 'openredirect',
                'type': 'open_redirect',
                'severity': 'medium',
                'reason': 'external_redirect_confirmed',
                'confidence': 'high',
                'source_signal': 'redirect_location',
            },
            'forbidden': [],
        },
    )

    def test_existing_security_findings_emit_same_required_contract(self):
        """All migrated security findings should expose the same passive_finding shape."""

        for case in self.EXPECTED_FINDINGS:
            with self.subTest(sniffer=case['name']):
                metadata = case['builder'](
                    case['url'],
                    case['code'],
                    case['method'],
                    case['detection'],
                )
                finding = metadata.get('passive_finding')

                self.assertIsInstance(finding, dict)
                self.assertEqual(set(finding), self.REQUIRED_FIELDS)
                self.assertEqual(finding['bucket'], case['expected']['bucket'])
                self.assertEqual(finding['type'], case['expected']['type'])
                self.assertEqual(finding['url'], case['url'])
                self.assertEqual(finding['severity'], case['expected']['severity'])
                self.assertEqual(finding['reason'], case['expected']['reason'])
                self.assertEqual(finding['confidence'], case['expected']['confidence'])
                self.assertIsInstance(finding['evidence'], dict)
                self.assertIsInstance(finding['source'], dict)
                self.assertEqual(finding['source']['signal'], case['expected']['source_signal'])
                self.assertEqual(finding['source']['request_method'], 'GET')
                self.assertEqual(finding['source']['status'], case['code'])

                serialized = repr(finding)
                for forbidden in case['forbidden']:
                    self.assertNotIn(forbidden, serialized)

    def test_contract_builders_ignore_invalid_detection_inputs(self):
        """Security finding adapters should not emit partial contract objects for invalid inputs."""

        for case in self.EXPECTED_FINDINGS:
            with self.subTest(sniffer=case['name']):
                self.assertEqual(case['builder']('', case['code'], 'GET', case['detection']), {})
                self.assertEqual(case['builder'](case['url'], case['code'], 'GET', None), {})



if __name__ == '__main__':
    unittest.main()
