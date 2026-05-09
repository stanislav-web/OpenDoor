# -*- coding: utf-8 -*-

"""
    WireGuard network transport.
"""

import os
import platform

from .base import BaseTransport


class WireGuardTransport(BaseTransport):

    """WireGuard transport adapter."""

    name = 'wireguard'
    profile_extension = '.conf'

    @staticmethod
    def executable_candidates():
        """
        Return common wg-quick locations across Unix-like systems.

        :return: list[str]
        """

        if os.name == 'nt' or platform.system().lower() == 'windows':
            return []

        return [
            '/usr/bin/wg-quick',
            '/usr/sbin/wg-quick',
            '/usr/local/bin/wg-quick',
            '/usr/local/sbin/wg-quick',
            '/opt/homebrew/bin/wg-quick',
            '/opt/homebrew/sbin/wg-quick',
        ]

    def build_up_command(self):
        """
        Build WireGuard up command.

        :return: list[str]
        """

        self.validate_profile()
        return [self.resolve_executable('wg-quick', self.executable_candidates()), 'up', self.profile]

    def build_down_command(self):
        """
        Build WireGuard down command.

        :return: list[str]
        """

        self.validate_profile()
        return [self.resolve_executable('wg-quick', self.executable_candidates()), 'down', self.profile]

    def start(self):
        """
        Start WireGuard transport.

        :return:
        """

        return self.runner.run(self.build_up_command(), timeout=self.timeout)

    def stop(self):
        """
        Stop WireGuard transport.

        :return:
        """

        return self.runner.run(self.build_down_command(), timeout=self.timeout)