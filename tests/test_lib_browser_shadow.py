# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib3.response import HTTPResponse

from src.core import CoreConfig, helper
from src.core.http.plugins.response import shadow
from src.core.http.plugins.response.shadow import ShadowResponsePlugin
from src.core.http.response import Response
from src.lib.browser.browser import Browser
from src.lib.browser.config import Config
from src.lib.browser.shadow import ShadowProbe
from src.lib.browser.debug import Debug


class TestShadowProbe(unittest.TestCase):
    """Active shadow-copy probe tests."""

    def make_response(self, body=b'hello', status=200, content_type='text/html'):
        """
        Build a response object for shadow tests.

        :param bytes body: response body
        :param int status: HTTP status
        :param str content_type: Content-Type header value
        :return: HTTP response
        """

        return HTTPResponse(
            status=status,
            body=body,
            headers={'Content-Type': content_type, 'Content-Length': str(len(body))},
        )

    def test_response_package_exports_shadow_plugin_alias(self):
        """Should resolve the shadow sniffer alias without passive classification."""

        response = self.make_response()
        plugin = ShadowResponsePlugin(None)

        self.assertIs(shadow, ShadowResponsePlugin)
        self.assertIsNone(plugin.process(response))

    def test_load_suffixes_keeps_clean_deduplicated_order(self):
        """Should load a clean suffix dictionary and ignore duplicates/empty lines."""

        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as handler:
            handler.write('.bak\n.old\n.bak\n\n~\n')
            path = handler.name

        try:
            with patch.dict(CoreConfig.get('data'), {'shadow_suffixes': path}):
                self.assertEqual(ShadowProbe.load_suffixes(), ['.bak', '.old', '~'])
        finally:
            os.unlink(path)

    def test_should_enable_only_when_shadow_sniffer_is_selected(self):
        """Should keep shadow runtime fully gated behind --sniff shadow."""

        self.assertFalse(ShadowProbe.is_enabled(SimpleNamespace(is_sniff=False, sniffers=[])))
        self.assertFalse(ShadowProbe.is_enabled(SimpleNamespace(is_sniff=True, sniffers=['secret'])))
        self.assertTrue(ShadowProbe.is_enabled(SimpleNamespace(is_sniff=True, sniffers=['shadow'])))

    def test_should_identify_file_like_seed_urls(self):
        """Should probe source/config-like files and skip directories/binary assets."""

        self.assertTrue(ShadowProbe.is_file_like_url('https://example.com/index.php'))
        self.assertTrue(ShadowProbe.is_file_like_url('https://example.com/app.py'))
        self.assertTrue(ShadowProbe.is_file_like_url('https://example.com/package.json'))
        self.assertTrue(ShadowProbe.is_file_like_url('https://example.com/.env'))
        self.assertFalse(ShadowProbe.is_file_like_url('https://example.com/admin/'))
        self.assertFalse(ShadowProbe.is_file_like_url('https://example.com/api/users'))
        self.assertFalse(ShadowProbe.is_file_like_url('https://example.com/logo.png'))

    def test_should_generate_postfix_candidates_with_limit(self):
        """Should generate bounded postfix candidates from one file-like hit."""

        suffixes = ['.s{0}'.format(index) for index in range(20)]
        candidates = ShadowProbe.build_candidates('https://example.com/index.php?x=1', suffixes)

        self.assertEqual(len(candidates), ShadowProbe.MAX_CANDIDATES_PER_HIT)
        self.assertEqual(candidates[0], ('https://example.com/index.php.s0?x=1', '.s0'))
        self.assertEqual(candidates[-1], ('https://example.com/index.php.s11?x=1', '.s11'))

    def test_should_classify_exact_content_match_as_shadow(self):
        """Should request generated candidates and report exact content matches only."""

        base = self.make_response(body=b'<?php echo "stable"; ?>')
        matches = []
        progress = []

        def request(url):
            if url.endswith('.bak'):
                return self.make_response(body=b'<?php echo "stable"; ?>')
            return self.make_response(body=b'not the same')

        probe = ShadowProbe(request, lambda url, response, metadata: matches.append((url, metadata)), lambda *args: progress.append(args))
        with patch.object(probe, '_ShadowProbe__suffixes', ['.bak', '.old']):
            self.assertEqual(probe.enqueue('https://example.com/index.php', base, 'success'), 2)
            probe.drain()

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], 'https://example.com/index.php.bak')
        detection = matches[0][1]['shadow_detection']
        self.assertEqual(detection['type'], 'backup_copy')
        self.assertEqual(detection['base_url'], 'https://example.com/index.php')
        self.assertEqual(detection['variant'], '.bak')
        self.assertEqual(detection['confidence'], 95)
        self.assertEqual(len(progress), 1)

    def test_should_skip_non_success_non_file_like_binary_and_shadow_buckets(self):
        """Should keep active probing limited to success 200 file-like responses."""

        request = MagicMock(return_value=self.make_response())
        match = MagicMock()
        probe = ShadowProbe(request, match)

        self.assertEqual(probe.enqueue('https://example.com/index.php', self.make_response(status=403), 'success'), 0)
        self.assertEqual(probe.enqueue('https://example.com/admin/', self.make_response(), 'success'), 0)
        self.assertEqual(probe.enqueue('https://example.com/logo.png', self.make_response(), 'success'), 0)
        self.assertEqual(probe.enqueue('https://example.com/index.php', self.make_response(), 'shadow'), 0)
        self.assertEqual(probe.enqueue('https://example.com/archive.zip', self.make_response(content_type='application/zip'), 'success'), 0)
        self.assertEqual(request.call_count, 0)
        self.assertEqual(match.call_count, 0)

    def test_should_deduplicate_shadow_candidates_globally(self):
        """Should never submit the same generated shadow URL twice."""

        request = MagicMock(return_value=self.make_response(body=b'different'))
        probe = ShadowProbe(request, MagicMock())
        base = self.make_response(body=b'base')

        with patch.object(probe, '_ShadowProbe__suffixes', ['.bak']):
            self.assertEqual(probe.enqueue('https://example.com/index.php', base, 'success'), 1)
            self.assertEqual(probe.enqueue('https://example.com/index.php', base, 'success'), 0)
            probe.drain()

        self.assertEqual(request.call_count, 1)

    def test_should_cover_shadow_helper_edge_paths(self):
        """Should cover shadow helper edge paths and defensive fallbacks."""

        with patch.dict(CoreConfig.get('data'), {'shadow_suffixes': None}):
            self.assertEqual(ShadowProbe.load_suffixes(), [])

        self.assertFalse(ShadowProbe.is_file_like_url('http://[::1'))
        self.assertFalse(ShadowProbe.is_file_like_url('https://example.com/.'))
        self.assertEqual(ShadowProbe.build_candidates('http://[::1', ['.bak']), [])
        self.assertEqual(ShadowProbe.build_candidates('https://example.com/admin/', ['.bak']), [])

        none_body = SimpleNamespace(status=200, data=None, headers={})
        string_body = SimpleNamespace(status=200, data='  stable text  ', headers={'content-type': 'text/plain; charset=utf-8'})
        empty_body = SimpleNamespace(status=200, data=b'   ', headers={})
        bad_status = SimpleNamespace(status='bad', data=b'stable', headers={})
        binary = SimpleNamespace(status=200, data=b'stable', headers={'Content-Type': 'image/png'})

        self.assertIsNone(ShadowProbe.response_signature(none_body))
        self.assertEqual(ShadowProbe.response_signature(string_body)['size'], len('  stable text  '))
        self.assertIsNone(ShadowProbe.response_signature(empty_body))
        self.assertFalse(ShadowProbe.is_supported_response(bad_status))
        self.assertFalse(ShadowProbe.is_supported_response(binary))
        self.assertIsNone(ShadowProbe.is_match(None, string_body))
        self.assertIsNone(ShadowProbe.is_match({'hash': 'missing'}, none_body))

    def test_should_cover_shadow_content_type_fallbacks(self):
        """Should normalize content-type from mapping-like and invalid headers."""

        class HeaderPairs(object):
            def __iter__(self):
                return iter([('content-type', 'Application/JSON; charset=utf-8')])

        pair_response = SimpleNamespace(headers=HeaderPairs())
        invalid_response = SimpleNamespace(headers=object())

        self.assertEqual(ShadowProbe.content_type(pair_response), 'application/json')
        self.assertEqual(ShadowProbe.content_type(invalid_response), '')

    def test_should_stop_enqueueing_after_total_probe_limit(self):
        """Should stop queueing candidates when the global probe limit is reached."""

        request = MagicMock(return_value=self.make_response(body=b'different'))
        probe = ShadowProbe(request, MagicMock())
        base = self.make_response(body=b'base')

        with patch.object(probe, '_ShadowProbe__suffixes', ['.bak']), \
                patch.object(ShadowProbe, 'MAX_TOTAL_PROBES', 0):
            self.assertEqual(probe.enqueue('https://example.com/index.php', base, 'success'), 0)

    def test_should_count_completed_and_findings_and_ignore_request_errors(self):
        """Should keep worker counters stable for matches and request failures."""

        responses = {
            'https://example.com/index.php.bak': self.make_response(body=b'base'),
        }

        def request(url):
            if url.endswith('.old'):
                raise RuntimeError('network failed')
            return responses[url]

        matches = []
        probe = ShadowProbe(request, lambda url, response, metadata: matches.append(metadata))
        base = self.make_response(body=b'base')

        with patch.object(probe, '_ShadowProbe__suffixes', ['.bak', '.old']):
            self.assertEqual(probe.enqueue('https://example.com/index.php', base, 'success'), 2)
            probe.drain()

        self.assertEqual(probe.completed, 2)
        self.assertEqual(probe.findings, 1)
        self.assertEqual(len(matches), 1)

    def test_config_reports_shadow_sniffer_state(self):
        """Should expose active shadow probing state only for the shadow sniffer."""

        enabled = Config({'sniff': 'shadow'})
        disabled = Config({'sniff': 'secret'})
        empty = Config({})

        self.assertTrue(enabled.is_shadow_sniff)
        self.assertFalse(disabled.is_shadow_sniff)
        self.assertFalse(empty.is_shadow_sniff)

    def test_response_debug_data_forwards_shadow_detection(self):
        """Should pass shadow detection metadata into runtime debug renderers."""

        debug = SimpleNamespace(debug_request_uri=MagicMock(), debug_classification=MagicMock())
        response_debug = Response(SimpleNamespace(is_sniff=False), debug)
        shadow_response = SimpleNamespace(opendoor_shadow_detection={'variant': '.bak'})
        secret_response = SimpleNamespace(opendoor_secret_detection={'type': 'generic'})
        stacktrace_response = SimpleNamespace(opendoor_stacktrace_detection={'runtime': 'python'})

        response_debug.debug_response_data(('shadow', 'https://example.com/index.php.bak', '4B', '200'),
                                           'https://example.com/index.php.bak', 1, 1, response=shadow_response)
        response_debug.debug_response_data(('secret', 'https://example.com/config.php', '4B', '200'),
                                           'https://example.com/config.php', 1, 1, response=secret_response)
        response_debug.debug_response_data(('stacktrace', 'https://example.com/debug', '4B', '500'),
                                           'https://example.com/debug', 1, 1, response=stacktrace_response)

        self.assertEqual(debug.debug_request_uri.call_args_list[0].kwargs['shadow_detection'], {'variant': '.bak'})
        self.assertEqual(debug.debug_classification.call_args_list[0].kwargs['shadow_detection'], {'variant': '.bak'})
        self.assertEqual(debug.debug_request_uri.call_args_list[1].kwargs['secret_detection'], {'type': 'generic'})
        self.assertEqual(debug.debug_request_uri.call_args_list[2].kwargs['stacktrace_detection'], {'runtime': 'python'})

    def test_debug_classification_renders_shadow_detection(self):
        """Should render shadow metadata in debug level 3 classification details."""

        cfg = SimpleNamespace(DEFAULT_SCAN='directories', scan='directories', debug=3, method='GET')
        debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.debug') as debug_mock:
            debug.debug_classification(
                status='shadow',
                code='200',
                size='21B',
                shadow_detection={'base_url': 'https://example.com/index.php', 'variant': '.bak', 'confidence': 95},
            )

        rendered = [call.kwargs.get('msg') for call in debug_mock.call_args_list]
        self.assertTrue(any('Shadow detection:' in str(item) for item in rendered))


class TestBrowserShadowIntegration(unittest.TestCase):
    """Browser integration tests for active shadow probe plumbing."""

    def make_browser(self):
        """Build a minimal Browser instance for private method coverage."""

        br = Browser.__new__(Browser)
        setattr(br, '_Browser__result', {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()})
        setattr(br, '_Browser__shadow_probe', None)
        setattr(br, '_Browser__pool', SimpleNamespace(items_size=1, total_items_size=3, workers_size=1))
        setattr(br, '_Browser__response', SimpleNamespace(
            _get_content_size=MagicMock(return_value='21B'),
            debug_response_data=MagicMock(),
        ))
        return br


    def test_browser_enqueue_shadow_probes_defensive_and_enabled_paths(self):
        """Should cover shadow enqueue guards and enabled delegation."""

        br = self.make_browser()
        response = HTTPResponse(status=200, body=b'base', headers={'Content-Type': 'text/html'})
        shadow_probe = SimpleNamespace(enqueue=MagicMock(return_value=2))
        setattr(br, '_Browser__shadow_probe', shadow_probe)

        self.assertEqual(br._Browser__enqueue_shadow_probes(None, response), 0)
        self.assertEqual(br._Browser__enqueue_shadow_probes(('success',), response), 0)
        self.assertEqual(br._Browser__enqueue_shadow_probes(('shadow', 'https://example.com/index.php'), response), 0)
        self.assertEqual(br._Browser__enqueue_shadow_probes(('success', 'https://example.com/index.php'), response), 2)

        shadow_probe.enqueue.assert_called_once_with('https://example.com/index.php', response, 'success')

    def test_browser_emits_shadow_probe_progress_and_fallback_size(self):
        """Should render shadow probe progress for misses and tolerate bad response objects."""

        br = self.make_browser()
        emit_mock = MagicMock(return_value=True)
        setattr(br, '_Browser__emit_filtered_progress', emit_mock)
        response = HTTPResponse(status=404, body=b'missing', headers={'Content-Type': 'text/html'})

        self.assertTrue(br._Browser__emit_shadow_probe_progress('https://example.com/index.php.bak', response, 1, 3))
        self.assertEqual(emit_mock.call_args_list[0].args[0], 'shadow-probe')
        self.assertEqual(emit_mock.call_args_list[0].args[2]['calibration_score'], '1/3')

        getattr(br, '_Browser__response')._get_content_size.side_effect = AttributeError('bad response')
        self.assertTrue(br._Browser__emit_shadow_probe_progress('https://example.com/index.php.old', object(), 2, 3))
        self.assertEqual(emit_mock.call_args_list[1].args[1], ('shadow-probe', 'https://example.com/index.php.old', '-', '-'))

    def test_browser_shadow_match_handles_missing_metadata_and_setattr_errors(self):
        """Should keep shadow match handling robust for partial metadata and frozen responses."""

        class FrozenResponse(object):
            status = 200

            def __setattr__(self, name, value):
                if name == 'opendoor_shadow_detection':
                    raise AttributeError('frozen')
                object.__setattr__(self, name, value)

        br = self.make_browser()
        response = FrozenResponse()

        br._Browser__handle_shadow_match('https://example.com/index.php.bak', response, {'shadow_detection': {'variant': '.bak'}})
        br._Browser__handle_shadow_match('https://example.com/index.php.old', response, {})

        self.assertFalse(hasattr(response, 'opendoor_shadow_detection'))
        self.assertEqual(getattr(br, '_Browser__result')['total']['shadow'], 2)

    def test_browser_shadow_match_skips_non_callable_debug_renderer(self):
        """Should persist shadow findings even when debug renderer is unavailable."""

        br = self.make_browser()
        setattr(br, '_Browser__response', SimpleNamespace(_get_content_size=MagicMock(return_value='21B'), debug_response_data=None))

        br._Browser__handle_shadow_match('https://example.com/index.php.bak', SimpleNamespace(status=200), {})

        self.assertEqual(getattr(br, '_Browser__result')['total']['shadow'], 1)

    def test_browser_shadow_drain_noop_and_zero_counter_paths(self):
        """Should no-op without a shadow queue and avoid empty probe counters."""

        br = self.make_browser()
        self.assertTrue(br._Browser__drain_shadow_probes())
        self.assertNotIn('shadow_probes', getattr(br, '_Browser__result')['total'])

        shadow_probe = SimpleNamespace(drain=MagicMock(), submitted=0)
        setattr(br, '_Browser__shadow_probe', shadow_probe)
        self.assertTrue(br._Browser__drain_shadow_probes())
        self.assertNotIn('shadow_probes', getattr(br, '_Browser__result')['total'])
        shadow_probe.drain.assert_called_once_with()

    def test_browser_preserves_shadow_detection_metadata(self):
        """Should store shadow metadata as one nested report object."""

        br = self.make_browser()
        detection = {'type': 'backup_copy', 'base_url': 'https://example.com/index.php', 'variant': '.bak'}

        br._Browser__catch_report_data(
            'shadow',
            'https://example.com/index.php.bak',
            '21B',
            '200',
            metadata={'shadow_detection': detection},
        )

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['shadow'], 1)
        self.assertEqual(result['items']['shadow'], ['https://example.com/index.php.bak'])
        self.assertEqual(result['report_items']['shadow'][0]['shadow_detection'], detection)

    def test_browser_does_not_enqueue_when_shadow_is_disabled(self):
        """Should leave normal success flow untouched when --sniff shadow is absent."""

        br = self.make_browser()
        response = HTTPResponse(status=200, body=b'base', headers={'Content-Type': 'text/html'})

        self.assertEqual(br._Browser__enqueue_shadow_probes(('success', 'https://example.com/index.php'), response), 0)

    def test_browser_drains_shadow_before_summary_and_records_probe_counter(self):
        """Should drain shadow queue before summary/report generation."""

        br = self.make_browser()
        shadow_probe = SimpleNamespace(drain=MagicMock(), submitted=3)
        setattr(br, '_Browser__shadow_probe', shadow_probe)

        br._Browser__drain_shadow_probes()

        shadow_probe.drain.assert_called_once_with()
        self.assertEqual(getattr(br, '_Browser__result')['total']['shadow_probes'], 3)

    def test_browser_shadow_match_renders_and_records_shadow_bucket(self):
        """Should render OK - Shadow progress and persist the shadow bucket."""

        br = self.make_browser()
        response = HTTPResponse(status=200, body=b'base', headers={'Content-Type': 'text/html'})
        metadata = {
            'shadow_detection': {
                'type': 'backup_copy',
                'base_url': 'https://example.com/index.php',
                'variant': '.bak',
            }
        }

        br._Browser__handle_shadow_match('https://example.com/index.php.bak', response, metadata)

        debug_response_data = getattr(br, '_Browser__response').debug_response_data
        debug_response_data.assert_called_once()
        self.assertEqual(debug_response_data.call_args.kwargs['response'], response)
        self.assertEqual(response.opendoor_shadow_detection, metadata['shadow_detection'])
        self.assertEqual(getattr(br, '_Browser__result')['total']['shadow'], 1)

    def test_debug_request_uri_renders_shadow_marker(self):
        """Should render shadow findings as OK plus red Shadow marker."""

        cfg = SimpleNamespace(DEFAULT_SCAN='directories', scan='directories', debug=0, method='GET')
        debug = Debug(cfg)

        with patch('src.lib.browser.debug.tpl.line') as line_mock, \
                patch('src.lib.browser.debug.tpl.info') as info_mock, \
                patch('src.lib.browser.debug.sys.writels'):
            line_mock.side_effect = lambda **kwargs: kwargs.get('msg') or kwargs.get('key') or kwargs.get('url')
            debug.debug_request_uri(
                status='shadow',
                request_uri='https://example.com/index.php.bak',
                items_size=1,
                total_size=1,
                content_size='21B',
                response_code='200',
            )

        rendered_item = info_mock.call_args.kwargs['item']
        self.assertIn('OK', rendered_item)
        self.assertIn('Shadow', rendered_item)


if __name__ == '__main__':
    unittest.main()
