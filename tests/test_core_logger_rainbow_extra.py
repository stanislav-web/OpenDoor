# -*- coding: utf-8 -*-

import logging
import unittest
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from src.core.logger.rainbow import RainbowLoggingHandler


class _TtyStream(StringIO):
    def isatty(self):
        return True


class _PlainStream(StringIO):
    def isatty(self):
        return False


class TestRainbowLoggingHandlerExtra(unittest.TestCase):
    """TestRainbowLoggingHandlerExtra class."""

    def make_record(self, level=logging.INFO, message='hello', func_name='scan'):
        """Create a logging record for formatter tests."""

        record = logging.LogRecord(
            name='test',
            level=level,
            pathname=__file__,
            lineno=10,
            msg=message,
            args=(),
            exc_info=None,
            func=func_name,
        )
        return record

    def test_get_color_supports_missing_fg_and_bold(self):
        """RainbowLoggingHandler.get_color() should handle empty and bold color params."""

        handler = RainbowLoggingHandler(_PlainStream())

        self.assertEqual(handler.get_color(), '\x1b[m')
        self.assertEqual(handler.get_color('red', True), '\x1b[31;1m')

    def test_pure_line_len_removes_ansi_sequences(self):
        """RainbowLoggingHandler.__pure_line_len() should ignore ANSI escapes."""

        actual = getattr(RainbowLoggingHandler, '_RainbowLoggingHandler__pure_line_len')('\x1b[31mhello\x1b[0m')
        self.assertEqual(actual, 5)

    def test_colorize_truncates_non_error_messages_to_terminal_width(self):
        """RainbowLoggingHandler.colorize() should truncate long non-error messages."""

        handler = RainbowLoggingHandler(_TtyStream())
        record = self.make_record(level=logging.INFO, message='X' * 200, func_name='scan')

        with patch('src.core.logger.rainbow.Term', SimpleNamespace(terminal_size={'width': 40})):
            actual = handler.colorize(record)

        self.assertIn('...', actual)

    def test_colorize_does_not_truncate_error_messages(self):
        """RainbowLoggingHandler.colorize() should not truncate long error messages."""

        handler = RainbowLoggingHandler(_TtyStream())
        record = self.make_record(level=logging.ERROR, message='Y' * 200, func_name='scan')

        with patch('src.core.logger.rainbow.Term', SimpleNamespace(terminal_size={'width': 40})):
            actual = handler.colorize(record)

        self.assertNotIn('...', actual)

    def test_colorize_handles_missing_levelno(self):
        """RainbowLoggingHandler.colorize() should default to INFO when levelno is missing."""

        handler = RainbowLoggingHandler(_TtyStream())
        record = self.make_record(level=logging.INFO, message='hello', func_name='scan')
        del record.levelno

        with patch('src.core.logger.rainbow.Term', SimpleNamespace(terminal_size={'width': 120})):
            actual = handler.colorize(record)

        self.assertIn('hello', actual)

    def test_format_uses_plain_stream_handler_path_when_not_tty(self):
        """RainbowLoggingHandler.format() should use plain formatting on non-TTY streams."""

        handler = RainbowLoggingHandler(_PlainStream())
        handler.setFormatter(logging.Formatter('%(message)s'))
        record = self.make_record(level=logging.INFO, message='plain', func_name='scan')

        actual = handler.format(record)

        self.assertEqual(actual, 'plain')

    def test_format_uses_colorized_path_when_stream_is_tty(self):
        """RainbowLoggingHandler.format() should colorize records on TTY streams."""

        handler = RainbowLoggingHandler(_TtyStream())
        record = self.make_record(level=logging.INFO, message='tty-message', func_name='scan')

        with patch('src.core.logger.rainbow.Term', SimpleNamespace(terminal_size={'width': 120})):
            actual = handler.format(record)

        self.assertIn('tty-message', actual)
        self.assertIn('\x1b[', actual)

    def test_colorize_keeps_debug_messages_untruncated(self):
        """RainbowLoggingHandler.colorize() should not truncate DEBUG messages."""

        handler = RainbowLoggingHandler(_TtyStream())
        record = self.make_record(level=logging.DEBUG, message='D' * 80, func_name='scan')

        with patch('src.core.logger.rainbow.Term', SimpleNamespace(terminal_size={'width': 40})):
            actual = handler.colorize(record)

        self.assertIn('D' * 80, actual)


class TestRainbowLoggingHandlerPaddingCoverage(unittest.TestCase):
    """Final branch coverage for RainbowLoggingHandler padding."""

    def test_colorize_does_not_pad_long_function_names(self):
        """RainbowLoggingHandler.colorize() should avoid extra padding for long function names."""

        handler = RainbowLoggingHandler(_TtyStream())
        record = TestRainbowLoggingHandlerExtra().make_record(
            level=logging.INFO,
            message='hello',
            func_name='function_name_longer_than_padding',
        )

        with patch('src.core.logger.rainbow.Term', SimpleNamespace(terminal_size={'width': 120})):
            actual = handler.colorize(record)

        self.assertIn('function_name_longer_than_padding', actual)
        self.assertIn('hello', actual)
