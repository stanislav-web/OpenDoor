# -*- coding: utf-8 -*-

import signal
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core.system.process import Process
from src.core.system.exceptions import CoreSystemError


class TestProcess(unittest.TestCase):
    """TestProcess class."""

    def test_terminal_size_is_cached(self):
        """Process.terminal_size should cache the resolved size."""

        process = Process()

        with patch('src.core.system.process.Terminal.get_ts', return_value=(120, 50)) as get_ts_mock:
            first = process.terminal_size
            second = process.terminal_size

        self.assertEqual(first, {'height': 50, 'width': 120})
        self.assertEqual(second, {'height': 50, 'width': 120})
        get_ts_mock.assert_called_once_with()

    def test_terminal_size_returns_existing_cache_without_terminal_call(self):
        """Process.terminal_size should return preloaded cache without touching Terminal."""

        process = Process()
        process.ts = {'height': 40, 'width': 100}

        with patch('src.core.system.process.Terminal.get_ts') as get_ts_mock:
            result = process.terminal_size

        self.assertEqual(result, {'height': 40, 'width': 100})
        get_ts_mock.assert_not_called()

    def test_termination_handler_registers_signal_callback(self):
        """Process.termination_handler should register a termination callback."""

        with patch('src.core.system.process.signal.signal') as signal_mock:
            Process.termination_handler()

        registered_signal, callback = signal_mock.call_args[0]
        self.assertIn(registered_signal, [getattr(signal, 'SIGTSTP', signal.SIGABRT), signal.SIGABRT])
        self.assertTrue(callable(callback))

    def test_termination_handler_callback_kills_current_process(self):
        """Process.termination_handler callback should terminate current process with SIGTERM."""

        with patch('src.core.system.process.signal.signal') as signal_mock:
            Process.termination_handler()

        _, callback = signal_mock.call_args[0]

        with patch('src.core.system.process.os.getpid', return_value=321), \
                patch('src.core.system.process.os.kill') as kill_mock:
            callback(20, object())

        kill_mock.assert_called_once_with(321, signal.SIGTERM)

    def test_termination_handler_uses_sigabrt_when_sigtstp_is_missing(self):
        """Process.termination_handler should fall back to SIGABRT when SIGTSTP is unavailable."""

        fake_signal = SimpleNamespace(SIGABRT=99, SIGTERM=15, signal=MagicMock())

        with patch('src.core.system.process.signal', fake_signal):
            Process.termination_handler()

        registered_signal, callback = fake_signal.signal.call_args[0]
        self.assertEqual(registered_signal, 99)
        self.assertTrue(callable(callback))

    def test_kill_sends_sigterm_to_current_process(self):
        """Process.kill() should terminate the current process with SIGTERM."""

        with patch('src.core.system.process.os.getpid', return_value=123), \
                patch('src.core.system.process.os.kill') as kill_mock:
            Process.kill()

        kill_mock.assert_called_once_with(123, signal.SIGTERM)

    def test_execute_returns_stdout_for_successful_command(self):
        """Process.execute() should return stdout on success."""

        completed = MagicMock(returncode=0, stdout=b'output', stderr=b'')

        with patch('src.core.system.process.subprocess.run', return_value=completed) as run_mock:
            result = Process.execute('echo test')

        self.assertEqual(result, b'output')
        run_mock.assert_called_once()
        self.assertEqual(run_mock.call_args.kwargs['shell'], True)
        self.assertEqual(run_mock.call_args.kwargs['stdout'], subprocess.PIPE)
        self.assertEqual(run_mock.call_args.kwargs['stderr'], subprocess.PIPE)
        self.assertEqual(run_mock.call_args.kwargs['check'], False)

    def test_execute_raises_core_system_error_for_failed_command(self):
        """Process.execute() should wrap command failures into CoreSystemError."""

        completed = MagicMock(returncode=1, stdout=b'', stderr=b'boom')

        with patch('src.core.system.process.subprocess.run', return_value=completed):
            with self.assertRaises(CoreSystemError):
                Process.execute('false')

    def test_execute_uses_stdout_when_stderr_is_empty(self):
        """Process.execute() should use stdout as error message fallback when stderr is empty."""

        completed = MagicMock(returncode=1, stdout=b'boom-stdout', stderr=b'')

        with patch('src.core.system.process.subprocess.run', return_value=completed):
            with self.assertRaises(CoreSystemError) as context:
                Process.execute('false')

        self.assertIn('boom-stdout', str(context.exception))

    def test_execute_uses_default_error_message_when_streams_are_empty(self):
        """Process.execute() should use the default message when both stderr and stdout are empty."""

        completed = MagicMock(returncode=1, stdout=b'', stderr=b'')

        with patch('src.core.system.process.subprocess.run', return_value=completed):
            with self.assertRaises(CoreSystemError) as context:
                Process.execute('false')

        self.assertIn('Command execution failed', str(context.exception))

    def test_execute_wraps_subprocess_errors(self):
        """Process.execute() should wrap subprocess-level exceptions into CoreSystemError."""

        with patch('src.core.system.process.subprocess.run', side_effect=subprocess.SubprocessError('subprocess boom')):
            with self.assertRaises(CoreSystemError) as context:
                Process.execute('false')

        self.assertIn('subprocess boom', str(context.exception))


if __name__ == '__main__':
    unittest.main()