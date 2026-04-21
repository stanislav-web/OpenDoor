# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.core import CoreSystemError, FileSystemError
from src.lib.reader.reader import Reader
from src.lib.reader.exceptions import ReaderError


class TestReaderExtra(unittest.TestCase):
    """Extra branch coverage tests for Reader."""

    def make_reader(self, browser_config=None, core_config=None):
        """Build Reader with a patched core data config."""

        if browser_config is None:
            browser_config = {
                'list': 'directories',
                'torlist': 'external-tor.txt',
                'use_random': False,
                'use_extensions': False,
                'use_ignore_extensions': False,
                'is_external_wordlist': False,
                'wordlist': '/tmp/external.txt',
                'is_standalone_proxy': False,
                'is_external_torlist': False,
                'prefix': '',
            }

        if core_config is None:
            core_config = {
                'directories': '/tmp/directories.txt',
                'subdomains': '/tmp/subdomains.txt',
                'tmplist': '/tmp/tmplist.txt',
                'extensionlist': '/tmp/extensionlist.txt',
                'ignore_extensionlist': '/tmp/ignore_extensionlist.txt',
                'useragents': '/tmp/useragents.txt',
                'ignored': '/tmp/ignored.txt',
                'proxies': '/tmp/proxies.txt',
            }

        with patch('src.lib.reader.reader.CoreConfig', {'data': core_config}):
            return Reader(browser_config)

    def test_get_dirlist_path_prefers_ignore_extensions_and_external_wordlist(self):
        """Reader._get_dirlist_path() should support ignore-extension and external-wordlist modes."""

        reader = self.make_reader({
            'list': 'directories',
            'torlist': 'external-tor.txt',
            'use_random': False,
            'use_extensions': False,
            'use_ignore_extensions': True,
            'is_external_wordlist': False,
            'wordlist': '/tmp/external.txt',
            'is_standalone_proxy': False,
            'is_external_torlist': False,
            'prefix': '',
        })
        self.assertEqual(reader._get_dirlist_path(), '/tmp/ignore_extensionlist.txt')

        reader = self.make_reader({
            'list': 'directories',
            'torlist': 'external-tor.txt',
            'use_random': False,
            'use_extensions': False,
            'use_ignore_extensions': False,
            'is_external_wordlist': True,
            'wordlist': '/tmp/external.txt',
            'is_standalone_proxy': False,
            'is_external_torlist': False,
            'prefix': '',
        })
        self.assertEqual(reader._get_dirlist_path(), '/tmp/external.txt')

    def test_get_proxies_returns_empty_for_standalone_proxy(self):
        """Reader.get_proxies() should return an empty list for standalone proxy mode."""

        reader = self.make_reader({
            'list': 'directories',
            'torlist': 'external-tor.txt',
            'use_random': False,
            'use_extensions': False,
            'use_ignore_extensions': False,
            'is_external_wordlist': False,
            'wordlist': '/tmp/external.txt',
            'is_standalone_proxy': True,
            'is_external_torlist': False,
            'prefix': '',
        })

        with patch('src.lib.reader.reader.filesystem.read') as read_mock:
            self.assertEqual(reader.get_proxies(), [])
        read_mock.assert_not_called()

    def test_get_proxies_reads_external_torlist(self):
        """Reader.get_proxies() should prefer external torlist when enabled."""

        reader = self.make_reader({
            'list': 'directories',
            'torlist': '/tmp/external-tor.txt',
            'use_random': False,
            'use_extensions': False,
            'use_ignore_extensions': False,
            'is_external_wordlist': False,
            'wordlist': '/tmp/external.txt',
            'is_standalone_proxy': False,
            'is_external_torlist': True,
            'prefix': '',
        })

        with patch('src.lib.reader.reader.filesystem.read', return_value=['1.1.1.1:80']) as read_mock:
            self.assertEqual(reader.get_proxies(), ['1.1.1.1:80'])

        read_mock.assert_called_once_with('/tmp/external-tor.txt')

    def test_get_proxies_returns_cached_default_proxies_without_reread(self):
        """Reader.get_proxies() should reuse cached default proxies."""

        reader = self.make_reader()
        setattr(reader, '_Reader__proxies', ['2.2.2.2:8080'])

        with patch('src.lib.reader.reader.filesystem.read') as read_mock:
            self.assertEqual(reader.get_proxies(), ['2.2.2.2:8080'])

        read_mock.assert_not_called()

    def test_get_lines_prepares_subdomain_loader_params_and_strips_www(self):
        """Reader.get_lines() should prepare subdomain params using host_no_www and port_suffix."""

        reader = self.make_reader({
            'list': 'subdomains',
            'torlist': 'external-tor.txt',
            'use_random': False,
            'use_extensions': False,
            'use_ignore_extensions': False,
            'is_external_wordlist': False,
            'wordlist': '/tmp/external.txt',
            'is_standalone_proxy': False,
            'is_external_torlist': False,
            'prefix': '',
        })

        with patch('src.lib.reader.reader.filesystem.readline') as readline_mock:
            reader.get_lines(
                params={'scheme': 'https://', 'host': 'www.example.com', 'port': 443},
                loader='loader-callback'
            )

        kwargs = readline_mock.call_args.kwargs
        self.assertEqual(kwargs['handler_params']['host_no_www'], 'example.com')
        self.assertEqual(kwargs['handler_params']['port_suffix'], '')
        self.assertEqual(kwargs['loader'], 'loader-callback')

    def test_get_lines_wraps_filesystem_errors(self):
        """Reader.get_lines() should wrap readline failures into ReaderError."""

        reader = self.make_reader()

        with patch('src.lib.reader.reader.filesystem.readline', side_effect=FileSystemError('boom')):
            with self.assertRaises(ReaderError):
                reader.get_lines(
                    params={'scheme': 'http://', 'host': 'example.com', 'port': 80},
                    loader='loader-callback'
                )

    def test_subdomains_line_uses_host_and_port_fallbacks(self):
        """Reader._subdomains__line() should derive host and port when helper params are missing."""

        result = Reader._subdomains__line(
            'admin',
            {'scheme': 'http://', 'host': 'www.example.com', 'port': 8080}
        )

        self.assertEqual(result, 'http://admin.example.com:8080')

    def test_directories_line_uses_reader_prefix_and_builds_base_url(self):
        """Reader._directories__line() should fall back to reader prefix and base_url generation."""

        reader = self.make_reader({
            'list': 'directories',
            'torlist': 'external-tor.txt',
            'use_random': False,
            'use_extensions': False,
            'use_ignore_extensions': False,
            'is_external_wordlist': False,
            'wordlist': '/tmp/external.txt',
            'is_standalone_proxy': False,
            'is_external_torlist': False,
            'prefix': 'api/',
        })

        result = reader._directories__line(
            'users',
            {'scheme': 'http://', 'host': 'example.com', 'port': 8080}
        )

        self.assertEqual(result, 'http://example.com:8080/api/users')

    def test_randomize_list_uses_windows_shuffle_branch(self):
        """Reader.randomize_list() should use filesystem.shuffle() on Windows."""

        reader = self.make_reader()
        setattr(reader, '_Reader__counter', 7)

        with patch('src.lib.reader.reader.filesystem.makefile', return_value='/tmp/out.txt') as makefile_mock, \
                patch('src.lib.reader.reader.filesystem.shuffle') as shuffle_mock, \
                patch('src.lib.reader.reader.process.execute') as execute_mock, \
                patch('src.lib.reader.reader.sys', return_value=SimpleNamespace(is_windows=True)):
            reader.randomize_list('directories', 'tmplist')

        makefile_mock.assert_called_once_with('/tmp/tmplist.txt')
        shuffle_mock.assert_called_once_with(target='/tmp/directories.txt', output='/tmp/out.txt', total=7)
        execute_mock.assert_not_called()

    def test_randomize_list_wraps_makefile_errors(self):
        """Reader.randomize_list() should wrap filesystem failures into ReaderError."""

        reader = self.make_reader()

        with patch('src.lib.reader.reader.filesystem.makefile', side_effect=FileSystemError('boom')):
            with self.assertRaises(ReaderError):
                reader.randomize_list('directories', 'tmplist')

    def test_randomize_list_wraps_process_errors(self):
        """Reader.randomize_list() should wrap process failures into ReaderError."""

        reader = self.make_reader()

        with patch('src.lib.reader.reader.filesystem.makefile', return_value='/tmp/out.txt'), \
                patch('src.lib.reader.reader.sys', return_value=SimpleNamespace(is_windows=False)), \
                patch('src.lib.reader.reader.process.execute', side_effect=CoreSystemError('boom')):
            with self.assertRaises(ReaderError):
                reader.randomize_list('directories', 'tmplist')

    def test_count_total_lines_uses_random_tmp_list_and_caches_result(self):
        """Reader.count_total_lines() should use tmplist in random mode and then reuse cached count."""

        reader = self.make_reader({
            'list': 'directories',
            'torlist': 'external-tor.txt',
            'use_random': True,
            'use_extensions': False,
            'use_ignore_extensions': False,
            'is_external_wordlist': False,
            'wordlist': '/tmp/external.txt',
            'is_standalone_proxy': False,
            'is_external_torlist': False,
            'prefix': '',
        })

        with patch('src.lib.reader.reader.filesystem.count_lines', return_value=11) as count_mock:
            first = reader.count_total_lines()
            second = reader.count_total_lines()

        self.assertEqual(first, 11)
        self.assertEqual(second, 11)
        self.assertEqual(reader.total_lines, 11)
        count_mock.assert_called_once_with('/tmp/tmplist.txt')

    def test_count_total_lines_uses_existing_counter_without_filesystem_call(self):
        """Reader.count_total_lines() should return cached counter without recounting."""

        reader = self.make_reader()
        setattr(reader, '_Reader__counter', 5)

        with patch('src.lib.reader.reader.filesystem.count_lines') as count_mock:
            result = reader.count_total_lines()

        self.assertEqual(result, 5)
        self.assertEqual(reader.total_lines, 5)
        count_mock.assert_not_called()

    def test_count_total_lines_wraps_filesystem_errors(self):
        """Reader.count_total_lines() should wrap count_lines failures into ReaderError."""

        reader = self.make_reader()

        with patch('src.lib.reader.reader.filesystem.count_lines', side_effect=FileSystemError('boom')):
            with self.assertRaises(ReaderError):
                reader.count_total_lines()

    def test_normalize_extensions_drops_empty_items(self):
        """Reader._normalize_extensions() should skip empty or dot-only entries."""

        self.assertEqual(
            Reader._normalize_extensions(['.php', '', ' .js ', '.']),
            ['php', 'js']
        )

    def test_get_ignored_list_uses_cached_values_without_reread(self):
        """Reader.get_ignored_list() should return cached ignored values without rereading the file."""

        reader = self.make_reader()
        setattr(reader, '_Reader__ignored', ['admin'])

        with patch('src.lib.reader.reader.filesystem.read') as read_mock:
            actual = reader.get_ignored_list()

        self.assertEqual(actual, ['admin'])
        read_mock.assert_not_called()

    def test_get_ignored_list_skips_blank_and_root_only_entries(self):
        """Reader.get_ignored_list() should skip blanks and slash-only entries."""

        reader = self.make_reader()
        with patch('src.lib.reader.reader.filesystem.read', return_value=['\n', '/\n', '/admin/\n']):
            actual = reader.get_ignored_list()

        self.assertEqual(actual, ['admin'])

    def test_get_lines_prepares_subdomain_params_without_www_prefix(self):
        """Reader.get_lines() should preserve host when it does not start with www."""

        reader = self.make_reader({
            'list': 'subdomains',
            'torlist': 'external-tor.txt',
            'use_random': False,
            'use_extensions': False,
            'use_ignore_extensions': False,
            'is_external_wordlist': False,
            'wordlist': '/tmp/external.txt',
            'is_standalone_proxy': False,
            'is_external_torlist': False,
            'prefix': '',
        })

        with patch('src.lib.reader.reader.filesystem.readline') as readline_mock:
            reader.get_lines(
                params={'scheme': 'https://', 'host': 'api.example.com', 'port': 8080},
                loader='loader-callback'
            )

        kwargs = readline_mock.call_args.kwargs
        self.assertEqual(kwargs['handler_params']['host_no_www'], 'api.example.com')
        self.assertEqual(kwargs['handler_params']['port_suffix'], ':8080')

    def test_subdomains_line_prefers_prepared_host_and_port_suffix(self):
        """Reader._subdomains__line() should use host_no_www and port_suffix when already prepared."""

        result = Reader._subdomains__line(
            'admin',
            {'scheme': 'https://', 'host_no_www': 'example.com', 'port_suffix': ':8443'}
        )

        self.assertEqual(result, 'https://admin.example.com:8443')

    def test_directories_line_uses_prepared_prefix_and_base_url(self):
        """Reader._directories__line() should use prepared prefix and base_url when provided."""

        reader = self.make_reader({
            'list': 'directories',
            'torlist': 'external-tor.txt',
            'use_random': False,
            'use_extensions': False,
            'use_ignore_extensions': False,
            'is_external_wordlist': False,
            'wordlist': '/tmp/external.txt',
            'is_standalone_proxy': False,
            'is_external_torlist': False,
            'prefix': '',
        })

        result = reader._directories__line(
            'users',
            {'prefix': 'api/', 'base_url': 'https://example.com:8443/'}
        )

        self.assertEqual(result, 'https://example.com:8443/api/users')

if __name__ == '__main__':
    unittest.main()