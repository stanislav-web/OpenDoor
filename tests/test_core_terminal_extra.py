# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from src.core.system.terminal import Terminal


class TestTerminalExtra(unittest.TestCase):
    """TestTerminalExtra class."""

    def test_get_ts_unknown_platform_uses_fallback(self):
        """Terminal.get_ts() should use the generic fallback on unknown platforms."""

        with patch('src.core.system.terminal.platform.system', return_value='AmigaOS'), \
                patch.object(Terminal, '_Terminal__get_ts_fallback', return_value=(90, 40)) as fallback_mock:
            self.assertEqual(Terminal().get_ts(), (90, 40))

        fallback_mock.assert_called_once_with()

    def test_get_ts_windows_tries_tput_when_windows_probe_fails(self):
        """Terminal.get_ts() should try tput after Windows-specific detection fails."""

        with patch('src.core.system.terminal.platform.system', return_value='Windows'), \
                patch.object(Terminal, '_Terminal__get_ts_windows', return_value=None), \
                patch.object(Terminal, '_Terminal__get_ts_tput', return_value=(100, 50)) as tput_mock:
            self.assertEqual(Terminal().get_ts(), (100, 50))

        tput_mock.assert_called_once_with()

    def test_get_ts_unix_returns_none_when_legacy_call_fails(self):
        """Terminal.__get_ts_unix() should return None when both providers fail."""

        with patch('src.core.system.terminal.subprocess.check_output', side_effect=AttributeError('no api')), \
                patch.object(Terminal, '_Terminal__legacy_call', side_effect=OSError('boom')):
            self.assertIsNone(getattr(Terminal, '_Terminal__get_ts_unix')())

    def test_get_ts_tput_returns_none_on_oserror(self):
        """Terminal.__get_ts_tput() should return None on subprocess errors."""

        with patch('src.core.system.terminal.subprocess.check_output', side_effect=OSError('boom')):
            self.assertIsNone(getattr(Terminal, '_Terminal__get_ts_tput')())

    def test_legacy_call_rejects_explicit_stdout_argument(self):
        """Terminal.__legacy_call() should reject an explicit stdout kwarg."""

        with self.assertRaises(ValueError):
            getattr(Terminal, '_Terminal__legacy_call')(['echo', 'x'], stdout=object())


if __name__ == '__main__':
    unittest.main()