# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace

from src.lib.browser.sniffers import SnifferCatalog, SnifferContext, SnifferEngine, SnifferResult


class _Detector:
    """Fake additive detector."""

    NAME = 'detector'
    KIND = 'detector'
    PRIORITY = 20

    def match(self, context):
        """Return one additive finding."""

        return SnifferResult(
            bucket='detector',
            url=context.request_url,
            code=context.code,
            size=context.size,
            metadata={'source': self.NAME},
            suppress_normal=True,
        )


class _SecondDetector:
    """Fake second additive detector."""

    NAME = 'second'
    KIND = 'detector'
    PRIORITY = 10

    def match(self, context):
        """Return one second finding."""

        return SnifferResult(bucket='second', url=context.request_url, code=context.code, size=context.size)


class _Suppressor:
    """Fake suppressor."""

    NAME = 'skipempty'
    KIND = 'suppressor'
    PRIORITY = 10

    def match(self, context):
        """Return one suppressor result."""

        return SnifferResult(
            bucket='skipempty',
            url=context.request_url,
            code=context.code,
            size=context.size,
            metadata={'suppress_reason': 'empty response'},
            suppress_normal=True,
        )


class _ActiveDetector:
    """Fake active detector."""

    NAME = 'active'
    KIND = 'active'
    PRIORITY = 10

    def match(self, context):
        """Return one active finding."""

        return SnifferResult(bucket='active', url=context.request_url, code=302, size=0)


class _UnknownKindDetector:
    """Fake detector with unknown kind."""

    NAME = 'unknown-kind'
    KIND = 'unknown'

    def match(self, context):
        """Return one finding using detector fallback kind."""

        return SnifferResult(bucket='unknown-kind', url=context.request_url)


class _EmptyDetector:
    """Fake detector without findings."""

    NAME = 'empty'

    def match(self, _context):
        """Return no findings."""


class TestSnifferEngine(unittest.TestCase):
    """TestSnifferEngine class."""

    def make_context(self):
        """Create a shared sniffer context."""

        return SnifferContext(
            request_url='https://example.com/favicon.ico',
            base_status='success',
            code=200,
            size='1KB',
            body='body',
            headers={'Content-Type': 'text/plain'},
            metadata={'scan': 'directories'},
        )

    def test_context_copies_headers_and_metadata(self):
        """SnifferContext should copy mutable mappings."""

        headers = {'Content-Type': 'text/plain'}
        metadata = {'source': 'test'}
        context = SnifferContext('https://example.com/', headers=headers, metadata=metadata)

        headers['Content-Type'] = 'application/json'
        metadata['source'] = 'changed'

        self.assertEqual(context.headers['Content-Type'], 'text/plain')
        self.assertEqual(context.metadata['source'], 'test')

    def test_context_with_metadata_returns_copy(self):
        """SnifferContext.with_metadata() should preserve the original context."""

        context = self.make_context()
        updated = context.with_metadata(sniffer='malware')

        self.assertIsNot(updated, context)
        self.assertEqual(updated.request_url, context.request_url)
        self.assertEqual(updated.metadata['scan'], 'directories')
        self.assertEqual(updated.metadata['sniffer'], 'malware')
        self.assertNotIn('sniffer', context.metadata)

    def test_result_builds_bucket_local_dedupe_key(self):
        """SnifferResult should build stable bucket-local dedupe keys."""

        result = SnifferResult(
            bucket='malware',
            url='https://example.com/shell.php',
            metadata={'evidence': 'WSO'},
        )

        self.assertEqual(result.dedupe_key(), ('malware', 'https://example.com/shell.php', 'WSO'))

    def test_engine_uses_config_sniffers_as_case_insensitive_enable_set(self):
        """SnifferEngine.from_config() should normalize configured sniffer aliases."""

        config = SimpleNamespace(sniffers=['Second', 'DETECTOR'])
        engine = SnifferEngine.from_config(config, sniffers=[_Detector(), _SecondDetector(), _Suppressor()])

        self.assertEqual(engine.registered_names(), ['detector', 'second', 'skipempty'])
        self.assertEqual(engine.active_names(), ['second', 'detector'])

    def test_passive_engine_runs_all_enabled_detectors_without_terminal_match(self):
        """Passive engine should collect all enabled detector findings."""

        engine = SnifferEngine(
            enabled=['detector', 'second'],
            sniffers=[_Detector(), _SecondDetector()],
        )
        decision = engine.run_passive(self.make_context())

        self.assertEqual([result.bucket for result in decision.findings], ['second', 'detector'])
        self.assertTrue(decision.suppress_normal)
        self.assertEqual(decision.suppress_reasons, ['detector'])

    def test_passive_engine_runs_suppressors_without_blocking_detectors(self):
        """Suppressors should suppress normal reporting without blocking detector findings."""

        engine = SnifferEngine(
            enabled=['skipempty', 'detector'],
            sniffers=[_Suppressor(), _Detector()],
        )
        decision = engine.run_passive(self.make_context())

        self.assertEqual([result.bucket for result in decision.findings], ['detector', 'skipempty'])
        self.assertTrue(decision.suppress_normal)
        self.assertEqual(decision.suppress_reasons, ['detector', 'empty response'])

    def test_passive_engine_does_not_run_active_sniffers(self):
        """Passive phase should skip active sniffers."""

        engine = SnifferEngine(enabled=['active', 'detector'], sniffers=[_ActiveDetector(), _Detector()])
        decision = engine.run_passive(self.make_context())

        self.assertEqual([result.bucket for result in decision.findings], ['detector'])

    def test_active_engine_runs_only_active_sniffers(self):
        """Active phase should only run active sniffers."""

        engine = SnifferEngine(enabled=['active', 'detector'], sniffers=[_ActiveDetector(), _Detector()])
        findings = engine.run_active(self.make_context())

        self.assertEqual([result.bucket for result in findings], ['active'])

    def test_engine_skips_disabled_and_empty_sniffers(self):
        """Engine should skip disabled sniffers and normalize empty matches."""

        engine = SnifferEngine(
            enabled=['empty', 'unknown-kind'],
            sniffers=[_EmptyDetector(), _UnknownKindDetector(), _Detector()],
        )
        decision = engine.run_passive(self.make_context())

        self.assertEqual([result.bucket for result in decision.findings], ['unknown-kind'])


class TestSnifferCatalog(unittest.TestCase):
    """Sniffer catalog metadata tests."""

    def test_builtin_catalog_lists_existing_public_sniffer_aliases(self):
        """Catalog should preserve existing public --sniff aliases."""

        catalog = SnifferCatalog.builtin()

        self.assertEqual(
            catalog.names(),
            [
                'file',
                'secret',
                'indexof',
                'stacktrace',
                'skipempty',
                'skipsizes',
                'collation',
                'shadow',
                'openredirect',
            ],
        )

    def test_catalog_classifies_detector_suppressor_and_active_sniffers(self):
        """Catalog should expose stable sniffer kind groupings."""

        catalog = SnifferCatalog.builtin()
        enabled = ['openredirect', 'secret', 'skipempty', 'shadow', 'file']

        self.assertEqual([item.name for item in catalog.detectors(enabled)], ['file', 'secret'])
        self.assertEqual([item.name for item in catalog.suppressors(enabled)], ['skipempty'])
        self.assertEqual([item.name for item in catalog.active(enabled)], ['shadow', 'openredirect'])

    def test_catalog_reports_body_required_sniffers(self):
        """Catalog should identify when enabled sniffers require response bodies."""

        catalog = SnifferCatalog.builtin()

        self.assertFalse(catalog.requires_body(['file', 'openredirect']))
        self.assertTrue(catalog.requires_body(['file', 'secret']))
        self.assertTrue(catalog.requires_body(['shadow']))

    def test_engine_returns_enabled_descriptors_from_config(self):
        """SnifferEngine descriptor helpers should use configured sniffer aliases."""

        config = SimpleNamespace(sniffers=['secret', 'openredirect', 'shadow'])

        self.assertEqual(
            [item.name for item in SnifferEngine.descriptors_from_config(config)],
            ['secret', 'shadow', 'openredirect'],
        )
        self.assertEqual(
            [item.name for item in SnifferEngine.active_descriptors_from_config(config)],
            ['shadow', 'openredirect'],
        )
        self.assertEqual(SnifferEngine.active_names_from_config(config), {'shadow', 'openredirect'})


if __name__ == '__main__':
    unittest.main()
