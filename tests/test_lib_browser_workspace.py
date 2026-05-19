# -*- coding: utf-8 -*-

import os
import signal
import tempfile
import unittest

from unittest.mock import MagicMock, patch

from src.lib.browser.workspace import ScanTempWorkspace


class TestScanTempWorkspace(unittest.TestCase):

    """Test per-scan temporary workspace behavior."""

    def test_workspace_creates_runtime_paths_inside_managed_directory(self):
        """ScanTempWorkspace should isolate runtime wordlists under one directory."""

        with tempfile.TemporaryDirectory() as root:
            workspace = ScanTempWorkspace(root=root, prefix='opendoor-test-')

            self.assertTrue(os.path.isdir(workspace.path))
            self.assertTrue(os.path.basename(workspace.path).startswith('opendoor-test-'))

            paths = workspace.paths
            self.assertEqual(set(paths.keys()), {'tmplist', 'extensionlist', 'ignore_extensionlist', 'remote_wordlist'})

            for path in paths.values():
                self.assertEqual(os.path.dirname(path), workspace.path)

            self.assertEqual(paths['tmplist'], workspace.get('tmplist'))
            workspace.cleanup()

    def test_cleanup_removes_only_managed_directory(self):
        """Cleanup should delete only the workspace and preserve sibling files."""

        with tempfile.TemporaryDirectory() as root:
            sibling = os.path.join(root, 'keep.tmp')
            with open(sibling, 'w', encoding='utf-8') as handler:
                handler.write('keep')

            workspace = ScanTempWorkspace(root=root, prefix='opendoor-test-')
            managed_path = workspace.path
            runtime_path = workspace.get('tmplist')

            with open(runtime_path, 'w', encoding='utf-8') as handler:
                handler.write('admin\n')

            workspace.cleanup()

            self.assertFalse(os.path.exists(managed_path))
            self.assertTrue(os.path.isfile(sibling))
            self.assertIsNone(workspace.path)
            self.assertEqual(workspace.paths, {})


    def test_cleanup_active_removes_registered_workspaces(self):
        """Process-level cleanup should remove all active managed workspaces."""

        with tempfile.TemporaryDirectory() as root:
            workspace = ScanTempWorkspace(root=root, prefix='opendoor-test-')
            managed_path = workspace.path

            ScanTempWorkspace.cleanup_active()

            self.assertFalse(os.path.exists(managed_path))
            self.assertIsNone(workspace.path)

    def test_signal_handler_cleans_active_workspaces_and_aborts(self):
        """Signal cleanup should remove temp files before aborting the process."""

        with tempfile.TemporaryDirectory() as root:
            workspace = ScanTempWorkspace(root=root, prefix='opendoor-test-')
            managed_path = workspace.path
            signum = getattr(signal, 'SIGTERM', signal.SIGINT)

            ScanTempWorkspace._previous_signal_handlers[signum] = None

            with self.assertRaises(SystemExit):
                ScanTempWorkspace._handle_signal(signum, None)

            self.assertFalse(os.path.exists(managed_path))
            self.assertIsNone(workspace.path)

    def test_sigint_handler_preserves_workspace_for_pause_resume(self):
        """SIGINT should raise KeyboardInterrupt without deleting pause-resume workspaces."""

        with tempfile.TemporaryDirectory() as root:
            workspace = ScanTempWorkspace(root=root, prefix='opendoor-test-')
            managed_path = workspace.path

            ScanTempWorkspace._previous_signal_handlers[signal.SIGINT] = None

            with self.assertRaises(KeyboardInterrupt):
                ScanTempWorkspace._handle_signal(signal.SIGINT, None)

            self.assertTrue(os.path.isdir(managed_path))
            self.assertEqual(workspace.path, managed_path)
            workspace.cleanup()


    def test_sigint_handler_chains_previous_handler_without_cleanup(self):
        """Custom SIGINT handlers should run without eager workspace cleanup."""

        with tempfile.TemporaryDirectory() as root:
            workspace = ScanTempWorkspace(root=root, prefix='opendoor-test-')
            managed_path = workspace.path
            previous = MagicMock()

            ScanTempWorkspace._previous_signal_handlers[signal.SIGINT] = previous

            ScanTempWorkspace._handle_signal(signal.SIGINT, None)

            previous.assert_called_once_with(signal.SIGINT, None)
            self.assertTrue(os.path.isdir(managed_path))
            self.assertEqual(workspace.path, managed_path)
            workspace.cleanup()

    def test_install_signal_handlers_skips_missing_signals(self):
        """Signal hook installation should ignore signals unavailable on the current OS."""

        class FakeSignal:
            SIGINT = 2

            @staticmethod
            def getsignal(signum):
                return None

            @staticmethod
            def signal(signum, handler):
                return None

        with patch('src.lib.browser.workspace.signal', FakeSignal):
            ScanTempWorkspace._install_signal_handlers()

    def test_install_signal_handlers_ignores_registration_errors(self):
        """Signal hook installation should remain best-effort on unsupported runtimes."""

        class FakeSignal:
            SIGINT = 2
            SIGTERM = 15
            SIGHUP = 1
            SIGTSTP = 20

            @staticmethod
            def getsignal(signum):
                return None

            @staticmethod
            def signal(signum, handler):
                raise ValueError('unsupported signal')

        with patch('src.lib.browser.workspace.signal', FakeSignal):
            ScanTempWorkspace._install_signal_handlers()

    def test_signal_handler_chains_custom_previous_handler_after_cleanup(self):
        """Custom signal handlers should still run after workspace cleanup."""

        with tempfile.TemporaryDirectory() as root:
            workspace = ScanTempWorkspace(root=root, prefix='opendoor-test-')
            managed_path = workspace.path
            signum = getattr(signal, 'SIGTERM', signal.SIGINT)
            previous = MagicMock()

            ScanTempWorkspace._previous_signal_handlers[signum] = previous

            ScanTempWorkspace._handle_signal(signum, None)

            previous.assert_called_once_with(signum, None)
            self.assertFalse(os.path.exists(managed_path))
            self.assertIsNone(workspace.path)

    def test_default_root_falls_back_to_tmp_when_core_path_is_missing(self):
        """Default root resolution should stay deterministic without tmplist config."""

        with patch('src.lib.browser.workspace.CoreConfig', {'data': {}}):
            self.assertEqual(ScanTempWorkspace._resolve_root(), os.path.abspath('tmp'))

    def test_cleanup_is_idempotent_when_files_are_missing(self):
        """Cleanup should be safe when called multiple times."""

        with tempfile.TemporaryDirectory() as root:
            workspace = ScanTempWorkspace(root=root, prefix='opendoor-test-')
            managed_path = workspace.path

            workspace.cleanup()
            workspace.cleanup()

            self.assertFalse(os.path.exists(managed_path))


if __name__ == '__main__':
    unittest.main()
