# -*- coding: utf-8 -*-

import errno
import os
import tempfile
import unittest
from configparser import ParsingError
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.filesystem.exceptions import FileSystemError
from src.core.filesystem.filesystem import FileSystem


class TestFileSystemExtra(unittest.TestCase):
    """TestFileSystemExtra class."""

    def test_iter_file_candidates_absolute_and_deduplicated(self):
        """_iter_file_candidates() should preserve absolute paths and deduplicate results."""

        absolute = '/tmp/example.txt'
        self.assertEqual(FileSystem._iter_file_candidates(absolute), [absolute])

        with patch.object(FileSystem, '_project_root', return_value='/repo'), \
                patch('src.core.filesystem.filesystem.os.path.expanduser', return_value='/home/user'):
            candidates = FileSystem._iter_file_candidates(
                'data.txt',
                include_home=True,
                include_project_root=True,
            )

        self.assertEqual(
            candidates,
            [
                os.path.abspath('data.txt'),
                os.path.abspath('/repo/data.txt'),
                os.path.abspath('/home/user/data.txt'),
            ],
        )

    def test_resolve_readable_file_raises_for_unreadable_existing_file(self):
        """_resolve_readable_file() should fail when an existing candidate is not readable."""

        with patch.object(FileSystem, '_iter_file_candidates', return_value=['/tmp/test.txt']), \
                patch('src.core.filesystem.filesystem.os.path.isfile', return_value=True), \
                patch('src.core.filesystem.filesystem.os.access', return_value=False):
            with self.assertRaises(FileSystemError):
                FileSystem._resolve_readable_file('test.txt')

    def test_resolve_readable_file_raises_when_no_candidates_exist(self):
        """_resolve_readable_file() should fail when no candidate file exists."""

        with patch.object(FileSystem, '_iter_file_candidates', return_value=['/tmp/missing.txt']), \
                patch('src.core.filesystem.filesystem.os.path.isfile', return_value=False):
            with self.assertRaises(FileSystemError):
                FileSystem._resolve_readable_file('missing.txt')

    def test_resolve_writable_file_raises_for_missing_and_non_writable_files(self):
        """_resolve_writable_file() should reject missing and non-writable files."""

        with patch('src.core.filesystem.filesystem.os.path.isfile', return_value=False):
            with self.assertRaises(FileSystemError):
                FileSystem._resolve_writable_file('missing.txt')

        with patch('src.core.filesystem.filesystem.os.path.isfile', return_value=True), \
                patch('src.core.filesystem.filesystem.os.access', return_value=False):
            with self.assertRaises(FileSystemError):
                FileSystem._resolve_writable_file('locked.txt')

    def test_is_exist_true_branch(self):
        """is_exist() should return True when the target exists."""

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / 'exists.txt'
            target.write_text('ok', encoding='utf-8')

            self.assertTrue(FileSystem.is_exist(temp_dir, 'exists.txt'))

    def test_makedir_uses_home_fallback_when_first_candidate_is_not_writable(self):
        """makedir() should fall back to a home-based candidate when needed."""

        target = 'reports'
        home_target = os.path.join('/home/user', target)

        def fake_makedirs(path, mode=0o777, exist_ok=True):
            return None

        def fake_access(path, mode):
            if path == target:
                return False
            if path == home_target:
                return True
            return False

        with patch('src.core.filesystem.filesystem.os.path.isabs', return_value=False), \
                patch('src.core.filesystem.filesystem.os.path.expanduser', return_value='/home/user'), \
                patch('src.core.filesystem.filesystem.os.makedirs', side_effect=fake_makedirs), \
                patch('src.core.filesystem.filesystem.os.access', side_effect=fake_access):
            actual = FileSystem.makedir(target)

        self.assertEqual(actual, home_target)

    def test_makedir_raises_when_all_candidates_fail(self):
        """makedir() should raise FileSystemError when all candidates fail."""

        error = OSError(errno.EACCES, 'denied')

        with patch('src.core.filesystem.filesystem.os.path.isabs', return_value=False), \
                patch('src.core.filesystem.filesystem.os.path.expanduser', return_value='/home/user'), \
                patch('src.core.filesystem.filesystem.os.makedirs', side_effect=error), \
                patch('src.core.filesystem.filesystem.os.access', return_value=False):
            with self.assertRaises(FileSystemError):
                FileSystem.makedir('reports')

    def test_clear_raises_for_missing_directory(self):
        """clear() should reject non-existing directories."""

        with self.assertRaises(FileSystemError):
            FileSystem.clear('/path/does/not/exist', '.txt')

    def test_makefile_returns_existing_readable_path(self):
        """makefile() should return the existing path if the file already exists and is readable."""

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / 'sample.txt'
            target.write_text('ok', encoding='utf-8')

            actual = FileSystem.makefile(str(target))
            self.assertEqual(actual, str(target))

    def test_shuffle_wraps_io_errors(self):
        """shuffle() should wrap file I/O errors."""

        with patch('builtins.open', side_effect=IOError('boom')):
            with self.assertRaises(FileSystemError):
                FileSystem.shuffle('input.txt', 'output.txt', 10)

    def test_readcfg_wraps_parsing_errors(self):
        """readcfg() should wrap parsing errors."""

        parser_mock = MagicMock()
        parser_mock.read.side_effect = ParsingError('broken.cfg')

        with patch.object(FileSystem, '_resolve_readable_file', return_value='broken.cfg'), \
                patch('src.core.filesystem.filesystem.RawConfigParser', return_value=parser_mock):
            with self.assertRaises(FileSystemError):
                FileSystem.readcfg('broken.cfg')

    def test_writelist_uses_resolved_file_path(self):
        """writelist() should write joined data to the resolved writable file."""

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / 'out.txt'
            target.write_text('', encoding='utf-8')

            FileSystem.writelist(str(target), ['a', 'b', 'c'], separator='|')

            self.assertEqual(target.read_text(encoding='utf-8'), 'a|b|c')


if __name__ == '__main__':
    unittest.main()