# -*- coding: utf-8 -*-

"""
    Base network transport adapter.
"""

import os
import platform
import shutil

from src.core.network.exceptions import NetworkTransportError
from src.core.network.process import ProcessRunner


class BaseTransport(object):

    """Base network transport adapter."""

    name = 'base'
    profile_extension = None

    def __init__(self, params, runner=None):
        """
        Constructor.

        :param dict params:
        :param ProcessRunner|None runner:
        """

        self.params = params
        self.runner = runner or ProcessRunner()
        self.profile = params.get('transport_profile')
        self.timeout = 30 if params.get('transport_timeout') is None else int(params.get('transport_timeout'))
        self.executable = params.get('transport_bin')
        self.process = None

    def resolve_executable(self, command, candidates=None):
        """
        Resolve a transport executable in a cross-platform way.

        :param str command: Default executable name.
        :param list[str]|None candidates: Additional absolute executable candidates.
        :raise NetworkTransportError:
        :return: str
        """

        if self.executable is not None:
            return self.__resolve_explicit_executable(self.executable)

        resolved = shutil.which(command)
        if resolved is not None:
            return resolved

        for candidate in candidates or []:
            if self.__is_executable_file(candidate) is True:
                return candidate

        raise NetworkTransportError(self.__build_missing_executable_error(command))

    def __resolve_explicit_executable(self, executable):
        """
        Resolve user-provided transport executable path or command name.

        :param str executable:
        :raise NetworkTransportError:
        :return: str
        """

        executable = str(executable).strip()
        resolved = shutil.which(executable)
        if resolved is not None:
            return resolved

        if self.__is_executable_file(executable) is True:
            return executable

        raise NetworkTransportError('Transport executable does not exist or is not executable: {0}'.format(executable))

    @staticmethod
    def __is_executable_file(path):
        """
        Check executable file existence.

        :param str path:
        :return: bool
        """

        return os.path.isfile(path) is True and os.access(path, os.X_OK) is True

    def __build_missing_executable_error(self, command):
        """
        Build an actionable missing executable error.

        :param str command:
        :return: str
        """

        system = platform.system().lower()
        base = '{0} executable not found in PATH'.format(command)

        if command == 'openvpn':
            if system == 'darwin':
                return '{0}. Install OpenVPN CLI or pass --transport-bin. macOS example: brew install openvpn; common paths: /opt/homebrew/sbin/openvpn or /usr/local/sbin/openvpn'.format(base)
            if system == 'windows':
                return '{0}. Install OpenVPN Community client and pass --transport-bin to openvpn.exe when it is not in PATH. Common path: C:\\Program Files\\OpenVPN\\bin\\openvpn.exe'.format(base)
            return '{0}. Install the OpenVPN package or pass --transport-bin. Linux examples: apt install openvpn, dnf install openvpn, pacman -S openvpn'.format(base)

        if command == 'wg-quick':
            if system == 'windows':
                return '{0}. wg-quick is not a native Windows backend. Start WireGuard outside OpenDoor and use --transport direct, or pass a compatible wrapper with --transport-bin.'.format(base)
            return '{0}. Install WireGuard tools or pass --transport-bin. Linux example: apt install wireguard-tools; macOS example: brew install wireguard-tools'.format(base)

        return '{0}. Pass --transport-bin with the executable path.'.format(base)

    @property
    def profile_name(self):
        """
        Safe profile basename for logs.

        :return: str
        """

        if self.profile is None:
            return '-'

        return os.path.basename(str(self.profile))

    def validate_profile(self):
        """
        Validate selected transport profile.

        :raise NetworkTransportError:
        :return: None
        """

        if self.profile_extension is None:
            return

        if self.profile is None:
            raise NetworkTransportError('{0} transport requires a profile'.format(self.name))

        if str(self.profile).lower().endswith(self.profile_extension) is False:
            raise NetworkTransportError('{0} transport requires *{1} profile'.format(
                self.name,
                self.profile_extension
            ))

        if os.path.isfile(self.profile) is False:
            raise NetworkTransportError('{0} profile does not exist: {1}'.format(
                self.name,
                self.profile
            ))

    def start(self):
        """
        Start transport.

        :return: None
        """

        return None

    def stop(self):
        """
        Stop transport.

        :return: None
        """

        return None
