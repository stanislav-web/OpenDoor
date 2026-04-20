# -*- coding: utf-8 -*-

import struct
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.core.system.terminal import Terminal


class TestTerminalWindowsExtra(unittest.TestCase):
    """TestTerminalWindowsExtra class."""

    def test_get_ts_windows_parses_console_buffer_info(self):
        """Terminal.__get_ts_windows() should parse Windows console buffer info."""

        packed = struct.pack(
            "hhhhHhhhhhh",
            120,   # bufx
            30,    # bufy
            0,     # curx
            0,     # cury
            0,     # wattr
            0,     # left
            0,     # top
            119,   # right
            29,    # bottom
            0,     # maxx
            0,     # maxy
        )
        fake_buffer = SimpleNamespace(raw=packed)
        fake_kernel32 = SimpleNamespace(
            GetStdHandle=lambda _handle: 1,
            GetConsoleScreenBufferInfo=lambda _handle, _buffer: 1,
        )
        fake_windll = SimpleNamespace(kernel32=fake_kernel32)

        with patch('ctypes.windll', fake_windll, create=True), \
                patch('ctypes.create_string_buffer', return_value=fake_buffer, create=True):
            actual = getattr(Terminal, '_Terminal__get_ts_windows')()

        self.assertEqual(actual, (120, 30))

    def test_get_ts_windows_returns_defaults_when_console_info_is_unavailable(self):
        """Terminal.__get_ts_windows() should fall back to default size when console info is unavailable."""

        fake_buffer = SimpleNamespace(raw=b'\x00' * 22)
        fake_kernel32 = SimpleNamespace(
            GetStdHandle=lambda _handle: 1,
            GetConsoleScreenBufferInfo=lambda _handle, _buffer: 0,
        )
        fake_windll = SimpleNamespace(kernel32=fake_kernel32)

        with patch('ctypes.windll', fake_windll, create=True), \
                patch('ctypes.create_string_buffer', return_value=fake_buffer, create=True):
            actual = getattr(Terminal, '_Terminal__get_ts_windows')()

        self.assertEqual(actual, (Terminal.DEFAULT_WIDTH, Terminal.DEFAULT_HEIGHT))

    def test_get_ts_windows_returns_none_on_exception(self):
        """Terminal.__get_ts_windows() should return None when Windows APIs are unavailable."""

        with patch('ctypes.create_string_buffer', side_effect=Exception('boom'), create=True):
            self.assertIsNone(getattr(Terminal, '_Terminal__get_ts_windows')())


if __name__ == '__main__':
    unittest.main()