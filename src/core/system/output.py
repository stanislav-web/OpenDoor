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

    Development Team: Brain Storm Team
"""

import os
import platform
import sys


class Output(object):

    """Output class"""

    __is_windows = None

    @staticmethod
    def exit(msg):
        """
        Abort session.

        :param str msg: input message
        :return: None
        """

        sys.exit(msg)

    @staticmethod
    def writels(msg, flush=True):
        """
        Write to stdout on one line dynamically.

        :param str msg: input message
        :param bool flush: force clear line
        :return: None
        """

        sys.stdout.write("\r\x1b[K" + str(msg))
        if flush:
            sys.stdout.flush()

    @staticmethod
    def writeln(msg):
        """
        Write new line.

        :param str msg: input message
        :return: None
        """

        sys.stdout.write('{0}\n'.format(msg))

    @staticmethod
    def version():
        """
        Interpreter version.

        :return: string
        """

        major, minor, _patch = platform.python_version().split(".")
        return "{0}.{1}".format(major, minor)

    @property
    def is_windows(self):
        """
        Check for windows signature.

        :return: bool
        """

        if Output.__is_windows is None:
            Output.__is_windows = sys.platform.startswith('win') or os.name == 'nt'
        return Output.__is_windows