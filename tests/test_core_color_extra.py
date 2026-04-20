# -*- coding: utf-8 -*-

import types
import unittest
from unittest.mock import patch

from src.core.color.color import Color


class _NoTtyStream(object):
    pass


class _FakeStream(object):
    def __init__(self, tty):
        self._tty = tty

    def isatty(self):
        return self._tty


class TestColorExtra(unittest.TestCase):
    """TestColorExtra class."""

    def test_get_returns_default_color_for_unknown_key(self):
        """Color.__get() should return default color when key is unknown."""

        self.assertEqual(getattr(Color, '_Color__get')('red'), 1)
        self.assertEqual(getattr(Color, '_Color__get')('unknown'), 7)

    def test_colored_returns_plain_text_when_stream_has_no_isatty(self):
        """Color.colored() should return plain text if stdout has no isatty()."""

        with patch('src.core.color.color.sys.stdout', _NoTtyStream()):
            self.assertEqual(Color.colored('hello', 'red'), 'hello')

    def test_colored_returns_plain_text_when_stream_is_not_tty(self):
        """Color.colored() should return plain text when stdout is not a TTY."""

        with patch('src.core.color.color.sys.stdout', _FakeStream(False)):
            self.assertEqual(Color.colored('hello', 'red'), 'hello')

    def test_colored_returns_plain_text_when_terminal_has_few_colors(self):
        """Color.colored() should return plain text when curses reports too few colors."""

        fake_curses = types.SimpleNamespace(
            setupterm=lambda: None,
            tigetnum=lambda _name: 1,
        )

        with patch('src.core.color.color.sys.stdout', _FakeStream(True)), \
                patch.dict('sys.modules', {'curses': fake_curses}):
            self.assertEqual(Color.colored('hello', 'red'), 'hello')

    def test_colored_returns_plain_text_when_curses_raises(self):
        """Color.colored() should return plain text when curses probing fails."""

        fake_curses = types.SimpleNamespace(
            setupterm=lambda: (_ for _ in ()).throw(RuntimeError('boom')),
            tigetnum=lambda _name: 256,
        )

        with patch('src.core.color.color.sys.stdout', _FakeStream(True)), \
                patch.dict('sys.modules', {'curses': fake_curses}):
            self.assertEqual(Color.colored('hello', 'red'), 'hello')

    def test_colored_decodes_bytes_and_uses_default_color_for_unknown_name(self):
        """Color.colored() should decode bytes and fall back to default ANSI color."""

        fake_curses = types.SimpleNamespace(
            setupterm=lambda: None,
            tigetnum=lambda _name: 256,
        )

        with patch('src.core.color.color.sys.stdout', _FakeStream(True)), \
                patch.dict('sys.modules', {'curses': fake_curses}):
            actual = Color.colored('hello'.encode('utf-8'), 'unknown')

        self.assertEqual(actual, '\x1b[37mhello\x1b[0m')


if __name__ == '__main__':
    unittest.main()