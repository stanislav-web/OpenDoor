# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development Team: Brain Storm Team
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.filesystem.exceptions import FileSystemError
from src.core.logger.logger import Logger
from src.lib.reader import Reader, ReaderError


class TestReader(unittest.TestCase):
    """TestReader class."""

    def setUp(self):
        """Create isolated temp paths used by reader tests."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.config = {
            'directories': 'tests/data/directories.dat',
            'subdomains': 'tests/data/subdomains.dat',
            'ignored': 'tests/data/ignored.dat',
            'proxies': 'tests/data/proxies.dat',
            'useragents': 'tests/data/useragents.dat',
            'tmplist': os.path.join(self.base_dir, 'list.tmp'),
            'extensionlist': os.path.join(self.base_dir, 'extensionlist.tmp'),
            'ignore_extensionlist': os.path.join(self.base_dir, 'ignore_extensionlist.tmp'),
        }

    def tearDown(self):
        """Cleanup temp paths and logger handlers."""

        logger = Logger.log()
        for handler in logger.handlers:
            logger.removeHandler(handler)

        self.temp_dir.cleanup()

    def create_reader(self, browser_config):
        """Create a reader instance with a deterministic config mapping."""

        reader = Reader(browser_config=browser_config)
        setattr(reader, '_Reader__config', self.config)
        return reader

    def test_get_user_agents_returns_cached_values(self):
        """Reader.get_user_agents() should cache loaded user agents."""

        reader = self.create_reader(browser_config={})

        with patch('src.lib.reader.reader.filesystem.read', return_value=['UA-1\n', 'UA-2\n']) as read_mock:
            first = reader.get_user_agents()
            second = reader.get_user_agents()

        self.assertEqual(first, ['UA-1\n', 'UA-2\n'])
        self.assertIs(first, second)
        read_mock.assert_called_once_with(self.config['useragents'])

    def test_get_user_agents_raises_reader_error(self):
        """Reader.get_user_agents() should wrap file errors."""

        reader = self.create_reader(browser_config={})

        with patch('src.lib.reader.reader.filesystem.read', side_effect=FileSystemError('failed')):
            with self.assertRaises(ReaderError):
                reader.get_user_agents()

    def test_get_ignored_list_normalizes_leading_slashes(self):
        """Reader.get_ignored_list() should strip leading slashes and newlines."""

        ignored_file = os.path.join(self.base_dir, 'ignored.dat')
        with open(ignored_file, 'w', encoding='utf-8') as handler:
            handler.write('/admin/\nstatus\n')

        self.config['ignored'] = ignored_file
        reader = self.create_reader(browser_config={})

        ignored = reader.get_ignored_list()

        self.assertEqual(ignored, ['admin', 'status'])

    def test_get_ignored_list_raises_reader_error(self):
        """Reader.get_ignored_list() should wrap file errors."""

        reader = self.create_reader(browser_config={})

        with patch('src.lib.reader.reader.filesystem.read', side_effect=FileSystemError('failed')):
            with self.assertRaises(ReaderError):
                reader.get_ignored_list()

    def test_get_proxies_returns_empty_list_for_standalone_proxy(self):
        """Reader.get_proxies() should skip proxy lists when standalone proxy is used."""

        reader = self.create_reader(browser_config={'is_standalone_proxy': True})

        self.assertEqual(reader.get_proxies(), [])

    def test_get_proxies_reads_default_proxy_list(self):
        """Reader.get_proxies() should use the bundled proxy list by default."""

        reader = self.create_reader(browser_config={'is_standalone_proxy': False})

        with patch('src.lib.reader.reader.filesystem.read', return_value=['http://proxy:80\n']) as read_mock:
            proxies = reader.get_proxies()

        self.assertEqual(proxies, ['http://proxy:80\n'])
        read_mock.assert_called_once_with(self.config['proxies'])

    def test_get_proxies_reads_external_torlist(self):
        """Reader.get_proxies() should prefer an external tor list when configured."""

        torlist_path = os.path.join(self.base_dir, 'torlist.dat')
        reader = self.create_reader(
            browser_config={
                'is_standalone_proxy': False,
                'is_external_torlist': True,
                'torlist': torlist_path,
            }
        )

        with patch('src.lib.reader.reader.filesystem.read', return_value=['socks5://127.0.0.1:9050\n']) as read_mock:
            proxies = reader.get_proxies()

        self.assertEqual(proxies, ['socks5://127.0.0.1:9050\n'])
        read_mock.assert_called_once_with(torlist_path)

    def test_get_proxies_raises_reader_error(self):
        """Reader.get_proxies() should wrap file errors."""

        reader = self.create_reader(browser_config={'is_standalone_proxy': False})

        with patch('src.lib.reader.reader.filesystem.read', side_effect=FileSystemError('failed')):
            with self.assertRaises(ReaderError):
                reader.get_proxies()

    def test_get_lines_uses_randomized_list_when_enabled(self):
        """Reader.get_lines() should read the randomized list when requested."""

        reader = self.create_reader(
            browser_config={
                'use_random': True,
                'list': 'directories',
            }
        )

        with patch('src.lib.reader.reader.filesystem.readline') as readline_mock:
            reader.get_lines(params={'scheme': 'http://', 'host': 'example.com', 'port': 80}, loader=lambda lines: lines)

        self.assertEqual(readline_mock.call_args[0][0], self.config['tmplist'])

    def test_get_lines_uses_extension_list_when_enabled(self):
        """Reader.get_lines() should read the filtered extension list when requested."""

        reader = self.create_reader(
            browser_config={
                'use_extensions': True,
                'list': 'directories',
            }
        )

        with patch('src.lib.reader.reader.filesystem.readline') as readline_mock:
            reader.get_lines(params={'scheme': 'http://', 'host': 'example.com', 'port': 80}, loader=lambda lines: lines)

        self.assertEqual(readline_mock.call_args[0][0], self.config['extensionlist'])

    def test_get_lines_uses_ignore_extension_list_when_enabled(self):
        """Reader.get_lines() should read the ignore-extension list when requested."""

        reader = self.create_reader(
            browser_config={
                'use_ignore_extensions': True,
                'list': 'directories',
            }
        )

        with patch('src.lib.reader.reader.filesystem.readline') as readline_mock:
            reader.get_lines(params={'scheme': 'http://', 'host': 'example.com', 'port': 80}, loader=lambda lines: lines)

        self.assertEqual(readline_mock.call_args[0][0], self.config['ignore_extensionlist'])

    def test_get_lines_uses_external_wordlist_when_enabled(self):
        """Reader.get_lines() should use the external wordlist when configured."""

        wordlist = os.path.join(self.base_dir, 'external.dat')
        reader = self.create_reader(
            browser_config={
                'is_external_wordlist': True,
                'wordlist': wordlist,
                'list': 'directories',
            }
        )

        with patch('src.lib.reader.reader.filesystem.readline') as readline_mock:
            reader.get_lines(params={'scheme': 'http://', 'host': 'example.com', 'port': 80}, loader=lambda lines: lines)

        self.assertEqual(readline_mock.call_args[0][0], wordlist)

    def test_get_lines_uses_default_list_when_no_override_is_enabled(self):
        """Reader.get_lines() should use the default configured list."""

        reader = self.create_reader(browser_config={'list': 'subdomains'})

        with patch('src.lib.reader.reader.filesystem.readline') as readline_mock:
            reader.get_lines(params={'scheme': 'http://', 'host': 'example.com', 'port': 80}, loader=lambda lines: lines)

        self.assertEqual(readline_mock.call_args[0][0], self.config['subdomains'])

    def test_get_lines_raises_reader_error(self):
        """Reader.get_lines() should wrap file errors."""

        reader = self.create_reader(browser_config={'list': 'directories'})

        with patch('src.lib.reader.reader.filesystem.readline', side_effect=FileSystemError('failed')):
            with self.assertRaises(ReaderError):
                reader.get_lines(params={'scheme': 'http://', 'host': 'example.com', 'port': 80}, loader=lambda lines: lines)

    def test_subdomains_line_uses_default_port_without_suffix(self):
        """Reader._subdomains__line() should omit the default HTTP port."""

        line = Reader._subdomains__line('www\n', {'scheme': 'http://', 'host': 'www.example.com', 'port': 80})

        self.assertEqual(line, 'http://www.example.com')

    def test_subdomains_line_uses_non_default_port_suffix(self):
        """Reader._subdomains__line() should append a non-default port."""

        line = Reader._subdomains__line('api\n', {'scheme': 'https://', 'host': 'www.example.com', 'port': 8443})

        self.assertEqual(line, 'https://api.example.com:8443')

    def test_directories_line_uses_prefix_when_configured(self):
        """Reader._directories__line() should prepend the configured prefix."""

        reader = self.create_reader(browser_config={'prefix': 'admin/', 'list': 'directories'})
        line = reader._directories__line('login.php\n', {'scheme': 'http://', 'host': 'example.com', 'port': 80})

        self.assertEqual(line, 'http://example.com/admin/login.php')

    def test_directories_line_appends_non_default_port(self):
        """Reader._directories__line() should include a non-default port in the final URL."""

        reader = self.create_reader(browser_config={'prefix': '', 'list': 'directories'})
        line = reader._directories__line('login.php\n', {'scheme': 'http://', 'host': 'example.com', 'port': 8080})

        self.assertEqual(line, 'http://example.com:8080/login.php')

    def test_randomize_list_uses_shuf_on_non_windows(self):
        """Reader.randomize_list() should use shuf on non-Windows systems."""

        reader = self.create_reader(browser_config={})

        with patch('src.lib.reader.reader.filesystem.makefile', return_value=self.config['tmplist']) as makefile_mock, \
                patch('src.lib.reader.reader.process.execute') as execute_mock, \
                patch('src.lib.reader.reader.sys') as sys_mock:
            sys_mock.return_value.is_windows = False
            reader.randomize_list('directories', 'tmplist')

        makefile_mock.assert_called_once_with(self.config['tmplist'])
        execute_mock.assert_called_once_with(
            'shuf {0} -o {1}'.format(self.config['directories'], self.config['tmplist'])
        )

    def test_randomize_list_uses_internal_shuffle_on_windows(self):
        """Reader.randomize_list() should use filesystem.shuffle() on Windows."""

        reader = self.create_reader(browser_config={})
        setattr(reader, '_Reader__counter', 15)

        with patch('src.lib.reader.reader.filesystem.makefile', return_value=self.config['tmplist']), \
                patch('src.lib.reader.reader.filesystem.shuffle') as shuffle_mock, \
                patch('src.lib.reader.reader.sys') as sys_mock:
            sys_mock.return_value.is_windows = True
            reader.randomize_list('directories', 'tmplist')

        shuffle_mock.assert_called_once_with(
            target=self.config['directories'],
            output=self.config['tmplist'],
            total=15,
        )

    def test_randomize_list_raises_reader_error(self):
        """Reader.randomize_list() should wrap filesystem and process errors."""

        reader = self.create_reader(browser_config={})

        with patch('src.lib.reader.reader.filesystem.makefile', side_effect=FileSystemError('failed')):
            with self.assertRaises(ReaderError):
                reader.randomize_list('directories', 'tmplist')

    def test_filter_by_extension_writes_only_selected_extensions(self):
        """Reader.filter_by_extension() should keep only matching extensions."""

        reader = self.create_reader(browser_config={})
        output = os.path.join(self.base_dir, 'extensions.txt')
        self.config['extension_output'] = output

        reader.filter_by_extension('directories', 'extension_output', ['php', 'html'])

        with open(output, 'r', encoding='utf-8') as handler:
            lines = handler.read().splitlines()

        self.assertEqual(reader.total_lines, len(lines))
        self.assertTrue(lines)
        self.assertTrue(all(line.endswith(('.php', '.html')) for line in lines))

    def test_filter_by_extension_uses_fast_full_read_path(self):
        """Reader.filter_by_extension() should use the fast in-memory read path."""

        reader = self.create_reader(browser_config={})
        output = os.path.join(self.base_dir, 'extensions.txt')
        self.config['extension_output'] = output

        sample_lines = [
            'admin.php\n',
            'index.html\n',
            'notes.txt\n',
        ]

        with patch('src.lib.reader.reader.filesystem.read', return_value=sample_lines) as read_mock:
            reader.filter_by_extension('directories', 'extension_output', ['php', 'html'])

        read_mock.assert_called_once_with(self.config['directories'])

        with open(output, 'r', encoding='utf-8') as handler:
            lines = handler.read().splitlines()

        self.assertEqual(lines, ['admin.php', 'index.html'])
        self.assertEqual(reader.total_lines, 2)

    def test_filter_by_extension_raises_reader_error(self):
        """Reader.filter_by_extension() should wrap filesystem errors."""

        reader = self.create_reader(browser_config={})
        self.config['extension_output'] = os.path.join(self.base_dir, 'extensions.txt')

        with patch('src.lib.reader.reader.filesystem._resolve_readable_file', side_effect=FileSystemError('failed')):
            with self.assertRaises(ReaderError):
                reader.filter_by_extension('directories', 'extension_output', ['php'])

    def test_filter_by_ignore_extension_writes_excluded_extensions(self):
        """Reader.filter_by_ignore_extension() should remove the selected extensions."""

        reader = self.create_reader(browser_config={})
        output = os.path.join(self.base_dir, 'ignored_extensions.txt')
        self.config['ignored_output'] = output

        reader.filter_by_ignore_extension('directories', 'ignored_output', ['php', 'html'])

        with open(output, 'r', encoding='utf-8') as handler:
            lines = handler.read().splitlines()

        self.assertEqual(reader.total_lines, len(lines))
        self.assertTrue(lines)
        self.assertTrue(all(not line.endswith(('.php', '.html')) for line in lines))

    def test_filter_by_ignore_extension_uses_fast_full_read_path(self):
        """Reader.filter_by_ignore_extension() should use the fast in-memory read path."""

        reader = self.create_reader(browser_config={})
        output = os.path.join(self.base_dir, 'ignored_extensions.txt')
        self.config['ignored_output'] = output

        sample_lines = [
            'admin.php\n',
            'index.html\n',
            'notes.txt\n',
        ]

        with patch('src.lib.reader.reader.filesystem.read', return_value=sample_lines) as read_mock:
            reader.filter_by_ignore_extension('directories', 'ignored_output', ['php', 'html'])

        read_mock.assert_called_once_with(self.config['directories'])

        with open(output, 'r', encoding='utf-8') as handler:
            lines = handler.read().splitlines()

        self.assertEqual(lines, ['notes.txt'])
        self.assertEqual(reader.total_lines, 1)

    def test_filter_by_ignore_extension_raises_reader_error(self):
        """Reader.filter_by_ignore_extension() should wrap filesystem errors."""

        reader = self.create_reader(browser_config={})
        self.config['ignored_output'] = os.path.join(self.base_dir, 'ignored_extensions.txt')

        with patch('src.lib.reader.reader.filesystem._resolve_readable_file', side_effect=FileSystemError('failed')):
            with self.assertRaises(ReaderError):
                reader.filter_by_ignore_extension('directories', 'ignored_output', ['php'])

    def test_count_total_lines_reads_wordlist_once(self):
        """Reader.count_total_lines() should cache the total line count."""

        reader = self.create_reader(browser_config={'list': 'directories'})

        with patch('src.lib.reader.reader.filesystem.count_lines', return_value=15) as count_mock:
            first = reader.count_total_lines()
            second = reader.count_total_lines()

        self.assertEqual(first, 15)
        self.assertEqual(second, 15)
        count_mock.assert_called_once_with(self.config['directories'])

    def test_count_total_lines_uses_external_wordlist(self):
        """Reader.count_total_lines() should count an external wordlist when configured."""

        wordlist = os.path.join(self.base_dir, 'external.dat')
        reader = self.create_reader(
            browser_config={
                'is_external_wordlist': True,
                'wordlist': wordlist,
                'list': 'directories',
            }
        )

        with patch('src.lib.reader.reader.filesystem.count_lines', return_value=3) as count_mock:
            total = reader.count_total_lines()

        self.assertEqual(total, 3)
        count_mock.assert_called_once_with(wordlist)

    def test_count_total_lines_raises_reader_error(self):
        """Reader.count_total_lines() should wrap filesystem errors."""

        reader = self.create_reader(browser_config={'list': 'directories'})

        with patch('src.lib.reader.reader.filesystem.count_lines', side_effect=FileSystemError('failed')):
            with self.assertRaises(ReaderError):
                reader.count_total_lines()

    def test_total_lines_returns_internal_counter(self):
        """Reader.total_lines should expose the cached counter."""

        reader = self.create_reader(browser_config={})
        setattr(reader, '_Reader__counter', 22)

        self.assertEqual(reader.total_lines, 22)

    def test_reader_error_does_not_log_when_wrapping_reader_error(self):
        """ReaderError should not log when it wraps the same ReaderError type."""

        from src.lib.reader.exceptions import ReaderError

        inner = ReaderError('inner boom')

        with patch('src.lib.reader.exceptions.exception.log') as log_mock:
            outer = ReaderError(inner)

        log_mock.assert_not_called()
        self.assertEqual(str(outer), 'ReaderError: str: inner boom')

    def test_reader_error_logs_when_wrapping_foreign_error(self):
        """ReaderError should log when it wraps a non-ReaderError exception."""

        from src.lib.reader.exceptions import ReaderError

        error = ValueError('boom')

        with patch('src.lib.reader.exceptions.exception.log') as log_mock:
            wrapped = ReaderError(error)

        log_mock.assert_called_once_with(class_name='ValueError', message=error)
        self.assertEqual(str(wrapped), 'ValueError: boom')


if __name__ == '__main__':
    unittest.main()