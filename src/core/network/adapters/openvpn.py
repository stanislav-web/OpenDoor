# -*- coding: utf-8 -*-

"""
    OpenVPN network transport.
"""

import os
import time

from src.core.network.exceptions import NetworkTransportError
from .base import BaseTransport


class OpenVpnTransport(BaseTransport):

    """OpenVPN transport adapter."""

    name = 'openvpn'
    profile_extension = '.ovpn'
    STARTUP_GRACE_SEC = 3.0
    STARTUP_POLL_SEC = 0.2

    def __init__(self, params, runner=None):
        """
        Constructor.

        :param dict params:
        :param ProcessRunner|None runner:
        """

        BaseTransport.__init__(self, params, runner=runner)
        self.auth = params.get('openvpn_auth')
        self.debug = self.__parse_debug_level(params.get('debug'))

    def validate_auth(self):
        """
        Validate optional auth-user-pass file.

        :raise NetworkTransportError:
        :return: None
        """

        if self.auth is None:
            return

        if os.path.isfile(self.auth) is False:
            raise NetworkTransportError('OpenVPN auth file does not exist: {0}'.format(self.auth))

    def executable_candidates(self):
        """
        Return common OpenVPN CLI locations across supported desktop OSes.

        :return: list[str]
        """

        candidates = []

        if os.name == 'nt':
            for root in [os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)')]:
                if root:
                    candidates.append(os.path.join(root, 'OpenVPN', 'bin', 'openvpn.exe'))
            return candidates

        return [
            '/usr/sbin/openvpn',
            '/usr/bin/openvpn',
            '/usr/local/sbin/openvpn',
            '/usr/local/bin/openvpn',
            '/opt/homebrew/sbin/openvpn',
            '/opt/homebrew/bin/openvpn',
        ]

    def build_start_command(self):
        """
        Build OpenVPN command.

        :raise NetworkTransportError:
        :return: list[str]
        """

        self.validate_profile()
        self.validate_auth()

        command = [self.resolve_executable('openvpn', self.executable_candidates()), '--config', self.profile]

        if self.auth is not None:
            command.extend(['--auth-user-pass', self.auth])

        return command

    def start(self):
        """
        Start OpenVPN process.

        :raise NetworkTransportError:
        :return: subprocess.Popen
        """

        command = self.build_start_command()
        self.process = self.runner.start_persistent(command)
        return self.process

    def wait_ready(self, timeout=30):
        """
        Give OpenVPN time to create the OS tunnel route after process start.

        OpenVPN is started as a persistent process. Popen only means the
        process was spawned; the tunnel interface, routes and DNS may still be
        initializing. Without this grace period the scanner can immediately run
        its target socket check and fail before OpenVPN finishes startup.

        :param int timeout: Transport timeout. Used as an upper bound.
        :raise NetworkTransportError:
        :return: None
        """

        grace = min(float(timeout), self.STARTUP_GRACE_SEC)
        deadline = time.monotonic() + max(0.0, grace)

        while True:
            self.assert_running()
            if time.monotonic() >= deadline:
                return
            time.sleep(self.STARTUP_POLL_SEC)

    def assert_running(self):
        """
        Ensure OpenVPN did not exit immediately after startup.

        :raise NetworkTransportError:
        :return: None
        """

        if self.process is None:
            return

        code = self.process.poll()
        if code is None:
            return

        output = ''
        try:
            output = self.process.communicate(timeout=1)[0] or ''
        except Exception:
            output = ''

        raise NetworkTransportError(self.__format_process_exit_error(code, output))

    @staticmethod
    def __parse_debug_level(value):
        """
        Parse transport debug level.

        :param int|str|None value:
        :return: int
        """

        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def __format_process_exit_error(self, code, output):
        """
        Format OpenVPN early-exit diagnostics according to debug level.

        :param int code:
        :param str output:
        :return: str
        """

        message = 'OpenVPN process exited before scan start with code {0}'.format(code)
        lines = self.__normalize_output_lines(output)

        if len(lines) <= 0:
            return message

        if self.debug >= 2:
            return '{0}. OpenVPN output tail:\n{1}'.format(
                message,
                '\n'.join(lines[-12:])
            )

        summary = self.__select_summary_line(lines)
        return '{0}: {1}. Re-run with --debug 2 for OpenVPN output tail.'.format(message, summary)

    @staticmethod
    def __normalize_output_lines(output):
        """
        Convert process output to non-empty stripped lines.

        :param str|None output:
        :return: list[str]
        """

        if not output:
            return []

        return [
            line.strip()
            for line in str(output).splitlines()
            if line.strip()
        ]

    @staticmethod
    def __select_summary_line(lines):
        """
        Pick the most useful single-line error for low debug levels.

        :param list[str] lines:
        :return: str
        """

        generic_tail_markers = [
            'exiting due to fatal error',
            'process exiting',
            'sigterm',
        ]

        for line in reversed(lines):
            lowered = line.lower()
            if any(marker in lowered for marker in generic_tail_markers):
                continue
            return line

        return lines[-1] if lines else ''

    def stop(self):
        """
        Stop OpenVPN process.

        :raise NetworkTransportError:
        :return: None
        """

        self.runner.stop(self.process, timeout=5)
        self.process = None
