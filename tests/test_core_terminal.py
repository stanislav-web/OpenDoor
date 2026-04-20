# -*- coding: utf-8 -*-

import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core.system.terminal import Terminal


class TestTerminal(unittest.TestCase):
    """TestTerminal class."""

    def test_get_ts_uses_unix_provider(self):
        """Terminal.get_ts() should use the Unix provider on Unix platforms."""

        with patch('src.core.system.terminal.platform.system', return_value='Linux'), \
                patch.object(Terminal, '_Terminal__get_ts_unix', return_value=(120, 40)) as unix_mock:
            self.assertEqual(Terminal().get_ts(), (120, 40))

        unix_mock.assert_called_once_with()

    def test_get_ts_uses_windows_provider(self):
        """Terminal.get_ts() should use the Windows provider on Windows."""

        with patch('src.core.system.terminal.platform.system', return_value='Windows'), \
                patch.object(Terminal, '_Terminal__get_ts_windows', return_value=(100, 30)) as win_mock:
            self.assertEqual(Terminal().get_ts(), (100, 30))

        win_mock.assert_called_once_with()

    def test_get_ts_falls_back_when_windows_provider_returns_none(self):
        """Terminal.get_ts() should fall back to tput and generic fallback on Windows."""

        with patch('src.core.system.terminal.platform.system', return_value='Windows'), \
                patch.object(Terminal, '_Terminal__get_ts_windows', return_value=None), \
                patch.object(Terminal, '_Terminal__get_ts_tput', return_value=None), \
                patch.object(Terminal, '_Terminal__get_ts_fallback', return_value=(80, 25)) as fallback_mock:
            self.assertEqual(Terminal().get_ts(), (80, 25))

        fallback_mock.assert_called_once_with()

    def test_get_ts_unix_parses_stty_output(self):
        """Terminal.__get_ts_unix() should parse stty output into width and height."""

        with patch('src.core.system.terminal.subprocess.check_output', return_value=b'24 120\n') as output_mock:
            actual = getattr(Terminal, '_Terminal__get_ts_unix')()

        self.assertEqual(actual, (120, 24))
        output_mock.assert_called_once()

    def test_get_ts_unix_uses_legacy_call_after_check_output_failure(self):
        """Terminal.__get_ts_unix() should try the legacy helper when check_output fails."""

        with patch('src.core.system.terminal.subprocess.check_output', side_effect=AttributeError('no api')), \
                patch.object(Terminal, '_Terminal__legacy_call', return_value=b'30 90') as legacy_mock:
            actual = getattr(Terminal, '_Terminal__get_ts_unix')()

        self.assertEqual(actual, (90, 30))
        legacy_mock.assert_called_once_with(['stty', 'size'])

    def test_get_ts_unix_returns_none_for_invalid_output(self):
        """Terminal.__get_ts_unix() should return None for invalid output."""

        with patch('src.core.system.terminal.subprocess.check_output', return_value=b'invalid'):
            self.assertIsNone(getattr(Terminal, '_Terminal__get_ts_unix')())

    def test_legacy_call_returns_stdout(self):
        """Terminal.__legacy_call() should return stdout for successful commands."""

        process = MagicMock()
        process.communicate.return_value = (b'24 80', b'')
        process.poll.return_value = 0

        with patch('src.core.system.terminal.subprocess.Popen', return_value=process):
            self.assertEqual(getattr(Terminal, '_Terminal__legacy_call')(['stty', 'size']), b'24 80')

    def test_legacy_call_raises_for_non_zero_return_code(self):
        """Terminal.__legacy_call() should raise CalledProcessError on command failure."""

        process = MagicMock()
        process.communicate.return_value = (b'', b'error')
        process.poll.return_value = 1

        with patch('src.core.system.terminal.subprocess.Popen', return_value=process):
            with self.assertRaises(subprocess.CalledProcessError):
                getattr(Terminal, '_Terminal__legacy_call')(['stty', 'size'])

    def test_get_ts_tput_parses_columns_and_rows(self):
        """Terminal.__get_ts_tput() should parse tput output."""

        with patch('src.core.system.terminal.subprocess.check_output', side_effect=[b'120\n', b'40\n']):
            self.assertEqual(getattr(Terminal, '_Terminal__get_ts_tput')(), (120, 40))

    def test_get_ts_fallback_uses_shutil_terminal_size(self):
        """Terminal.__get_ts_fallback() should use shutil.get_terminal_size()."""

        with patch('src.core.system.terminal.shutil.get_terminal_size', return_value=SimpleNamespace(columns=101, lines=33)):
            self.assertEqual(getattr(Terminal, '_Terminal__get_ts_fallback')(), (101, 33))


if __name__ == '__main__':
    unittest.main()