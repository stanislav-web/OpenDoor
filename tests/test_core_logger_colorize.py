# -*- coding: utf-8 -*-

import importlib.util
import logging
import types
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.logger.colorize import ColorizingStreamHandler


class FakeStream(StringIO):
    def __init__(self, tty=False):
        super().__init__()
        self._tty = tty
        self.flushed = False

    def isatty(self):
        return self._tty

    def flush(self):
        self.flushed = True
        super().flush()


class TestColorizingStreamHandler(unittest.TestCase):
    """TestColorizingStreamHandler class."""

    def test_is_tty_uses_stream_method(self):
        """ColorizingStreamHandler.is_tty should delegate to stream.isatty()."""

        handler = ColorizingStreamHandler(FakeStream(tty=True))
        self.assertTrue(handler.is_tty)

        handler = ColorizingStreamHandler(FakeStream(tty=False))
        self.assertFalse(handler.is_tty)

    def test_emit_writes_plain_message_when_not_tty(self):
        """ColorizingStreamHandler.emit() should write plain text for non-tty streams."""

        stream = FakeStream(tty=False)
        handler = ColorizingStreamHandler(stream)
        handler.setFormatter(logging.Formatter('%(message)s'))
        record = logging.LogRecord('x', logging.INFO, __file__, 1, 'hello', (), None)

        handler.emit(record)

        self.assertEqual(stream.getvalue(), 'hello\n')
        self.assertTrue(stream.flushed)

    def test_emit_uses_output_colorized_when_tty(self):
        """ColorizingStreamHandler.emit() should delegate to output_colorized() for tty streams."""

        stream = FakeStream(tty=True)
        handler = ColorizingStreamHandler(stream)
        handler.setFormatter(logging.Formatter('%(message)s'))
        record = logging.LogRecord('x', logging.INFO, __file__, 1, 'hello', (), None)

        with patch.object(handler, 'output_colorized') as colorized_mock:
            handler.emit(record)

        colorized_mock.assert_called_once_with('hello')
        self.assertEqual(stream.getvalue(), '\n')

    def test_emit_delegates_errors_to_handle_error(self):
        """ColorizingStreamHandler.emit() should forward unexpected errors to handleError()."""

        stream = FakeStream(tty=False)
        handler = ColorizingStreamHandler(stream)
        record = logging.LogRecord('x', logging.INFO, __file__, 1, 'hello', (), None)

        with patch.object(handler, 'format', side_effect=ValueError('broken')), \
                patch.object(handler, 'handleError') as error_mock:
            handler.emit(record)

        error_mock.assert_called_once_with(record)
        self.assertEqual(str(record.msg), 'broken')

    def test_emit_reraises_keyboard_interrupt(self):
        """ColorizingStreamHandler.emit() should re-raise KeyboardInterrupt."""

        stream = FakeStream(tty=False)
        handler = ColorizingStreamHandler(stream)
        record = logging.LogRecord('x', logging.INFO, __file__, 1, 'hello', (), None)

        with patch.object(handler, 'format', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                handler.emit(record)

    def test_output_colorized_writes_message_on_posix(self):
        """ColorizingStreamHandler.output_colorized() should write the message directly on non-Windows."""

        stream = FakeStream(tty=True)
        handler = ColorizingStreamHandler(stream)

        handler.output_colorized('abc')

        self.assertEqual(stream.getvalue(), 'abc')

    def test_windows_output_colorized_branch_can_be_loaded(self):
        """ColorizingStreamHandler Windows-specific output branch should be importable and callable."""

        path = Path(__file__).resolve().parents[1] / 'src' / 'core' / 'logger' / 'colorize.py'
        spec = importlib.util.spec_from_file_location('colorize_win_test', path)
        module = importlib.util.module_from_spec(spec)

        with patch('os.name', 'nt'):
            spec.loader.exec_module(module)

        stream = MagicMock()
        stream.write = MagicMock()
        stream.fileno = MagicMock(return_value=1)

        fake_kernel32 = MagicMock()
        fake_kernel32.GetStdHandle.return_value = 10
        fake_kernel32.SetConsoleTextAttribute = MagicMock()
        module.ctypes.windll = types.SimpleNamespace(kernel32=fake_kernel32)

        handler = module.ColorizingStreamHandler(stream)
        handler.output_colorized('\x1b[31mRED\x1b[0m')

        stream.write.assert_called_with('RED')
        self.assertTrue(fake_kernel32.SetConsoleTextAttribute.called)

    def test_windows_output_colorized_handles_background_intensity_reset_and_unknown_codes(self):
        """Windows output_colorized() should cover background, intensity, reset and ignored ANSI params."""

        path = Path(__file__).resolve().parents[1] / 'src' / 'core' / 'logger' / 'colorize.py'
        spec = importlib.util.spec_from_file_location('colorize_win_cov_test', path)
        module = importlib.util.module_from_spec(spec)

        with patch('os.name', 'nt'):
            spec.loader.exec_module(module)

        stream = MagicMock()
        stream.write = MagicMock()
        stream.fileno = MagicMock(return_value=1)

        fake_kernel32 = MagicMock()
        fake_kernel32.GetStdHandle.return_value = 10
        fake_kernel32.SetConsoleTextAttribute = MagicMock()
        module.ctypes.windll = types.SimpleNamespace(kernel32=fake_kernel32)

        handler = module.ColorizingStreamHandler(stream)
        handler.output_colorized('\x1b[41;32;1;0;99mX')

        stream.write.assert_called_with('X')
        self.assertTrue(fake_kernel32.GetStdHandle.called)
        self.assertTrue(fake_kernel32.SetConsoleTextAttribute.called)

    def test_windows_output_colorized_skips_console_api_for_non_std_fileno(self):
        """Windows output_colorized() should skip console color API when fileno is not stdout/stderr."""

        path = Path(__file__).resolve().parents[1] / 'src' / 'core' / 'logger' / 'colorize.py'
        spec = importlib.util.spec_from_file_location('colorize_win_cov_test_fd', path)
        module = importlib.util.module_from_spec(spec)

        with patch('os.name', 'nt'):
            spec.loader.exec_module(module)

        stream = MagicMock()
        stream.write = MagicMock()
        stream.fileno = MagicMock(return_value=9)

        fake_kernel32 = MagicMock()
        fake_kernel32.GetStdHandle.return_value = 10
        fake_kernel32.SetConsoleTextAttribute = MagicMock()
        module.ctypes.windll = types.SimpleNamespace(kernel32=fake_kernel32)

        handler = module.ColorizingStreamHandler(stream)
        handler.output_colorized('\x1b[31mRED\x1b[0m')

        stream.write.assert_called_with('RED')
        fake_kernel32.GetStdHandle.assert_not_called()
        fake_kernel32.SetConsoleTextAttribute.assert_not_called()

if __name__ == '__main__':
    unittest.main()