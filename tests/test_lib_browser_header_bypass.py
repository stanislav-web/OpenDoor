# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace

from src.lib.browser.header_bypass import HeaderBypassProbe


class TestHeaderBypassProbe(unittest.TestCase):
    """Header injection bypass probe tests."""

    @staticmethod
    def make_config(**kwargs):
        """
        Build lightweight probe config.

        :param dict kwargs: config overrides
        :return: types.SimpleNamespace
        """

        values = {
            'is_header_bypass': True,
            'header_bypass_headers': list(HeaderBypassProbe.DEFAULT_HEADERS),
            'header_bypass_ips': list(HeaderBypassProbe.DEFAULT_IP_VALUES),
            'header_bypass_status': list(HeaderBypassProbe.DEFAULT_STATUS_CODES),
            'header_bypass_limit': 32,
        }
        values.update(kwargs)

        return SimpleNamespace(**values)

    def test_should_probe_only_when_enabled_and_status_matches(self):
        """Probe should run only for configured blocked status codes."""

        enabled_cfg = self.make_config(header_bypass_status=[401, 403])
        disabled_cfg = self.make_config(is_header_bypass=False)
        enabled_probe = HeaderBypassProbe(enabled_cfg)
        disabled_probe = HeaderBypassProbe(disabled_cfg)

        self.assertTrue(enabled_probe.should_probe(('forbidden', 'https://example.com/admin', '10B', '403')))
        self.assertTrue(enabled_probe.should_probe(('auth', 'https://example.com/admin', '10B', '401')))
        self.assertFalse(enabled_probe.should_probe(('ok', 'https://example.com/admin', '90B', '200')))
        self.assertFalse(disabled_probe.should_probe(('forbidden', 'https://example.com/admin', '10B', '403')))

    def test_known_headers_include_user_requested_candidates(self):
        """Known headers should include the stabilized user-provided candidate list."""

        expected_headers = (
            'CF-Connecting-IP',
            'CF-Connecting_IP',
            'Client-IP',
            'Forwarded',
            'Host',
            'Origin',
            'Proxy',
            'Proxy-Host',
            'Proxy-Url',
            'Real-Ip',
            'Referer',
            'Referrer',
            'Request-Uri',
            'True-Client-IP',
            'X-Client-IP',
            'X-Custom-IP-Authorization',
            'X-Forwarded',
            'X-Forwarded-For',
            'X-Forwarded-Host',
            'X-Forwarded-Proto',
            'X-Forwarded-Server',
            'X-Host',
            'X-HTTP-DestinationURL',
            'X-HTTP-Host-Override',
            'X-Original-Remote-Addr',
            'X-Original-URL',
            'X-Originating-IP',
            'X-Proxy-Url',
            'X-Real-IP',
            'X-Referrer',
            'X-Remote-Addr',
            'X-Remote-IP',
            'X-Rewrite-URL',
            'X-WAP-Profile',
            'X-Real-Ip',
            'X-True-IP',
        )

        for header in expected_headers:
            self.assertIn(header, HeaderBypassProbe.KNOWN_HEADERS)

    def test_probe_builds_deterministic_limited_variants(self):
        """Probe should build deterministic variants and respect the configured limit."""

        cfg = self.make_config(
            header_bypass_headers=['X-Original-URL', 'X-Forwarded-For', 'Forwarded'],
            header_bypass_ips=['127.0.0.1', '10.0.0.1'],
            header_bypass_limit=4,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_variants('https://example.com/admin?tab=1')

        self.assertEqual(variants, [
            {'header': 'X-Original-URL', 'value': '/admin?tab=1'},
            {'header': 'X-Original-URL', 'value': '/'},
            {'header': 'X-Forwarded-For', 'value': '127.0.0.1'},
            {'header': 'X-Forwarded-For', 'value': '10.0.0.1'},
        ])

    def test_probe_supports_host_origin_referer_and_url_variants(self):
        """Probe should generate context-aware values for host, origin, referer and URL headers."""

        cfg = self.make_config(
            header_bypass_headers=['X-Forwarded-Host', 'Origin', 'Referer', 'Proxy-Url'],
            header_bypass_ips=['127.0.0.1'],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_variants('https://example.com/admin?tab=1')

        self.assertIn({'header': 'X-Forwarded-Host', 'value': 'example.com'}, variants)
        self.assertIn({'header': 'X-Forwarded-Host', 'value': 'localhost'}, variants)
        self.assertIn({'header': 'Origin', 'value': 'https://example.com'}, variants)
        self.assertIn({'header': 'Referer', 'value': 'https://example.com/admin?tab=1'}, variants)
        self.assertIn({'header': 'Referer', 'value': 'https://example.com'}, variants)
        self.assertIn({'header': 'Proxy-Url', 'value': 'https://example.com/admin?tab=1'}, variants)
        self.assertIn({'header': 'Proxy-Url', 'value': 'https://example.com'}, variants)

    def test_probe_deduplicates_case_insensitive_header_values(self):
        """Probe should avoid duplicated header/value pairs."""

        cfg = self.make_config(
            header_bypass_headers=['X-Real-IP', 'X-Real-IP'],
            header_bypass_ips=['127.0.0.1', '127.0.0.1'],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        self.assertEqual(probe.build_header_variants('https://example.com/admin'), [
            {'header': 'X-Real-IP', 'value': '127.0.0.1'},
        ])

    def test_probe_builds_path_manipulation_variants(self):
        """Probe should build deterministic path-manipulation variants after header probes."""

        cfg = self.make_config(
            header_bypass_headers=[],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_path_variants('https://example.com/admin?tab=1')

        self.assertIn({
            'type': 'path',
            'variant': 'trailing-slash',
            'url': 'https://example.com/admin/?tab=1',
            'value': '/admin/?tab=1',
        }, variants)
        self.assertIn({
            'type': 'path',
            'variant': 'double-leading-slash',
            'url': 'https://example.com//admin?tab=1',
            'value': '//admin?tab=1',
        }, variants)
        self.assertIn({
            'type': 'path',
            'variant': 'dot-segment',
            'url': 'https://example.com/admin/.?tab=1',
            'value': '/admin/.?tab=1',
        }, variants)
        self.assertIn({
            'type': 'path',
            'variant': 'semicolon-suffix',
            'url': 'https://example.com/admin;/?tab=1',
            'value': '/admin;/?tab=1',
        }, variants)
        self.assertIn({
            'type': 'path',
            'variant': 'case-variation',
            'url': 'https://example.com/Admin?tab=1',
            'value': '/Admin?tab=1',
        }, variants)

    def test_probe_builds_403_normalization_prefix_variants(self):
        """Probe should include controlled 403 path-normalization prefix variants."""

        cfg = self.make_config(
            header_bypass_headers=[],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_path_variants('https://example.com/admin?tab=1')

        self.assertIn({
            'type': 'path',
            'variant': 'encoded-dot-prefix',
            'url': 'https://example.com/%2e/admin?tab=1',
            'value': '/%2e/admin?tab=1',
        }, variants)
        self.assertIn({
            'type': 'path',
            'variant': 'semicolon-prefix',
            'url': 'https://example.com/;/admin?tab=1',
            'value': '/;/admin?tab=1',
        }, variants)
        self.assertIn({
            'type': 'path',
            'variant': 'dot-semicolon-prefix',
            'url': 'https://example.com/.;/admin?tab=1',
            'value': '/.;/admin?tab=1',
        }, variants)
        self.assertIn({
            'type': 'path',
            'variant': 'double-slash-semicolon-prefix',
            'url': 'https://example.com//;//admin?tab=1',
            'value': '//;//admin?tab=1',
        }, variants)
        self.assertIn({
            'type': 'path',
            'variant': 'dot-dot-semicolon-suffix',
            'url': 'https://example.com/admin..;/?tab=1',
            'value': '/admin..;/?tab=1',
        }, variants)

    def test_probe_builds_403_normalization_variants_for_arbitrary_service_paths(self):
        """Probe should not depend on admin-specific protected path names."""

        cfg = self.make_config(
            header_bypass_headers=[],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_path_variants('https://api.example.com/payments/internal-auth')

        self.assertIn({
            'type': 'path',
            'variant': 'encoded-dot-prefix',
            'url': 'https://api.example.com/%2e/payments/internal-auth',
            'value': '/%2e/payments/internal-auth',
        }, variants)
        self.assertIn({
            'type': 'path',
            'variant': 'dot-dot-semicolon-suffix',
            'url': 'https://api.example.com/payments/internal-auth..;/',
            'value': '/payments/internal-auth..;/',
        }, variants)

    def test_probe_keeps_header_variants_before_path_variants(self):
        """Combined probes should keep existing header order before path manipulations."""

        cfg = self.make_config(
            header_bypass_headers=['X-Original-URL'],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_variants('https://example.com/admin')

        self.assertEqual(variants[0], {'header': 'X-Original-URL', 'value': '/admin'})
        self.assertEqual(variants[1], {'header': 'X-Original-URL', 'value': '/'})
        self.assertEqual(variants[2]['type'], 'path')
        self.assertEqual(variants[2]['variant'], 'trailing-slash')

    def test_probe_reports_only_promising_transitions(self):
        """Only meaningful status transitions should be treated as bypass candidates."""

        self.assertTrue(HeaderBypassProbe.is_promising(
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            ('success', 'https://example.com/admin', '100B', '200')
        ))
        self.assertTrue(HeaderBypassProbe.is_promising(
            ('auth', 'https://example.com/admin', '10B', '401'),
            ('redirect', 'https://example.com/admin', '0B', '302')
        ))
        self.assertTrue(HeaderBypassProbe.is_promising(
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            ('not_found', 'https://example.com/admin', '40B', '404')
        ))
        self.assertFalse(HeaderBypassProbe.is_promising(
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            ('forbidden', 'https://example.com/admin', '11B', '403')
        ))
        self.assertFalse(HeaderBypassProbe.is_promising(
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            None
        ))

    def test_probe_metadata_contains_report_fields(self):
        """Metadata should contain stable report fields."""

        metadata = HeaderBypassProbe.metadata(
            {'header': 'X-Original-URL', 'value': '/admin'},
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            ('success', 'https://example.com/admin', '100B', '200')
        )

        self.assertEqual(metadata, {
            'bypass': 'header',
            'bypass_profile': 'safe',
            'bypass_from_status': 'forbidden',
            'bypass_to_status': 'success',
            'bypass_from_code': 403,
            'bypass_to_code': 200,
            'bypass_score': 100,
            'bypass_reasons': [
                'status-code-changed',
                'bucket-changed',
                'probe-returned-success-or-redirect',
                'blocked-status-cleared',
            ],
            'bypass_header': 'X-Original-URL',
            'bypass_value': '/admin',
        })

    def test_probe_uses_path_value_for_unknown_custom_header(self):
        """Unknown custom headers should safely fallback to the request path value."""

        cfg = self.make_config(
            header_bypass_headers=['X-Unknown-Bypass-Header'],
            header_bypass_ips=['127.0.0.1'],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        self.assertEqual(probe.build_header_variants('https://example.com/private/admin?debug=1'), [
            {'header': 'X-Unknown-Bypass-Header', 'value': '/private/admin?debug=1'},
        ])

    def test_probe_metadata_supports_path_variant_report_fields(self):
        """Path-bypass metadata should contain stable report fields."""

        metadata = HeaderBypassProbe.metadata(
            {
                'type': 'path',
                'variant': 'trailing-slash',
                'url': 'https://example.com/admin/',
                'value': '/admin/',
            },
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            ('success', 'https://example.com/admin/', '100B', '200')
        )

        self.assertEqual(metadata, {
            'bypass': 'path',
            'bypass_profile': 'safe',
            'bypass_from_status': 'forbidden',
            'bypass_to_status': 'success',
            'bypass_from_code': 403,
            'bypass_to_code': 200,
            'bypass_score': 100,
            'bypass_reasons': [
                'status-code-changed',
                'bucket-changed',
                'probe-returned-success-or-redirect',
                'blocked-status-cleared',
            ],
            'bypass_variant': 'trailing-slash',
            'bypass_value': '/admin/',
            'bypass_url': 'https://example.com/admin/',
        })


    def test_probe_builds_extended_path_variants(self):
        """Path bypass should include controlled normalization and encoding variants."""

        cfg = self.make_config(
            header_bypass_headers=[],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_path_variants('https://example.com/admin?tab=1')
        names = [variant['variant'] for variant in variants]

        self.assertIn('encoded-dot-segment', names)
        self.assertIn('matrix-parameter', names)
        self.assertIn('duplicate-trailing-slash', names)
        self.assertIn('encoded-trailing-slash', names)
        self.assertIn('double-encoded-trailing-slash', names)
        self.assertIn('url-encoded-first-character', names)

    def test_probe_builds_offensive_header_family(self):
        """Offensive profile should add extended proxy, client-IP, method and scheme headers."""

        cfg = self.make_config(
            header_bypass_profile='offensive',
            header_bypass_headers=[
                'X-ProxyUser-IP',
                'Fastly-Client-IP',
                'X-HTTP-Method-Override',
                'X-Forwarded-Scheme',
                'Front-End-Https',
            ],
            header_bypass_ips=['0.0.0.0'],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_header_variants('https://example.com/admin')

        self.assertIn({'header': 'X-ProxyUser-IP', 'value': '0.0.0.0', 'profile': 'offensive'}, variants)
        self.assertIn({'header': 'Fastly-Client-IP', 'value': '0.0.0.0', 'profile': 'offensive'}, variants)
        self.assertIn({'header': 'X-HTTP-Method-Override', 'value': 'GET', 'profile': 'offensive'}, variants)
        self.assertIn({'header': 'X-Forwarded-Scheme', 'value': 'https', 'profile': 'offensive'}, variants)
        self.assertIn({'header': 'Front-End-Https', 'value': 'on', 'profile': 'offensive'}, variants)

    def test_probe_metadata_preserves_offensive_profile(self):
        """Bypass metadata should preserve the variant profile for reporting."""

        metadata = HeaderBypassProbe.metadata(
            {'header': 'X-ProxyUser-IP', 'value': '0.0.0.0', 'profile': 'offensive'},
            ('blocked', 'https://example.com/admin', '10B', '403'),
            ('success', 'https://example.com/admin', '100B', '200')
        )

        self.assertEqual(metadata['bypass_profile'], 'offensive')
        self.assertEqual(metadata['bypass_score'], 100)
        self.assertIn('waf-block-cleared', metadata['bypass_reasons'])

    def test_response_status_handles_malformed_response_data(self):
        """Response status resolver should tolerate malformed response tuples."""

        self.assertEqual(HeaderBypassProbe.response_status(None), '')
        self.assertEqual(HeaderBypassProbe.response_status(()), '')

    def test_probe_builds_encoded_path_variant_for_special_segment(self):
        """Path variants should include encoded last-segment values when useful."""

        cfg = self.make_config(
            header_bypass_headers=[],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_path_variants('https://example.com/admin panel?x=1')

        self.assertIn({
            'type': 'path',
            'variant': 'url-encoded-segment',
            'url': 'https://example.com/admin%20panel?x=1',
            'value': '/admin%20panel?x=1',
        }, variants)

    def test_probe_skips_case_and_encoded_path_variants_without_last_segment(self):
        """Path variant builder should skip case/encoding mutations without a usable segment."""

        cfg = self.make_config(
            header_bypass_headers=[],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        root_variants = probe.build_path_variants('https://example.com/')
        root_names = [variant['variant'] for variant in root_variants]
        self.assertNotIn('case-variation', root_names)
        self.assertNotIn('url-encoded-segment', root_names)

        slash_variants = probe.build_path_variants('https://example.com/admin/')
        slash_names = [variant['variant'] for variant in slash_variants]
        self.assertNotIn('trailing-slash', slash_names)
        self.assertNotIn('case-variation', slash_names)
        self.assertNotIn('url-encoded-segment', slash_names)

    def test_probe_skips_case_variant_when_last_segment_is_already_uppercase(self):
        """Case-variation should not duplicate already-uppercase path segments."""

        cfg = self.make_config(
            header_bypass_headers=[],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_path_variants('https://example.com/ADMIN')
        names = [variant['variant'] for variant in variants]

        self.assertNotIn('case-variation', names)

    def test_probe_skips_double_leading_slash_for_already_double_slash_path(self):
        """Double-leading-slash variant should not duplicate paths that already start with //."""

        cfg = self.make_config(
            header_bypass_headers=[],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_path_variants('https://example.com//admin')
        names = [variant['variant'] for variant in variants]

        self.assertNotIn('double-leading-slash', names)

    def test_probe_rejects_non_blocked_base_non_success_transition(self):
        """Non-success transitions from non-blocked base statuses should not be reported."""

        self.assertFalse(HeaderBypassProbe.is_promising(
            ('server_error', 'https://example.com/admin', '10B', '500'),
            ('not_found', 'https://example.com/admin', '40B', '404')
        ))

    def test_probe_allows_waf_blocked_status_outside_configured_list(self):
        """WAF detection should unlock probes for non-standard blocked status codes."""

        cfg = self.make_config(
            is_waf_safe_mode=True,
            is_waf_detect=True,
            header_bypass_status=[401, 403],
        )
        probe = HeaderBypassProbe(cfg)

        self.assertTrue(probe.should_probe(('blocked', 'https://example.com/admin', '0B', '301')))
        self.assertFalse(probe.should_probe(('redirect', 'https://example.com/admin', '0B', '301')))

    def test_probe_requires_waf_mode_for_blocked_status_override(self):
        """Blocked non-standard statuses should not bypass configured codes without WAF mode."""

        cfg = self.make_config(
            is_waf_safe_mode=False,
            is_waf_detect=False,
            header_bypass_status=[401, 403],
        )
        probe = HeaderBypassProbe(cfg)

        self.assertFalse(probe.should_probe(('blocked', 'https://example.com/admin', '0B', '301')))

    def test_response_code_handles_malformed_response_data(self):
        """Response code resolver should tolerate malformed response tuples."""

        self.assertIsNone(HeaderBypassProbe.response_code(None))
        self.assertIsNone(HeaderBypassProbe.response_code(()))
        self.assertIsNone(HeaderBypassProbe.response_code(('body', 'url', 'size', 'abc')))

    def test_probe_invalid_profile_falls_back_to_safe(self):
        """Invalid profile values should preserve safe default behaviour."""

        cfg = self.make_config(header_bypass_profile='unknown')
        probe = HeaderBypassProbe(cfg)

        self.assertEqual(probe.profile, HeaderBypassProbe.SAFE_PROFILE)

    def test_probe_adds_profile_to_offensive_path_variants(self):
        """Offensive profile should be preserved on path bypass variants."""

        cfg = self.make_config(
            header_bypass_profile='offensive',
            header_bypass_headers=[],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)

        variants = probe.build_path_variants('https://example.com/admin?tab=1')

        self.assertGreater(len(variants), 0)
        self.assertTrue(all(variant.get('profile') == 'offensive' for variant in variants))

    def test_probe_skips_unchanged_path_variant_from_helper(self):
        """Path variant builder should ignore helper output equal to the original path."""

        cfg = self.make_config(
            header_bypass_headers=[],
            header_bypass_ips=[],
            header_bypass_limit=0,
        )
        probe = HeaderBypassProbe(cfg)
        helper_name = '_HeaderBypassProbe__matrix_parameter_variant'
        original_helper = getattr(HeaderBypassProbe, helper_name)

        try:
            setattr(HeaderBypassProbe, helper_name, staticmethod(lambda path: path))
            variants = probe.build_path_variants('https://example.com/admin')
        finally:
            setattr(HeaderBypassProbe, helper_name, staticmethod(original_helper))

        self.assertNotIn('matrix-parameter', [variant['variant'] for variant in variants])

    def test_probe_evidence_handles_unchanged_or_incomplete_response_data(self):
        """Evidence scoring should tolerate unchanged and malformed response data."""

        unchanged_score, unchanged_reasons = HeaderBypassProbe.evidence(
            ('success', 'https://example.com/admin', '10B', 'abc'),
            ('success', 'https://example.com/admin', '10B', 'abc'),
        )
        changed_score, changed_reasons = HeaderBypassProbe.evidence(
            ('forbidden', 'https://example.com/admin', '10B', '403'),
            ('forbidden', 'https://example.com/admin', '11B', '404'),
        )

        self.assertEqual(unchanged_score, 0)
        self.assertEqual(unchanged_reasons, [])
        self.assertEqual(changed_score, 50)
        self.assertEqual(changed_reasons, ['status-code-changed', 'blocked-status-cleared'])


if __name__ == '__main__':
    unittest.main()
