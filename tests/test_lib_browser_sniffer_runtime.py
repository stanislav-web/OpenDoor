# -*- coding: utf-8 -*-

import threading
import unittest
from typing import ClassVar
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core import helper
from src.lib.browser.browser import Browser
from src.lib.browser.sniffers import SnifferResult


class TestBrowserSnifferRuntimeHelpers(unittest.TestCase):
    """Browser-side sniffer finding render/persist helper tests."""

    @staticmethod
    def make_browser():
        """Create a minimal Browser instance with report and debug state."""

        browser = Browser.__new__(Browser)
        browser._Browser__pool = SimpleNamespace(items_size=3, total_items_size=10)
        browser._Browser__response = SimpleNamespace(debug_response_data=MagicMock())
        browser._Browser__result = {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
        }
        browser._Browser__progress_output_lock = threading.RLock()
        browser._Browser__filtered_progress_active = False
        return browser

    def test_emit_sniffer_finding_uses_legacy_debug_renderer_and_metadata_attributes(self):
        """Sniffer rendering should use existing debug_response_data semantics."""

        browser = self.make_browser()
        response = SimpleNamespace()
        finding = SnifferResult(
            bucket='openredirect',
            url='https://api.example.com/login?next=https://opendoor.invalid/',
            code=302,
            size='0B',
            metadata={
                'openredirect_detection': {
                    'type': 'open_redirect',
                    'location': 'https://opendoor.invalid/',
                },
            },
        )

        self.assertTrue(browser._Browser__emit_sniffer_finding(finding, response_object=response))
        self.assertEqual(
            response.opendoor_openredirect_detection,
            {'type': 'open_redirect', 'location': 'https://opendoor.invalid/'},
        )

        debug_response_data = browser._Browser__response.debug_response_data
        debug_response_data.assert_called_once_with(
            ('openredirect', finding.url, '0B', '302'),
            request_url=finding.url,
            items_size=3,
            total_size=10,
            response=response,
        )

    def test_catch_sniffer_finding_persists_legacy_report_item(self):
        """Sniffer persistence should write to the requested bucket and preserve metadata."""

        browser = self.make_browser()
        finding = SnifferResult(
            bucket='shadow',
            url='https://example.com/index.php.bak',
            code=200,
            size='1KB',
            metadata={'shadow_detection': {'type': 'backup_copy', 'confidence': 90}},
        )

        self.assertTrue(browser._Browser__catch_sniffer_finding(finding))

        result = browser._Browser__result
        self.assertEqual(result['total']['shadow'], 1)
        self.assertEqual(result['items']['shadow'], ['https://example.com/index.php.bak'])
        self.assertEqual(result['report_items']['shadow'][0]['code'], '200')
        self.assertEqual(
            result['report_items']['shadow'][0]['shadow_detection'],
            {'type': 'backup_copy', 'confidence': 90},
        )

    def test_sniffer_helpers_ignore_invalid_findings(self):
        """Runtime helpers should be defensive while the engine is being wired in."""

        browser = self.make_browser()

        self.assertFalse(browser._Browser__emit_sniffer_finding(object(), response_object=SimpleNamespace()))
        self.assertFalse(browser._Browser__catch_sniffer_finding(object()))
        browser._Browser__response.debug_response_data.assert_not_called()

    def test_sniffer_response_data_uses_stable_fallbacks(self):
        """Sniffer tuple conversion should keep legacy response_data shape stable."""

        finding = SnifferResult(bucket='secret', url='https://example.com/config.js')

        self.assertEqual(
            Browser._Browser__sniffer_response_data(finding),
            ('secret', 'https://example.com/config.js', '0B', '-'),
        )



class TestBrowserPassiveSnifferMultiFinding(unittest.TestCase):
    """Browser passive additive sniffer collection tests."""

    @staticmethod
    def make_response(status=200, body=b'', headers=None):
        """Create a response object accepted by response plugins."""

        from urllib3.response import HTTPResponse

        return HTTPResponse(status=status, body=body, headers=headers or {})

    @staticmethod
    def make_browser_with_plugins(plugins):
        """Create a minimal Browser instance with loaded response plugins."""

        from src.core.http.plugins.response_plugin import ResponsePlugin

        browser = TestBrowserSnifferRuntimeHelpers.make_browser()
        response = browser._Browser__response
        response._response_plugins = [ResponsePlugin.load(plugin) for plugin in plugins]
        return browser

    def test_collects_secondary_secret_when_file_wins_legacy_first_match(self):
        """Passive additive sniffers should not be hidden by an earlier file finding."""

        browser = self.make_browser_with_plugins(['file', 'secret'])
        response = self.make_response(
            body=b'window.__cfg = {"key":"AKIAABCDEFGHIJKLMNOP"};',
            headers={'Content-Length': '1000000'},
        )
        response_data = ('file', 'https://example.com/download.bin', '977KB', '200')

        findings = browser._Browser__collect_passive_sniffer_findings(response, response_data)

        self.assertEqual([finding.bucket for finding in findings], ['secret'])
        self.assertEqual(findings[0].url, 'https://example.com/download.bin')
        self.assertEqual(findings[0].metadata['secret_detection']['type'], 'aws_access_key')

    def test_collects_secondary_file_when_secret_wins_legacy_first_match(self):
        """Passive additive sniffers should run in engine order, not CLI order."""

        browser = self.make_browser_with_plugins(['secret', 'file'])
        response = self.make_response(
            body=b'window.__cfg = {"key":"AKIAABCDEFGHIJKLMNOP"};',
            headers={'Content-Length': '1000000'},
        )
        response_data = ('secret', 'https://example.com/download.js', '977KB', '200')

        findings = browser._Browser__collect_passive_sniffer_findings(response, response_data)

        self.assertEqual([finding.bucket for finding in findings], ['file'])
        self.assertTrue(findings[0].suppress_normal)
        self.assertEqual(findings[0].evidence_key, 'file')

    def test_emit_passive_sniffer_findings_renders_and_persists_each_bucket(self):
        """Each passive finding should render and persist independently."""

        browser = self.make_browser_with_plugins([])
        response = SimpleNamespace()
        findings = [
            SnifferResult(bucket='file', url='https://example.com/file.bin', code=200, size='1KB'),
            SnifferResult(
                bucket='secret',
                url='https://example.com/file.bin',
                code=200,
                size='1KB',
                metadata={'secret_detection': {'type': 'secret_leak'}},
            ),
        ]

        emitted = browser._Browser__emit_passive_sniffer_findings(findings, response)

        self.assertEqual(emitted, 2)
        result = browser._Browser__result
        self.assertEqual(result['total']['file'], 1)
        self.assertEqual(result['total']['secret'], 1)
        self.assertEqual(result['items']['file'], ['https://example.com/file.bin'])
        self.assertEqual(result['items']['secret'], ['https://example.com/file.bin'])

        debug_response_data = browser._Browser__response.debug_response_data
        self.assertEqual(debug_response_data.call_count, 2)

    def test_collect_passive_sniffer_findings_is_defensive_for_invalid_inputs(self):
        """Passive finding collection should stay defensive during migration."""

        browser = self.make_browser_with_plugins(['file', 'secret'])

        self.assertEqual(browser._Browser__collect_passive_sniffer_findings(None, None), [])
        self.assertEqual(browser._Browser__collect_passive_sniffer_findings(SimpleNamespace(), ('success',)), [])


class TestBrowserSuppressorSnifferRuntime(unittest.TestCase):
    """Browser primary-bucket suppression tests for the sniffer migration."""

    @staticmethod
    def make_browser():
        """Create a minimal Browser instance for suppression helper tests."""

        return TestBrowserSnifferRuntimeHelpers.make_browser()

    def test_suppressor_bucket_suppresses_primary_response_reporting(self):
        """Skip-style suppressor buckets should not render or persist a base item."""

        browser = self.make_browser()
        response = SimpleNamespace(status=200)
        response_data = ('skip', 'https://example.com/empty', '0B', '200')

        self.assertTrue(browser._Browser__should_suppress_primary_response(response, response_data, []))

    def test_soft404_collation_suppresses_failed_bucket_only_for_2xx_responses(self):
        """Collation soft404 failures should suppress base reporting without hiding real 404s."""

        browser = self.make_browser()

        self.assertTrue(browser._Browser__should_suppress_primary_response(
            SimpleNamespace(status=200),
            ('failed', 'https://example.com/missing-soft404', '1KB', '200'),
            [],
        ))
        self.assertFalse(browser._Browser__should_suppress_primary_response(
            SimpleNamespace(status=404),
            ('failed', 'https://example.com/missing', '1KB', '404'),
            [],
        ))

    def test_additive_findings_suppress_only_normal_success_bucket(self):
        """Security findings should suppress normal success noise but not another finding bucket."""

        browser = self.make_browser()
        finding = SnifferResult(
            bucket='secret',
            url='https://example.com/config.js',
            code=200,
            size='1KB',
            suppress_normal=True,
        )

        self.assertTrue(browser._Browser__should_suppress_primary_response(
            SimpleNamespace(status=200),
            ('success', 'https://example.com/config.js', '1KB', '200'),
            [finding],
        ))
        self.assertFalse(browser._Browser__should_suppress_primary_response(
            SimpleNamespace(status=200),
            ('file', 'https://example.com/config.js', '1KB', '200'),
            [finding],
        ))

    def test_primary_suppression_helper_is_defensive_for_invalid_input(self):
        """Invalid response tuples should preserve the legacy primary response path."""

        browser = self.make_browser()

        self.assertFalse(browser._Browser__should_suppress_primary_response(SimpleNamespace(), None, []))
        self.assertFalse(browser._Browser__should_suppress_primary_response(SimpleNamespace(), ('success',), []))


class TestBrowserActiveSnifferRuntime(unittest.TestCase):
    """Browser active-sniffer catalog gate tests."""

    @staticmethod
    def make_browser(sniffers=None, active_names=None):
        """Create a minimal Browser instance with active sniffer state."""

        browser = TestBrowserSnifferRuntimeHelpers.make_browser()
        browser._Browser__config = SimpleNamespace(sniffers=sniffers or [])
        if active_names is not None:
            browser._Browser__active_sniffer_names = set(active_names)
        return browser

    def test_active_sniffer_gate_uses_catalog_names_not_legacy_probe_helpers(self):
        """Browser should gate active sniffers from the engine catalog metadata."""

        browser = self.make_browser(active_names={'shadow', 'openredirect'})

        self.assertTrue(browser._Browser__is_active_sniffer_enabled('shadow'))
        self.assertTrue(browser._Browser__is_active_sniffer_enabled('openredirect'))
        self.assertFalse(browser._Browser__is_active_sniffer_enabled('secret'))

    def test_active_sniffer_gate_builds_names_lazily_from_config(self):
        """Browser should lazily derive enabled active sniffers from Config sniffers."""

        browser = self.make_browser(sniffers=['secret', 'shadow', 'openredirect'])

        self.assertTrue(browser._Browser__is_active_sniffer_enabled('shadow'))
        self.assertTrue(browser._Browser__is_active_sniffer_enabled('openredirect'))
        self.assertFalse(browser._Browser__is_active_sniffer_enabled('secret'))
        self.assertEqual(
            browser._Browser__active_sniffer_names,
            {'shadow', 'openredirect'},
        )


    def test_inline_active_sniffers_run_openredirect_through_common_orchestrator(self):
        """Inline active sniffers should run through the shared active entrypoint."""

        browser = self.make_browser(active_names={'openredirect'})
        browser._Browser__probe_open_redirect = MagicMock(return_value=True)

        emitted = browser._Browser__run_inline_active_sniffers(
            'https://example.com/login?next=/home',
            ('success', 'https://example.com/login?next=/home', '1KB', '200'),
            SimpleNamespace(status=200),
        )

        self.assertEqual(emitted, 1)
        browser._Browser__probe_open_redirect.assert_called_once_with('https://example.com/login?next=/home')

    def test_inline_active_sniffers_skip_disabled_openredirect(self):
        """Disabled inline active sniffers should not call their probe implementation."""

        browser = self.make_browser(active_names={'shadow'})
        browser._Browser__probe_open_redirect = MagicMock(return_value=True)

        emitted = browser._Browser__run_inline_active_sniffers(
            'https://example.com/login?next=/home',
            ('success', 'https://example.com/login?next=/home', '1KB', '200'),
            SimpleNamespace(status=200),
        )

        self.assertEqual(emitted, 0)
        browser._Browser__probe_open_redirect.assert_not_called()

    def test_deferred_active_sniffers_queue_shadow_through_common_orchestrator(self):
        """Deferred active sniffers should submit work through the shared active entrypoint."""

        browser = self.make_browser(active_names={'shadow'})
        browser._Browser__enqueue_shadow_probes = MagicMock(return_value=2)
        response_data = ('success', 'https://example.com/index.php', '1KB', '200')
        response = SimpleNamespace(status=200)

        submitted = browser._Browser__run_deferred_active_sniffers(response_data, response)

        self.assertEqual(submitted, 2)
        browser._Browser__enqueue_shadow_probes.assert_called_once_with(response_data, response)

    def test_deferred_active_sniffers_skip_disabled_shadow(self):
        """Disabled deferred active sniffers should not enqueue any active work."""

        browser = self.make_browser(active_names={'openredirect'})
        browser._Browser__enqueue_shadow_probes = MagicMock(return_value=2)

        submitted = browser._Browser__run_deferred_active_sniffers(
            ('success', 'https://example.com/index.php', '1KB', '200'),
            SimpleNamespace(status=200),
        )

        self.assertEqual(submitted, 0)
        browser._Browser__enqueue_shadow_probes.assert_not_called()


class TestBrowserSnifferCoverageGaps(unittest.TestCase):
    """Coverage tests for defensive browser sniffer branches."""

    @staticmethod
    def make_browser():
        """Create a minimal Browser instance for coverage-gap tests."""

        return TestBrowserSnifferRuntimeHelpers.make_browser()

    def test_soft404_helper_rejects_invalid_primary_bucket_and_invalid_statuses(self):
        """Soft404 suppression should remain defensive for invalid status values."""

        self.assertFalse(Browser._Browser__is_soft404_suppressor_response(
            SimpleNamespace(status=200),
            'success',
            '200',
        ))
        self.assertFalse(Browser._Browser__is_soft404_suppressor_response(
            SimpleNamespace(status='not-int'),
            'failed',
            'also-not-int',
        ))

    def test_primary_suppression_ignores_non_sniffer_results(self):
        """Primary suppression should ignore non-SnifferResult values."""

        browser = self.make_browser()

        self.assertFalse(browser._Browser__should_suppress_primary_response(
            SimpleNamespace(status=200),
            ('success', 'https://example.com/index.html', '1KB', '200'),
            [object()],
        ))

    def test_collect_passive_findings_skips_plugin_errors_and_bucket_mismatches(self):
        """Passive collection should skip failing plugins and non-matching plugin results."""

        class RaisingSecretPlugin:
            """Fake plugin that raises during detection."""

            RESPONSE_INDEX = 'secret'

            def process(self, _response):
                """Raise a synthetic plugin error."""

                raise RuntimeError('synthetic plugin error')

        class MismatchFilePlugin:
            """Fake plugin that returns a different bucket."""

            RESPONSE_INDEX = 'file'

            def process(self, _response):
                """Return a non-matching bucket."""

                return 'secret'

        browser = self.make_browser()
        browser._Browser__response._response_plugins = [
            RaisingSecretPlugin(),
            MismatchFilePlugin(),
        ]

        findings = browser._Browser__collect_passive_sniffer_findings(
            SimpleNamespace(status=200),
            ('success', 'https://example.com/index.html', '1KB', '200'),
        )

        self.assertEqual(findings, [])

    def test_metadata_helper_ignores_non_dict_secret_and_stacktrace_attributes(self):
        """Metadata helper should ignore malformed plugin metadata attributes."""

        response = SimpleNamespace(
            opendoor_secret_detection='not-a-dict',
            opendoor_stacktrace_detection='not-a-dict',
        )

        self.assertEqual(browser_metadata('secret', response), {})
        self.assertEqual(browser_metadata('stacktrace', response), {})

    def test_apply_sniffer_metadata_maps_all_known_metadata_keys(self):
        """Sniffer metadata mapping should attach all known detection metadata fields."""

        browser = self.make_browser()
        response = SimpleNamespace()
        metadata = {
            'stacktrace_detection': {'type': 'trace'},
            'secret_detection': {'type': 'secret'},
            'shadow_detection': {'type': 'shadow'},
            'openredirect_detection': {'type': 'openredirect'},
        }

        self.assertFalse(browser._Browser__apply_sniffer_metadata(None, metadata))
        self.assertFalse(browser._Browser__apply_sniffer_metadata(response, None))
        self.assertTrue(browser._Browser__apply_sniffer_metadata(response, metadata))

        self.assertEqual(response.opendoor_stacktrace_detection, {'type': 'trace'})
        self.assertEqual(response.opendoor_secret_detection, {'type': 'secret'})
        self.assertEqual(response.opendoor_shadow_detection, {'type': 'shadow'})
        self.assertEqual(response.opendoor_openredirect_detection, {'type': 'openredirect'})

    def test_inline_active_sniffers_count_only_positive_openredirect_findings(self):
        """Inline active orchestration should return zero when the probe has no finding."""

        browser = self.make_browser()
        browser._Browser__active_sniffer_names = {'openredirect'}
        browser._Browser__probe_open_redirect = MagicMock(return_value=False)

        emitted = browser._Browser__run_inline_active_sniffers(
            'https://example.com/login?next=/home',
            ('success', 'https://example.com/login?next=/home', '1KB', '200'),
            SimpleNamespace(status=200),
        )

        self.assertEqual(emitted, 0)
        browser._Browser__probe_open_redirect.assert_called_once_with(
            'https://example.com/login?next=/home',
        )


def browser_metadata(bucket, response):
    """Proxy private metadata helper for concise assertions."""

    return Browser._Browser__metadata_for_sniffer_bucket(bucket, response)


class TestBrowserRemainingCoverageGaps(unittest.TestCase):
    """Remaining browser.py coverage gaps around sniffer architecture helpers."""

    @staticmethod
    def make_browser():
        """Create a minimal Browser instance for remaining coverage tests."""

        return TestBrowserSnifferRuntimeHelpers.make_browser()

    def test_fingerprint_progress_done_clears_active_line(self):
        """Done state should clear active fingerprint progress before persistent output."""

        import contextlib
        import io

        browser = self.make_browser()
        browser._Browser__fingerprint_progress_active = True
        browser._Browser__fingerprint_progress_last_length = 12

        with (
            contextlib.redirect_stdout(io.StringIO()) as stream,
            patch('src.lib.browser.browser.tpl.info') as info,
        ):
            browser._Browser__fingerprint_progress(1, 1, 'done')

        self.assertIn('\r', stream.getvalue())
        self.assertFalse(browser._Browser__fingerprint_progress_active)
        self.assertEqual(browser._Browser__fingerprint_progress_last_length, 0)
        info.assert_called_once()

    def test_privacy_risk_warnings_cover_defensive_returns_and_warning(self):
        """Privacy warning helper should ignore malformed data and print valid warnings."""

        with patch('src.lib.browser.browser.tpl.warning') as warning:
            Browser._Browser__print_privacy_risk_warnings(None)
            Browser._Browser__print_privacy_risk_warnings({'privacy_risks': None})
            Browser._Browser__print_privacy_risk_warnings({'privacy_risks': {'supercookie': None}})
            Browser._Browser__print_privacy_risk_warnings({
                'privacy_risks': {
                    'supercookie': {
                        'risk': 'high',
                        'warnings': None,
                    },
                },
            })
            Browser._Browser__print_privacy_risk_warnings({
                'privacy_risks': {
                    'supercookie': {
                        'risk': 'high',
                        'warnings': ['ETag tracking'],
                    },
                },
            })

        warning.assert_called_once_with(
            msg='Possible supercookie tracking surface: ETag tracking',
        )

    def test_fingerprint_proxy_error_uses_default_result_in_non_standalone_proxy_mode(self):
        """Proxy fingerprint errors should be graceful outside standalone proxy mode."""

        from src.core import ProxyRequestError

        class FakeFingerprint:
            """Fingerprint replacement that raises a proxy error."""

            DEFAULT_RESULT: ClassVar[dict[str, object]] = {
                'category': 'custom',
                'name': 'Unknown custom stack',
                'confidence': 0,
            }

            def __init__(self, *_args, **_kwargs):
                """Accept the production constructor shape."""

            def detect(self):
                """Raise synthetic proxy error."""

                raise ProxyRequestError('proxy unavailable')

        browser = self.make_browser()
        browser._Browser__config = SimpleNamespace(
            is_fingerprint=True,
            host='example.com',
            is_standalone_proxy=False,
        )
        browser._Browser__client = SimpleNamespace()

        with (
            patch('src.lib.browser.browser.Fingerprint', FakeFingerprint),
            patch('src.lib.browser.browser.tpl.warning') as warning,
        ):
            result = browser.fingerprint()

        self.assertEqual(result['category'], 'custom')
        self.assertEqual(browser._Browser__result['fingerprint'], result)
        warning.assert_called_once()

    def test_resolve_dns_addresses_skips_malformed_records(self):
        """DNS resolver should skip malformed records and normalize valid addresses."""

        browser = self.make_browser()
        records = [
            (),
            (None, None, None, None, (None,)),
            (None, None, None, None, ('127.0.0.1',)),
        ]

        with patch('src.lib.browser.browser.net_socket.getaddrinfo', return_value=records):
            self.assertEqual(browser._Browser__resolve_dns_addresses('example.com'), ['127.0.0.1'])

    def test_shared_cookie_sync_stores_non_empty_cookie_header(self):
        """Accepted cookies should be captured from the active request provider."""

        browser = self.make_browser()
        browser._Browser__config = SimpleNamespace(accept_cookies=True)
        browser._Browser__client = SimpleNamespace(_push_cookies=MagicMock(return_value='SID=abc'))

        browser._Browser__sync_shared_cookies_from_client()

        self.assertEqual(browser._Browser__shared_cookie_header, 'SID=abc')

    def test_header_lookup_falls_back_to_case_insensitive_items(self):
        """Header lookup should work for mapping-like objects without get()."""

        class ItemsOnlyHeaders:
            """Headers object exposing items only."""

            def get(self, _key):
                """Simulate an object without usable get()."""

                raise AttributeError('no get')

            def items(self):
                """Return mixed-case header items."""

                return [('Retry-After', '5')]

        response = SimpleNamespace(headers=ItemsOnlyHeaders())

        self.assertEqual(
            Browser._Browser__get_header_value(response, 'retry-after'),
            '5',
        )

    def test_dns_wildcard_match_returns_none_without_active_baseline(self):
        """DNS wildcard matcher should return None when calibration baseline is unavailable."""

        browser = self.make_browser()
        browser._Browser__config = SimpleNamespace(
            is_auto_calibrate=True,
            scan='subdomains',
            SUBDOMAINS_SCAN='subdomains',
            host='example.com',
        )
        browser._Browser__calibration = None

        self.assertIsNone(
            browser._Browser__match_dns_wildcard_response('http://api.example.com'),
        )

    def test_openredirect_probe_handles_missing_probe_and_empty_probe_response(self):
        """OpenRedirect probing should stay defensive for absent probes and empty responses."""

        browser = self.make_browser()
        browser._Browser__open_redirect_probe = None

        self.assertFalse(browser._Browser__probe_open_redirect('https://example.com/login?next=/'))

        browser._Browser__open_redirect_probe = SimpleNamespace(
            filter_new_variants=MagicMock(return_value=[{
                'url': 'https://example.com/login?next=https://opendoor.invalid/',
            }]),
        )
        browser._Browser__request_with_waf_safe_mode = MagicMock(return_value=None)

        self.assertFalse(browser._Browser__probe_open_redirect('https://example.com/login?next=/'))
        browser._Browser__request_with_waf_safe_mode.assert_called_once()

    def test_emit_filtered_progress_formats_numeric_score(self):
        """Filtered progress should format numeric calibration scores."""

        import contextlib
        import io

        browser = self.make_browser()

        with contextlib.redirect_stdout(io.StringIO()) as stream:
            emitted = browser._Browser__emit_filtered_progress(
                'calibrated',
                ('success', 'https://example.com/admin', '1KB', '200'),
                {'calibration_score': 0.987},
                request_url='https://example.com/admin',
            )

        self.assertTrue(emitted)
        self.assertIn('score=0.99', stream.getvalue())

    def test_stacktrace_metadata_and_emit_false_branch(self):
        """Stacktrace metadata should be mapped and non-callable debug renderers should be safe."""

        response = SimpleNamespace(opendoor_stacktrace_detection={'type': 'trace'})
        self.assertEqual(
            Browser._Browser__metadata_for_sniffer_bucket('stacktrace', response),
            {'stacktrace_detection': {'type': 'trace'}},
        )

        browser = self.make_browser()
        browser._Browser__response.debug_response_data = None
        emitted = browser._Browser__emit_passive_sniffer_findings([
            SnifferResult(bucket='stacktrace', url='https://example.com/debug', code=200, size='1KB'),
        ], response)

        self.assertEqual(emitted, 0)
        self.assertEqual(browser._Browser__result['total']['stacktrace'], 1)

    def test_shrink_planned_total_ignores_invalid_pool_numbers(self):
        """Subdomain total shrink should ignore invalid pool counters."""

        browser = self.make_browser()
        browser._Browser__pool = SimpleNamespace(submitted_size='bad', total_items_size=10)

        browser._Browser__shrink_planned_total_for_deduplicated_url()

        self.assertEqual(browser._Browser__pool.total_items_size, 10)

    def test_warn_filtered_progress_mode_emits_when_sniffing_is_enabled(self):
        """Filtered-progress warning should emit for sniffer-enabled scans."""

        browser = self.make_browser()
        browser._Browser__config = SimpleNamespace(
            is_response_filtering=False,
            is_auto_calibrate=False,
            is_sniff=True,
        )

        with patch('src.lib.browser.browser.tpl.warning') as warning:
            browser._Browser__warn_filtered_progress_mode()

        warning.assert_called_once_with(key='filtered_progress_notice')


if __name__ == '__main__':
    unittest.main()
