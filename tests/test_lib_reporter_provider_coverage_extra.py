# -*- coding: utf-8 -*-

import unittest

from src.lib.reporter.plugins.provider.provider import PluginProvider


class TestPluginProviderCoverageExtra(unittest.TestCase):
    """Extra coverage for provider report item formatting branches."""

    def test_get_report_items_falls_back_to_legacy_items_and_returns_copy(self):
        """Legacy URL-only buckets should be normalized to detailed report items."""

        provider = PluginProvider('example.com', {
            'items': {
                'success': ['https://example.com/index.html'],
            },
        })

        items = provider.get_report_items('success')
        self.assertEqual(items, [{
            'url': 'https://example.com/index.html',
            'size': '0B',
            'code': '-',
        }])

        items[0]['url'] = 'changed'
        self.assertEqual(
            provider.get_report_items('success')[0]['url'],
            'https://example.com/index.html',
        )

    def test_format_report_item_accepts_legacy_non_dict_items(self):
        """Legacy plain-string report entries should still format safely."""

        self.assertEqual(
            PluginProvider.format_report_item('https://example.com/plain'),
            'https://example.com/plain',
        )

    def test_format_report_item_renders_all_security_metadata_details(self):
        """Security metadata details should be represented in plain-text report output."""

        rendered = PluginProvider.format_report_item({
            'url': 'https://example.com/admin',
            'code': '200',
            'size': '1KB',
            'waf': 'Cloudflare',
            'waf_confidence': 91,
            'bypass': 'header',
            'bypass_profile': 'safe',
            'bypass_header': 'X-Forwarded-For',
            'bypass_variant': 'loopback',
            'bypass_value': '127.0.0.1',
            'bypass_from_code': '403',
            'bypass_to_code': '200',
            'bypass_score': 88,
            'bypass_reasons': ['status_changed', 'body_changed'],
            'stacktrace_detection': {
                'type': 'python_traceback',
                'runtime': 'python',
                'signal': 'Traceback',
                'confidence': 95,
            },
            'secret_detection': {
                'type': 'aws_access_key',
                'redacted': 'AKIA************',
                'confidence': 90,
                'count': 2,
                'types': ['aws_access_key', 'jwt'],
            },
            'shadow_detection': {
                'type': 'backup_copy',
                'variant': '.bak',
                'base_url': 'https://example.com/admin',
                'confidence': 92,
                'similarity': '0.97',
            },
            'openredirect_detection': {
                'type': 'open_redirect',
                'parameter': 'next',
                'variant': 'absolute_url',
                'location': 'https://opendoor.invalid/',
                'confidence': 99,
            },
        })

        expected_tokens = [
            'WAF: Cloudflare (91%)',
            'bypass=header',
            'profile=safe',
            'header=X-Forwarded-For',
            'variant=loopback',
            'value=127.0.0.1',
            '403->200',
            'score=88',
            'reasons=status_changed;body_changed',
            'stacktrace=python_traceback',
            'runtime=python',
            'signal=Traceback',
            'secret=aws_access_key',
            'redacted=AKIA************',
            'count=2',
            'types=aws_access_key;jwt',
            'shadow=backup_copy',
            'base=https://example.com/admin',
            'similarity=0.97',
            'openredirect=open_redirect',
            'param=next',
            'location=https://opendoor.invalid/',
        ]

        for token in expected_tokens:
            self.assertIn(token, rendered)

    def test_format_report_item_renders_minimal_security_metadata_without_optional_details(self):
        """Minimal security metadata should cover false optional formatting branches."""

        rendered = PluginProvider.format_report_item({
            'url': 'https://example.com/minimal',
            'code': '200',
            'size': '2KB',
            'waf': 'Generic WAF',
            'bypass': 'path',
            'stacktrace_detection': {},
            'secret_detection': {},
            'shadow_detection': {},
            'openredirect_detection': {},
        })

        self.assertIn('WAF: Generic WAF', rendered)
        self.assertIn('bypass=path', rendered)
        self.assertIn('stacktrace=stacktrace', rendered)
        self.assertIn('secret=secret', rendered)
        self.assertIn('shadow=backup_copy', rendered)
        self.assertIn('openredirect=open_redirect', rendered)

        self.assertNotIn('confidence=', rendered)
        self.assertNotIn('runtime=', rendered)
        self.assertNotIn('signal=', rendered)
        self.assertNotIn('redacted=', rendered)
        self.assertNotIn('variant=', rendered)
        self.assertNotIn('location=', rendered)


if __name__ == '__main__':
    unittest.main()
