# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib3.response import HTTPResponse

from src.core import helper
from src.core.http.plugins.response import openredirect
from src.core.http.plugins.response.openredirect import OpenredirectResponsePlugin
from src.core.http.response import Response
from src.lib.browser.browser import Browser
from src.lib.browser.debug import Debug
from src.lib.browser.open_redirect import OpenRedirectProbe


class TestOpenRedirectProbe(unittest.TestCase):
    """Active open redirect verification helper tests."""

    @staticmethod
    def make_response(status=302, location='https://redirect.invalid/'):
        """Build a redirect-like HTTP response."""

        return HTTPResponse(status=status, body=b'', headers={'Location': location, 'Content-Length': '0'})

    def test_response_package_exports_openredirect_plugin_alias(self):
        """Should resolve the openredirect sniffer alias without passive classification."""

        response = self.make_response()
        plugin = OpenredirectResponsePlugin(None)

        self.assertIs(openredirect, OpenredirectResponsePlugin)
        self.assertIsNone(plugin.process(response))

    def test_should_enable_only_when_openredirect_sniffer_is_selected(self):
        """Should keep active open redirect verification gated behind --sniff openredirect."""

        self.assertFalse(OpenRedirectProbe.is_enabled(SimpleNamespace(is_sniff=False, sniffers=[])))
        self.assertFalse(OpenRedirectProbe.is_enabled(SimpleNamespace(is_sniff=True, sniffers=['secret'])))
        self.assertTrue(OpenRedirectProbe.is_enabled(SimpleNamespace(is_sniff=True, sniffers=['openredirect'])))

    def test_build_variants_replaces_redirect_like_parameters_only(self):
        """Should build controlled marker variants for existing redirect-like query params."""

        variants = OpenRedirectProbe.build_variants(
            'https://api.example.com/auth/login?returnUrl=/dashboard&safe=1'
        )

        self.assertEqual(len(variants), 2)
        self.assertEqual(variants[0]['param'], 'returnUrl')
        self.assertEqual(variants[0]['payload'], 'https://redirect.invalid/')
        self.assertEqual(variants[0]['payload_family'], 'external_url')
        self.assertEqual(variants[1]['payload_family'], 'protocol_relative_external')
        self.assertIn('returnUrl=https%3A%2F%2Fredirect.invalid%2F', variants[0]['url'])
        self.assertIn('safe=1', variants[0]['url'])
        self.assertIn('returnUrl=%2F%2Fredirect.invalid%2F', variants[1]['url'])


    def test_build_variants_deduplicates_same_probe_url_for_duplicate_marker_values(self):
        """Should avoid duplicate probes when equivalent query mutations produce the same URL."""

        variants = OpenRedirectProbe.build_variants(
            'https://api.example.com/login?next=https://redirect.invalid/&next=https://redirect.invalid/'
        )

        self.assertEqual(len(variants), 3)
        self.assertEqual(
            [variant['variant'] for variant in variants].count('absolute-external-url'),
            1,
        )
        self.assertEqual(
            [variant['variant'] for variant in variants].count('protocol-relative-url'),
            2,
        )

    def test_get_redirect_location_falls_back_to_case_insensitive_headers(self):
        """Should read Location from generic response-like header mappings."""

        response = SimpleNamespace(headers={'location': ' https://redirect.invalid/fallback '})

        self.assertEqual(
            OpenRedirectProbe.get_redirect_location(response),
            'https://redirect.invalid/fallback',
        )

    def test_get_redirect_location_returns_empty_for_non_mapping_headers(self):
        """Should safely ignore response objects without iterable header mappings."""

        response = SimpleNamespace(headers=['Location', 'https://redirect.invalid/'])

        self.assertEqual(OpenRedirectProbe.get_redirect_location(response), '')

    def test_get_redirect_location_prefers_response_redirect_location(self):
        """Should use native urllib3 redirect locations before raw headers."""

        response = SimpleNamespace(
            headers={'Location': 'https://trusted.example.com/'},
            get_redirect_location=MagicMock(return_value=' https://redirect.invalid/native '),
        )

        self.assertEqual(
            OpenRedirectProbe.get_redirect_location(response),
            'https://redirect.invalid/native',
        )

    def test_get_redirect_location_falls_back_when_native_location_is_empty(self):
        """Should inspect headers when get_redirect_location() has no redirect target."""

        response = SimpleNamespace(
            headers={'Location': 'https://redirect.invalid/header'},
            get_redirect_location=MagicMock(return_value=False),
        )

        self.assertEqual(
            OpenRedirectProbe.get_redirect_location(response),
            'https://redirect.invalid/header',
        )

    def test_get_redirect_location_returns_empty_for_mapping_without_location(self):
        """Should return an empty location for ordinary header mappings without Location."""

        response = SimpleNamespace(headers={'Server': 'test', 'Content-Type': 'text/plain'})

        self.assertEqual(OpenRedirectProbe.get_redirect_location(response), '')

    def test_location_host_normalizes_absolute_and_protocol_relative_locations(self):
        """Should normalize Location hosts for legacy helper callers."""

        self.assertEqual(OpenRedirectProbe.location_host(' https://Redirect.Invalid/path '), 'redirect.invalid')
        self.assertEqual(OpenRedirectProbe.location_host('//Redirect.Invalid/path'), 'redirect.invalid')
        self.assertEqual(OpenRedirectProbe.location_host('/relative/path'), '')

    def test_is_confirmed_rejects_invalid_status_values(self):
        """Should avoid confirmations when response status cannot be parsed."""

        response = SimpleNamespace(status='not-a-status', headers={'Location': 'https://redirect.invalid/'})

        self.assertFalse(OpenRedirectProbe.is_confirmed(response))

    def test_build_variants_skips_urls_without_redirect_parameters(self):
        """Should avoid blind probing for ordinary directory paths."""

        self.assertEqual(OpenRedirectProbe.build_variants('https://api.example.com/admin?debug=1'), [])
        self.assertEqual(OpenRedirectProbe.build_variants('https://api.example.com/admin'), [])

    def test_filter_new_variants_deduplicates_probe_urls(self):
        """Should not send duplicate active verification requests in one process."""

        probe = OpenRedirectProbe()
        url = 'https://api.example.com/logout?continue=/login'

        self.assertEqual(len(probe.filter_new_variants(url)), 2)
        self.assertEqual(probe.filter_new_variants(url), [])

    def test_is_confirmed_accepts_absolute_and_protocol_relative_marker_location(self):
        """Should confirm only redirects to the controlled marker host."""

        self.assertTrue(self.OpenRedirectProbe_is_confirmed(status=302, location='https://redirect.invalid/path'))
        self.assertTrue(self.OpenRedirectProbe_is_confirmed(status=302, location='//redirect.invalid/path'))
        self.assertFalse(self.OpenRedirectProbe_is_confirmed(status=200, location='https://redirect.invalid/path'))
        self.assertFalse(self.OpenRedirectProbe_is_confirmed(status=302, location='https://trusted.example.com/'))

    def test_is_confirmed_rejects_relative_same_origin_login_waf_and_body_reflection(self):
        """Should keep marker confirmation strict to controlled external Location targets."""

        source_url = 'https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F'

        self.assertFalse(self.OpenRedirectProbe_is_confirmed(status=302, location='/login?next=https://redirect.invalid/', source_url=source_url))
        self.assertFalse(self.OpenRedirectProbe_is_confirmed(status=302, location='https://api.example.com/login', source_url=source_url))
        self.assertFalse(self.OpenRedirectProbe_is_confirmed(status=302, location='//api.example.com/login', source_url=source_url))
        self.assertFalse(self.OpenRedirectProbe_is_confirmed(status=302, location='/cdn-cgi/challenge-platform/h/b', source_url=source_url))

        reflected = HTTPResponse(
            status=200,
            body=b'https://redirect.invalid/',
            headers={'Content-Type': 'text/html'},
        )
        self.assertFalse(OpenRedirectProbe.is_confirmed(reflected, source_url=source_url))

    def test_is_confirmed_rejects_unsafe_schemes_and_internal_targets(self):
        """Should not treat unsafe schemes or internal hosts as marker confirmations."""

        source_url = 'https://api.example.com/login?next=/home'
        locations = [
            'javascript:alert(1)',
            'data:text/html,https://redirect.invalid/',
            'file:///etc/passwd',
            'http://127.0.0.1/',
            'http://localhost/',
            'http://10.0.0.1/',
            'https://redirect.invalid.evil.example/',
        ]

        for location in locations:
            with self.subTest(location=location):
                self.assertFalse(
                    self.OpenRedirectProbe_is_confirmed(
                        status=302,
                        location=location,
                        source_url=source_url,
                    )
                )

    def test_classify_response_uses_shared_redirect_classifier_metadata(self):
        """Should expose shared redirect classification for probe responses."""

        classification = OpenRedirectProbe.classify_response(
            self.make_response(location='//redirect.invalid/ok'),
            source_url='https://api.example.com/login?next=%2F%2Fredirect.invalid%2F',
        )

        self.assertEqual(classification['type'], 'external')
        self.assertEqual(classification['target_host'], 'redirect.invalid')
        self.assertFalse(classification['same_origin'])

    def OpenRedirectProbe_is_confirmed(self, status, location, source_url=None):
        """Proxy to keep assertion calls compact."""

        return OpenRedirectProbe.is_confirmed(
            self.make_response(status=status, location=location),
            source_url=source_url,
        )

    def test_metadata_contains_verified_evidence(self):
        """Should preserve source URL, payload and Location evidence for reports."""

        variant = {
            'url': 'https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F',
            'param': 'next',
            'payload': 'https://redirect.invalid/',
            'variant': 'absolute-external-url',
            'payload_family': 'external_url',
        }
        metadata = OpenRedirectProbe.metadata(
            'https://api.example.com/login?next=/home',
            variant,
            self.make_response(location='https://redirect.invalid/landing')
        )

        detection = metadata['openredirect_detection']
        self.assertEqual(detection['type'], 'open_redirect')
        self.assertEqual(detection['parameter'], 'next')
        self.assertEqual(detection['confidence'], 100)
        self.assertEqual(detection['payload_family'], 'external_url')
        self.assertEqual(detection['location'], 'https://redirect.invalid/landing')


class TestOpenRedirectRuntime(unittest.TestCase):
    """Browser and runtime rendering tests for openredirect sniffer."""

    @staticmethod
    def make_browser():
        """Build a minimal Browser instance for active open redirect verification."""

        br = Browser.__new__(Browser)
        setattr(br, '_Browser__config', SimpleNamespace(
            is_sniff=True,
            sniffers=['openredirect'],
            is_waf_safe_mode=False,
            is_session_enabled=False,
            accept_cookies=False,
        ))
        setattr(br, '_Browser__client', MagicMock())
        setattr(br, '_Browser__open_redirect_probe', OpenRedirectProbe())
        setattr(br, '_Browser__pool', SimpleNamespace(items_size=1, total_items_size=2, workers_size=1))
        setattr(br, '_Browser__response', SimpleNamespace(
            _get_content_size=MagicMock(return_value='0B'),
            debug_response_data=MagicMock(),
        ))
        setattr(br, '_Browser__result', {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
        })
        setattr(br, '_Browser__progress_output_lock', __import__('threading').RLock())
        return br

    @staticmethod
    def make_response(status=302, location='https://redirect.invalid/'):
        """Build a response object for Browser integration tests."""

        return HTTPResponse(status=status, body=b'', headers={'Location': location, 'Content-Length': '0'})

    def test_browser_probe_persists_confirmed_open_redirect_without_conflicting_with_other_sniffers(self):
        """Should run active verification and persist only confirmed openredirect findings."""

        br = self.make_browser()
        client = getattr(br, '_Browser__client')
        client.request.return_value = self.make_response(location='https://redirect.invalid/ok')

        actual = br._Browser__probe_open_redirect('https://api.example.com/login?returnUrl=/home')

        self.assertTrue(actual)
        self.assertEqual(client.request.call_count, 1)
        result = br.result
        self.assertEqual(result['total']['openredirect'], 1)
        finding = result['report_items']['openredirect'][0]
        self.assertEqual(finding['openredirect_detection']['parameter'], 'returnUrl')
        self.assertEqual(finding['openredirect_detection']['location'], 'https://redirect.invalid/ok')
        self.assertEqual(finding['openredirect_detection']['payload_family'], 'external_url')
        passive = finding['passive_finding']
        self.assertEqual(passive['bucket'], 'openredirect')
        self.assertEqual(passive['type'], 'open_redirect')
        self.assertEqual(passive['severity'], 'medium')
        self.assertEqual(passive['reason'], 'external_redirect_confirmed')
        self.assertEqual(passive['confidence'], 'high')
        self.assertEqual(passive['evidence']['parameter'], 'returnUrl')
        self.assertEqual(passive['evidence']['payload_family'], 'external_url')
        self.assertEqual(passive['evidence']['location'], 'https://redirect.invalid/ok')
        self.assertEqual(passive['source']['signal'], 'redirect_location')
        self.assertEqual(passive['source']['status'], 302)
        getattr(br, '_Browser__response').debug_response_data.assert_called_once()

    def test_inline_active_sniffers_do_not_probe_when_openredirect_is_disabled(self):
        """Should not add active openredirect requests unless --sniff openredirect is enabled."""

        br = self.make_browser()
        setattr(br, '_Browser__config', SimpleNamespace(
            is_sniff=True,
            sniffers=['secret'],
            is_waf_safe_mode=False,
            is_session_enabled=False,
            accept_cookies=False,
        ))
        setattr(br, '_Browser__open_redirect_probe', OpenRedirectProbe())
        setattr(br, '_Browser__request_with_waf_safe_mode', MagicMock())

        emitted = br._Browser__run_inline_active_sniffers(
            'https://api.example.com/login?next=/home',
            ('redirect', 'https://api.example.com/login?next=/home', '0B', '302'),
            self.make_response(location='/login'),
        )

        self.assertEqual(emitted, 0)
        getattr(br, '_Browser__request_with_waf_safe_mode').assert_not_called()

    def test_browser_probe_stops_after_first_confirmed_source_url(self):
        """Should preserve bounded request volume by stopping after first confirmed probe."""

        br = self.make_browser()
        client = getattr(br, '_Browser__client')
        client.request.return_value = self.make_response(location='https://redirect.invalid/ok')

        actual = br._Browser__probe_open_redirect('https://api.example.com/go?next=/a&returnUrl=/b')

        self.assertTrue(actual)
        self.assertEqual(client.request.call_count, 1)
        self.assertEqual(br.result['total']['openredirect'], 1)

    def test_browser_probe_does_not_report_when_redirect_is_not_controlled_marker(self):
        """Should avoid false positives for legitimate allowlisted external redirects."""

        br = self.make_browser()
        client = getattr(br, '_Browser__client')
        client.request.return_value = self.make_response(location='https://trusted.example.com/login')

        actual = br._Browser__probe_open_redirect('https://api.example.com/login?returnUrl=/home')

        self.assertFalse(actual)
        self.assertEqual(client.request.call_count, 2)
        self.assertEqual(br.result['total']['openredirect'], 0)

    def test_passive_openredirect_metadata_handles_edge_values(self):
        """Structured metadata helper should safely normalize partial openredirect evidence."""

        metadata = Browser._Browser__passive_openredirect_metadata(
            url='https://api.example.com/login?next=//redirect.invalid/',
            code='redirect',
            method='POST',
            detection={
                'type': 'open_redirect',
                'confidence': 72,
                'parameter': 'next',
                'variant': 'protocol-relative-url',
                'payload_family': 'protocol_relative_external',
                'location': '//redirect.invalid/',
            },
        )

        finding = metadata['passive_finding']
        self.assertEqual(finding['confidence'], 'medium')
        self.assertEqual(finding['source']['status'], 'redirect')
        self.assertEqual(finding['source']['request_method'], 'POST')
        self.assertEqual(finding['evidence']['payload_family'], 'protocol_relative_external')
        self.assertEqual(finding['evidence']['probe_url'], 'https://api.example.com/login?next=//redirect.invalid/')

    def test_passive_openredirect_metadata_returns_empty_for_invalid_input(self):
        """Structured metadata helper should not create findings without confirmed evidence."""

        self.assertEqual(Browser._Browser__passive_openredirect_metadata('', 302, 'GET', {'confidence': 100}), {})
        self.assertEqual(Browser._Browser__passive_openredirect_metadata('https://x/', 302, 'GET', None), {})

    def test_response_debug_data_passes_openredirect_detection_to_runtime_debug(self):
        """Response.debug_response_data() should route openredirect metadata to Debug."""

        debug = MagicMock()
        response = Response(SimpleNamespace(is_sniff=False), debug)
        redirect_response = self.make_response(location='https://redirect.invalid/next')
        setattr(redirect_response, 'opendoor_openredirect_detection', {'parameter': 'next'})

        response.debug_response_data(
            ('openredirect', 'https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F', '0B', '302'),
            'https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F',
            1,
            1,
            response=redirect_response,
        )

        self.assertEqual(debug.debug_request_uri.call_args.kwargs['openredirect_detection'], {'parameter': 'next'})
        self.assertEqual(debug.debug_classification.call_args.kwargs['openredirect_detection'], {'parameter': 'next'})

    def test_debug_request_uri_renders_openredirect_marker_as_red_finding(self):
        """Runtime progress should render R (OpenRedirect) without conflicting with normal redirects."""

        cfg = SimpleNamespace(DEFAULT_SCAN='directories', scan='directories', debug=1, method='GET')
        debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.info') as info_mock, \
                patch('src.lib.browser.debug.sys.writels'):
            debug.debug_request_uri(
                status='openredirect',
                request_uri='https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F',
                items_size=1,
                total_size=1,
                content_size='0B',
                response_code='302',
                openredirect_detection={'location': 'https://redirect.invalid/'},
            )

        rendered_item = info_mock.call_args.kwargs['item']
        self.assertIn('R', rendered_item)
        self.assertIn('OpenRedirect', rendered_item)
        self.assertIn('redirect.invalid', rendered_item)

    def test_debug_classification_renders_openredirect_detection(self):
        """Debug level 3 should render openredirect verification metadata."""

        cfg = SimpleNamespace(DEFAULT_SCAN='directories', scan='directories', debug=3, method='GET')
        debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            debug.debug_classification(
                status='openredirect',
                code='302',
                size='0B',
                openredirect_detection={
                    'parameter': 'next',
                    'variant': 'absolute-external-url',
                    'location': 'https://redirect.invalid/',
                    'confidence': 100,
                },
            )

        rendered = [call.kwargs.get('msg') for call in debug_mock.call_args_list]
        self.assertTrue(any('OpenRedirect detection:' in str(item) for item in rendered))


if __name__ == '__main__':
    unittest.main()
