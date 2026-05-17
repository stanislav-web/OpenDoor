# -*- coding: utf-8 -*-

import unittest

from src.lib.browser.sniffers import (
    SnifferCatalog,
    SnifferDescriptor,
    SnifferResult,
)


class _TupleResultDetector:
    """Fake detector that returns findings as a tuple."""

    NAME = 'tuple'
    KIND = 'detector'

    def match(self, context):
        """Return one finding wrapped in a tuple."""

        return (
            SnifferResult(
                bucket='tuple',
                url=context.request_url,
                code=context.code,
                size=context.size,
                evidence_key='tuple-evidence',
            ),
        )


class _ListResultDetector:
    """Fake detector that returns findings as a list."""

    NAME = 'list'
    KIND = 'detector'

    def match(self, context):
        """Return one finding wrapped in a list."""

        return [
            SnifferResult(
                bucket='list',
                url=context.request_url,
                code=context.code,
                size=context.size,
            )
        ]


class TestSnifferCoverageExtra(unittest.TestCase):
    """Additional coverage tests for sniffer primitives."""

    def test_catalog_descriptor_lookup_and_missing_descriptor(self):
        """Catalog should expose explicit descriptor lookup."""

        catalog = SnifferCatalog.builtin()
        descriptor = catalog.descriptor('openredirect')

        self.assertIsNotNone(descriptor)
        self.assertEqual(descriptor.name, 'openredirect')
        self.assertTrue(descriptor.active)
        self.assertIsNone(catalog.descriptor('missing-sniffer'))

    def test_descriptor_as_dict_contains_runtime_metadata(self):
        """SnifferDescriptor.as_dict() should expose stable metadata."""

        descriptor = SnifferDescriptor(
            name='malware',
            bucket='malware',
            kind='detector',
            display_name='Malware',
            requires_body=True,
            priority=50,
        )

        self.assertEqual(
            descriptor.as_dict(),
            {
                'bucket': 'malware',
                'display_name': 'Malware',
                'kind': 'detector',
                'name': 'malware',
                'priority': 50,
                'requires_body': True,
            },
        )
