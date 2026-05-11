# -*- coding: utf-8 -*-

import io
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

    def OpenRedirectProbe_is_confirmed(self, status, location):
        """Proxy to keep assertion calls compact."""

        return OpenRedirectProbe.is_confirmed(self.make_response(status=status, location=location))

    def test_metadata_contains_verified_evidence(self):
        """Should preserve source URL, payload and Location evidence for reports."""

        variant = {
            'url': 'https://api.example.com/login?next=https%3A%2F%2Fredirect.invalid%2F',
            'param': 'next',
            'payload': 'https://redirect.invalid/',
            'variant': 'absolute-external-url',
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
        getattr(br, '_Browser__response').debug_response_data.assert_called_once()

    def test_browser_probe_does_not_report_when_redirect_is_not_controlled_marker(self):
        """Should avoid false positives for legitimate allowlisted external redirects."""

        br = self.make_browser()
        client = getattr(br, '_Browser__client')
        client.request.return_value = self.make_response(location='https://trusted.example.com/login')

        actual = br._Browser__probe_open_redirect('https://api.example.com/login?returnUrl=/home')

        self.assertFalse(actual)
        self.assertEqual(client.request.call_count, 2)
        self.assertEqual(br.result['total']['openredirect'], 0)

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
