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

from src.core.filesystem.filesystem import FileSystem
from src.core.filesystem.exceptions import FileSystemError


class TestFileSystem(unittest.TestCase):
    """TestFileSystem class."""

    def setUp(self):
        """Create an isolated temporary workspace for file tests."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name

    def tearDown(self):
        """Cleanup the temporary workspace."""

        self.temp_dir.cleanup()

    def test_is_exist_returns_true_for_existing_file(self):
        """FileSystem.is_exist() should detect an existing file."""

        filename = 'example.txt'
        filepath = os.path.join(self.base_dir, filename)

        with open(filepath, 'w', encoding=FileSystem.text_encoding) as handler:
            handler.write('data')

        self.assertTrue(FileSystem.is_exist(self.base_dir, filename))

    def test_is_exist_returns_false_for_missing_file(self):
        """FileSystem.is_exist() should return False for a missing file."""

        self.assertFalse(FileSystem.is_exist(self.base_dir, 'missing.txt'))

    def test_makedir_creates_nested_directory(self):
        """FileSystem.makedir() should create nested directories."""

        target_dir = os.path.join(self.base_dir, 'reports', 'nested')
        created_dir = FileSystem.makedir(target_dir)

        self.assertTrue(os.path.isdir(created_dir))

    def test_getabsname_returns_absolute_path(self):
        """FileSystem.getabsname() should normalize to an absolute path."""

        relative_path = os.path.join('tests', 'data', 'directories.dat')
        absolute_path = FileSystem.getabsname(relative_path)

        self.assertTrue(os.path.isabs(absolute_path))
        self.assertTrue(absolute_path.endswith(relative_path))

    def test_get_extension_returns_extension(self):
        """FileSystem.get_extension() should return the file extension."""

        self.assertEqual(FileSystem.get_extension('archive.tar.gz'), '.gz')

    def test_has_extension_returns_true_for_paths_with_extension(self):
        """FileSystem.has_extension() should detect an extension."""

        self.assertTrue(FileSystem.has_extension('report.json'))

    def test_has_extension_returns_false_for_paths_without_extension(self):
        """FileSystem.has_extension() should return False when extension is absent."""

        self.assertFalse(FileSystem.has_extension('admin/login'))

    def test_filter_file_lines_filters_by_pattern(self):
        """FileSystem.filter_file_lines() should filter lines by regex pattern."""

        lines = ['index.php', 'index.html', 'assets/', 'main.js']
        filtered = FileSystem.filter_file_lines(lines, r'.*\.(php|html)$')

        self.assertEqual(filtered, ['index.php', 'index.html'])

    def test_clear_removes_only_matching_extension(self):
        """FileSystem.clear() should delete only files matching the requested extension."""

        removable = os.path.join(self.base_dir, 'remove.tmp')
        preserved = os.path.join(self.base_dir, 'keep.log')

        for path in [removable, preserved]:
            with open(path, 'w', encoding=FileSystem.text_encoding) as handler:
                handler.write('payload')

        FileSystem.clear(self.base_dir, '.tmp')

        self.assertFalse(os.path.exists(removable))
        self.assertTrue(os.path.exists(preserved))

    def test_clear_raises_for_missing_directory(self):
        """FileSystem.clear() should fail for a missing directory."""

        with self.assertRaises(FileSystemError):
            FileSystem.clear(os.path.join(self.base_dir, 'missing'), '.tmp')

    def test_makefile_creates_file_in_nested_directory(self):
        """FileSystem.makefile() should create a file and parent directories."""

        filepath = os.path.join(self.base_dir, 'nested', 'report.txt')
        result = FileSystem.makefile(filepath)

        self.assertEqual(result, filepath)
        self.assertTrue(os.path.isfile(result))

    def test_makefile_returns_existing_file_path(self):
        """FileSystem.makefile() should return the same path for an existing file."""

        filepath = os.path.join(self.base_dir, 'existing.txt')
        with open(filepath, 'w', encoding=FileSystem.text_encoding) as handler:
            handler.write('ok')

        self.assertEqual(FileSystem.makefile(filepath), filepath)

    def test_shuffle_preserves_all_lines(self):
        """FileSystem.shuffle() should write the same lines in shuffled order."""

        source = os.path.join(self.base_dir, 'source.txt')
        output = os.path.join(self.base_dir, 'output.txt')
        lines = ['first\n', 'second\n', 'third\n', 'fourth\n']

        with open(source, 'w', encoding=FileSystem.text_encoding) as handler:
            handler.writelines(lines)

        with patch('src.core.filesystem.filesystem.random.shuffle', side_effect=lambda seq: seq.reverse()):
            FileSystem.shuffle(source, output, total=2)

        with open(output, 'r', encoding=FileSystem.text_encoding) as handler:
            shuffled = handler.readlines()

        self.assertEqual(shuffled, ['fourth\n', 'third\n', 'second\n', 'first\n'])

    def test_readline_passes_transformed_lines_to_loader(self):
        """FileSystem.readline() should transform each line before loading."""

        source = os.path.join(self.base_dir, 'lines.txt')
        with open(source, 'w', encoding=FileSystem.text_encoding) as handler:
            handler.write('alpha\nbeta\n')

        loaded = []

        def handler(line, params):
            return '{0}:{1}'.format(params['prefix'], line.strip())

        def loader(lines):
            loaded.extend(lines)

        FileSystem.readline(source, handler=handler, handler_params={'prefix': 'item'}, loader=loader)

        self.assertEqual(loaded, ['item:alpha', 'item:beta'])

    def test_readline_raises_for_missing_file(self):
        """FileSystem.readline() should raise for a missing file."""

        with self.assertRaises(FileSystemError):
            FileSystem.readline(
                os.path.join(self.base_dir, 'missing.txt'),
                handler=lambda line, params: line,
                handler_params={},
                loader=lambda lines: lines,
            )

    def test_read_returns_file_lines(self):
        """FileSystem.read() should return file lines."""

        source = os.path.join(self.base_dir, 'read.txt')
        with open(source, 'w', encoding=FileSystem.text_encoding) as handler:
            handler.write('one\ntwo\n')

        self.assertEqual(FileSystem.read(source), ['one\n', 'two\n'])

    def test_read_raises_for_missing_file(self):
        """FileSystem.read() should raise for a missing file."""

        with self.assertRaises(FileSystemError):
            FileSystem.read(os.path.join(self.base_dir, 'missing.txt'))

    def test_count_lines_returns_total_number_of_lines(self):
        """FileSystem.count_lines() should count lines in a file."""

        source = os.path.join(self.base_dir, 'count.txt')
        with open(source, 'w', encoding=FileSystem.text_encoding) as handler:
            handler.write('one\ntwo\nthree\n')

        self.assertEqual(FileSystem.count_lines(source), 3)

    def test_count_lines_raises_for_missing_file(self):
        """FileSystem.count_lines() should raise for a missing file."""

        with self.assertRaises(FileSystemError):
            FileSystem.count_lines(os.path.join(self.base_dir, 'missing.txt'))

    def test_readcfg_returns_parser_for_valid_cfg(self):
        """FileSystem.readcfg() should parse a valid cfg file."""

        current_dir = os.getcwd()
        config_path = os.path.join('tests', 'data', 'setup.cfg')

        class FakeMatch(object):
            """Simple regex match stub used to stabilize readcfg() path detection."""

            def group(self):
                return current_dir + os.sep

        try:
            with patch('src.core.filesystem.filesystem.re.search', return_value=FakeMatch()):
                config = FileSystem.readcfg(config_path)
        finally:
            os.chdir(current_dir)

        self.assertEqual(config.get('opendoor', 'directories'), 'tests/data/directories.dat')

    def test_readcfg_raises_for_missing_cfg(self):
        """FileSystem.readcfg() should raise for a missing config file."""

        current_dir = os.getcwd()
        try:
            with self.assertRaises(FileSystemError):
                FileSystem.readcfg(os.path.join('tests', 'data', 'missing.cfg'))
        finally:
            os.chdir(current_dir)

    def test_readcfg_raises_for_invalid_cfg(self):
        """FileSystem.readcfg() should raise for an invalid config file."""

        invalid_cfg = os.path.join(self.base_dir, 'invalid.cfg')
        with open(invalid_cfg, 'w', encoding=FileSystem.text_encoding) as handler:
            handler.write('[section\ninvalid')

        current_dir = os.getcwd()
        try:
            with self.assertRaises(FileSystemError):
                FileSystem.readcfg(invalid_cfg)
        finally:
            os.chdir(current_dir)

    def test_writelist_writes_joined_data(self):
        """FileSystem.writelist() should write list items with a separator."""

        target = os.path.join(self.base_dir, 'output.txt')
        FileSystem.makefile(target)
        FileSystem.writelist(target, ['one', 'two', 'three'], '\n')

        with open(target, 'r', encoding=FileSystem.text_encoding) as handler:
            self.assertEqual(handler.read(), 'one\ntwo\nthree')

    def test_writelist_raises_when_directory_is_missing(self):
        """FileSystem.writelist() should raise when parent directory is missing."""

        with self.assertRaises(FileSystemError):
            FileSystem.writelist(os.path.join(self.base_dir, 'missing', 'output.txt'), ['one'])

    def test_human_size_formats_bytes(self):
        """FileSystem.human_size() should format bytes to a readable string."""

        self.assertEqual(FileSystem.human_size(512), '512.00B')
        self.assertEqual(FileSystem.human_size(2048), '2.00KB')


if __name__ == '__main__':
    unittest.main()