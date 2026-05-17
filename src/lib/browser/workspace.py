# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development: Stanislav WEB
"""

import atexit
import os
import shutil
import signal
import tempfile
import threading
import weakref

from src.core import CoreConfig
from src.core import filesystem


class ScanTempWorkspace(object):

    """Managed per-scan temporary workspace for runtime-generated wordlists."""

    RUNTIME_LISTS = {
        'tmplist': 'list.tmp',
        'extensionlist': 'extensionlist.tmp',
        'ignore_extensionlist': 'ignore_extensionlist.tmp',
        'remote_wordlist': 'remote-wordlist.tmp',
    }
    _active = weakref.WeakSet()
    _active_lock = threading.RLock()
    _signal_handlers_installed = False
    _previous_signal_handlers = {}

    def __init__(self, root=None, prefix='opendoor-scan-'):
        """
        Create a managed temporary workspace.

        The workspace is intentionally directory-based instead of using
        NamedTemporaryFile so generated wordlists can be reopened on Windows.

        :param str | None root: Parent temporary directory.
        :param str prefix: Directory name prefix passed to tempfile.mkdtemp().
        :raise FileSystemError:
        """

        self.__root = self._resolve_root(root)
        self.__path = None
        self.__paths = {}

        self._ensure_process_cleanup_hooks()

        filesystem.makedir(self.__root)
        self.__path = tempfile.mkdtemp(prefix=prefix, dir=self.__root)
        self.__paths = {
            name: os.path.join(self.__path, filename)
            for name, filename in self.RUNTIME_LISTS.items()
        }
        self._register_active(self)

    @staticmethod
    def _resolve_root(root=None):
        """
        Resolve the parent directory for scan temporary workspaces.

        :param str | None root: Explicit parent directory.
        :return: Absolute parent directory path.
        """

        if root is not None:
            return os.path.abspath(str(root))

        data_config = CoreConfig.get('data') or {}
        tmplist = data_config.get('tmplist')

        if tmplist:
            return os.path.abspath(os.path.dirname(tmplist))

        return os.path.abspath('tmp')

    @property
    def path(self):
        """
        Return the workspace directory path.

        :return: str | None
        """

        return self.__path

    @property
    def paths(self):
        """
        Return generated runtime wordlist paths.

        :return: dict[str, str]
        """

        return dict(self.__paths)

    def get(self, name):
        """
        Return one generated runtime path by logical name.

        :param str name: Runtime path key.
        :return: str | None
        """

        return self.__paths.get(name)

    def cleanup(self):
        """
        Silently remove only this managed workspace directory.

        The method is best-effort and idempotent by design because scan cleanup
        can be triggered by normal completion, exceptions, or interruptions.

        :return: None
        """

        path = self.__path
        if path is None:
            return

        try:
            shutil.rmtree(path, ignore_errors=True)
        finally:
            self._unregister_active(self)
            self.__path = None
            self.__paths = {}

    @classmethod
    def cleanup_active(cls):
        """
        Cleanup all currently registered scan workspaces.

        This is used as a process-level safety net for termination signals that
        can interrupt the normal Browser.close() / finally path.

        :return: None
        """

        with cls._active_lock:
            workspaces = list(cls._active)

        for workspace in workspaces:
            workspace.cleanup()

    @classmethod
    def _register_active(cls, workspace):
        """
        Register a workspace for process-level cleanup hooks.

        :param ScanTempWorkspace workspace: Workspace instance.
        :return: None
        """

        with cls._active_lock:
            cls._active.add(workspace)

    @classmethod
    def _unregister_active(cls, workspace):
        """
        Remove a workspace from the process-level cleanup registry.

        :param ScanTempWorkspace workspace: Workspace instance.
        :return: None
        """

        with cls._active_lock:
            cls._active.discard(workspace)

    @classmethod
    def _ensure_process_cleanup_hooks(cls):
        """
        Install process-level cleanup hooks once per interpreter process.

        :return: None
        """

        with cls._active_lock:
            if cls._signal_handlers_installed is True:
                return

            atexit.register(cls.cleanup_active)
            cls._install_signal_handlers()
            cls._signal_handlers_installed = True

    @classmethod
    def _install_signal_handlers(cls):
        """
        Install best-effort cleanup handlers for supported OS signals.

        Windows exposes only a subset of POSIX signals, so every signal is
        checked dynamically before registration.

        :return: None
        """

        for signal_name in ('SIGINT', 'SIGTERM', 'SIGHUP', 'SIGTSTP'):
            signum = getattr(signal, signal_name, None)

            if signum is None:
                continue

            try:
                cls._previous_signal_handlers[signum] = signal.getsignal(signum)
                signal.signal(signum, cls._handle_signal)
            except (OSError, RuntimeError, ValueError):
                continue

    @classmethod
    def _handle_signal(cls, signum, frame):
        """
        Cleanup active workspaces before terminating after an OS signal.

        Ctrl+Z sends SIGTSTP on POSIX shells. OpenDoor treats it as an abort for
        managed temp cleanup purposes instead of leaving a suspended process with
        stale runtime files.

        :param int signum: Received signal number.
        :param frame: Current stack frame provided by signal.signal().
        :raise KeyboardInterrupt: For SIGINT so existing interrupt handling works.
        :raise SystemExit: For other termination/suspend signals.
        :return: None
        """

        cls.cleanup_active()

        previous = cls._previous_signal_handlers.get(signum)
        if callable(previous) and previous is not cls._handle_signal:
            previous(signum, frame)
            return

        if signum == getattr(signal, 'SIGINT', None):
            raise KeyboardInterrupt

        raise SystemExit(128 + int(signum))
