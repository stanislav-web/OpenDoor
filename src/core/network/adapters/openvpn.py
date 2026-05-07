# -*- coding: utf-8 -*-

"""
    OpenVPN network transport.
"""

import os

from src.core.network.exceptions import NetworkTransportError
from .base import BaseTransport


class OpenVpnTransport(BaseTransport):

    """OpenVPN transport adapter."""

    name = 'openvpn'
    profile_extension = '.ovpn'

    def __init__(self, params, runner=None):
        """
        Constructor.

        :param dict params:
        :param ProcessRunner|None runner:
        """

        BaseTransport.__init__(self, params, runner=runner)
        self.auth = params.get('openvpn_auth')

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

    def build_start_command(self):
        """
        Build OpenVPN command.

        :raise NetworkTransportError:
        :return: list[str]
        """

        self.validate_profile()
        self.validate_auth()

        command = ['openvpn', '--config', self.profile]

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

        message = 'OpenVPN process exited before scan start with code {0}'.format(code)
        output = output.strip()
        if output:
            message = '{0}: {1}'.format(message, output.splitlines()[-1])

        raise NetworkTransportError(message)

    def stop(self):
        """
        Stop OpenVPN process.

        :raise NetworkTransportError:
        :return: None
        """

        self.runner.stop(self.process, timeout=5)
        self.process = None
