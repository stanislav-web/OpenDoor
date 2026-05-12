# -*- coding: utf-8 -*-

import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from src.core.system.output import Output


class TestOutput(unittest.TestCase):
    """TestOutput class."""

    def tearDown(self):
        Output._Output__is_windows = None
        Output.clear_dynamic_line()

    def test_exit_raises_system_exit(self):
        """Output.exit() should raise SystemExit with the provided message."""

        with self.assertRaises(SystemExit) as context:
            Output.exit('abort')

        self.assertEqual(str(context.exception), 'abort')

    def test_writels_writes_and_flushes(self):
        """Output.writels() should write a plain dynamic line for piped output."""

        fake_stdout = StringIO()
        with patch('src.core.system.output.sys.stdout', fake_stdout):
            Output.writels('message')

        self.assertEqual(fake_stdout.getvalue(), '\rmessage')

    def test_should_keep_ansi_clear_line_only_for_interactive_tty(self):
        """Output.writels() should keep ANSI clear-line only for interactive TTY output."""

        fake_stdout = MagicMock()
        fake_stdout.isatty.return_value = True

        with patch('src.core.system.output.sys.stdout', fake_stdout), \
                patch.dict('src.core.system.output.os.environ', {}, clear=True):
            Output.writels('message')

        fake_stdout.write.assert_called_once_with('\r\x1b[Kmessage')

    def test_should_not_write_ansi_clear_line_when_cli_color_is_disabled(self):
        """Output.writels() should keep log files clean when CLI_COLOR=0."""

        fake_stdout = MagicMock()
        fake_stdout.isatty.return_value = True

        with patch('src.core.system.output.sys.stdout', fake_stdout), \
                patch.dict('src.core.system.output.os.environ', {'CLI_COLOR': '0'}, clear=True):
            Output.writels('message')

        fake_stdout.write.assert_called_once_with('\rmessage')

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

    def test_writels_can_skip_flush(self):
        """Output.writels() should not flush stdout when flush is disabled."""

        fake_stdout = unittest.mock.MagicMock()
        fake_stdout.isatty.return_value = False
        with patch('src.core.system.output.sys.stdout', fake_stdout):
            Output.writels('message', flush=False)

        fake_stdout.write.assert_called_once_with('\rmessage')
        fake_stdout.flush.assert_not_called()

    def test_finish_dynamic_line_should_add_newline_once(self):
        """Output.finish_dynamic_line() should terminate an active rotating line once."""

        fake_stdout = StringIO()

        with patch('src.core.system.output.sys.stdout', fake_stdout):
            Output.mark_dynamic_line(12)
            Output.finish_dynamic_line()
            Output.finish_dynamic_line()

        self.assertEqual(fake_stdout.getvalue(), '\n')

    def test_clear_dynamic_line_should_skip_finish_newline(self):
        """Output.clear_dynamic_line() should suppress later line termination."""

        fake_stdout = StringIO()

        with patch('src.core.system.output.sys.stdout', fake_stdout):
            Output.mark_dynamic_line(12)
            Output.clear_dynamic_line()
            Output.finish_dynamic_line()

        self.assertEqual(fake_stdout.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
