# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.filesystem.filesystem import FileSystem


class TestFileSystemStreaming(unittest.TestCase):
    """TestFileSystemStreaming class."""

    def setUp(self):
        """Create an isolated temporary directory."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name

    def tearDown(self):
        """Cleanup temporary resources."""

        self.temp_dir.cleanup()

    def test_readline_sends_data_in_batches(self):
        """FileSystem.readline() should stream lines to loader in batches."""

        source = os.path.join(self.base_dir, 'lines.txt')
        with open(source, 'w', encoding=FileSystem.text_encoding) as handler:
            handler.write('one\n')
            handler.write('two\n')
            handler.write('three\n')
            handler.write('four\n')
            handler.write('five\n')

        received_batches = []

        def line_handler(line, _params):
            return line.strip()

        def loader(items):
            received_batches.append(list(items))

        with patch.object(FileSystem, 'READLINE_BATCH_SIZE', 2):
            FileSystem.readline(source, handler=line_handler, handler_params={}, loader=loader)

        self.assertEqual(
            received_batches,
            [['one', 'two'], ['three', 'four'], ['five']]
        )

    def test_readline_calls_loader_once_for_empty_file(self):
        """FileSystem.readline() should still call loader once for empty files."""

        source = os.path.join(self.base_dir, 'empty.txt')
        with open(source, 'w', encoding=FileSystem.text_encoding):
            pass

        received_batches = []

        def loader(items):
            received_batches.append(list(items))

        with patch.object(FileSystem, 'READLINE_BATCH_SIZE', 2):
            FileSystem.readline(
                source,
                handler=lambda line, _params: line,
                handler_params={},
                loader=loader,
            )

        self.assertEqual(received_batches, [[]])


if __name__ == '__main__':
    unittest.main()