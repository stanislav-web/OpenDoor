# -*- coding: utf-8 -*-

import unittest
from io import StringIO
from unittest.mock import patch

from src.core.system.output import Output


class TestOutput(unittest.TestCase):
    """TestOutput class."""

    def tearDown(self):
        Output._Output__is_windows = None

    def test_exit_raises_system_exit(self):
        """Output.exit() should raise SystemExit with the provided message."""

        with self.assertRaises(SystemExit) as context:
            Output.exit('abort')

        self.assertEqual(str(context.exception), 'abort')

    def test_writels_writes_and_flushes(self):
        """Output.writels() should write a dynamic line and flush by default."""

        fake_stdout = StringIO()
        with patch('src.core.system.output.sys.stdout', fake_stdout):
            Output.writels('message')

        self.assertEqual(fake_stdout.getvalue(), '\r\x1b[Kmessage')

    def test_writeln_writes_line_break(self):
        """Output.writeln() should append a trailing newline."""

        fake_stdout = StringIO()
        with patch('src.core.system.output.sys.stdout', fake_stdout):
            Output.writeln('message')

        self.assertEqual(fake_stdout.getvalue(), 'message\n')

    def test_version_returns_major_minor_only(self):
        """Output.version() should return only major.minor."""

        with patch('src.core.system.output.platform.python_version', return_value='3.14.2'):
            self.assertEqual(Output.version(), '3.14')

    def test_is_windows_is_cached(self):
        """Output.is_windows should cache the platform detection result."""

        output = Output()
        with patch('src.core.system.output.sys.platform', 'win32'), \
                patch('src.core.system.output.os.name', 'nt'):
            self.assertTrue(output.is_windows)

        with patch('src.core.system.output.sys.platform', 'linux'), \
                patch('src.core.system.output.os.name', 'posix'):
            self.assertTrue(output.is_windows)


if __name__ == '__main__':
    unittest.main()