# -*- coding: utf-8 -*-

import unittest

from src.lib.reader import WordlistSource


class TestWordlistSource(unittest.TestCase):
    """Wordlist source metadata tests."""

    def test_none_value_is_bundled(self):
        """Missing --wordlist should be classified as bundled."""

        source = WordlistSource.from_value(None)

        self.assertEqual(source.source_type, WordlistSource.BUNDLED)
        self.assertEqual(source.marker, 'internal')
        self.assertIsNone(source.runtime_path)

    def test_local_path_is_external_local(self):
        """Filesystem path should be classified as local external source."""

        source = WordlistSource.from_value('./wordlists/admin.txt')

        self.assertEqual(source.source_type, WordlistSource.LOCAL)
        self.assertEqual(source.marker, 'external')
        self.assertEqual(source.runtime_path, './wordlists/admin.txt')

    def test_http_url_is_external_remote(self):
        """HTTP URL should be classified as remote external source."""

        source = WordlistSource.from_value('http://example.test/admin.txt')

        self.assertEqual(source.source_type, WordlistSource.REMOTE)
        self.assertEqual(source.marker, 'external')
        self.assertEqual(source.scheme, 'http')
        self.assertIsNone(source.runtime_path)

    def test_https_url_is_external_remote(self):
        """HTTPS URL should be classified as remote external source."""

        source = WordlistSource.from_value('https://example.test/admin.txt')

        self.assertEqual(source.source_type, WordlistSource.REMOTE)
        self.assertEqual(source.marker, 'external')
        self.assertEqual(source.scheme, 'https')

    def test_remote_source_can_carry_resolved_runtime_path(self):
        """Remote source should support a future local runtime path."""

        source = WordlistSource.from_value(
            'https://example.test/admin.txt',
            resolved_value='/tmp/opendoor/remote-wordlist.txt',
        )

        self.assertEqual(source.source_type, WordlistSource.REMOTE)
        self.assertEqual(source.runtime_path, '/tmp/opendoor/remote-wordlist.txt')

    def test_custom_wordlist_applies_only_to_active_scan_list(self):
        """Only the active scan row should be marked as external."""

        params = {'scan': 'directories', 'wordlist': './wordlists/admin.txt'}

        directories = WordlistSource.from_scan_params(params, 'directories')
        subdomains = WordlistSource.from_scan_params(params, 'subdomains')

        self.assertEqual(directories.source_type, WordlistSource.LOCAL)
        self.assertEqual(subdomains.source_type, WordlistSource.BUNDLED)
