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

    Development Team: Stanislav WEB
"""

import sys
import platform

class Output(object):
    """Output class"""

    @staticmethod
    def exit(msg):
        """
        Abort session
        :param str msg: input message
        :return: None
        """

        sys.exit(msg)

    @staticmethod
    def writels(msg, flush=True):
        """
        Write to stdout on one line dynamically
        :param str msg: input message
        :param bool flush: force clear line
        :return: None
        """

        sys.stdout.write("\r\x1b[K" + msg.__str__())
        if True is flush:
            sys.stdout.flush()

    @staticmethod
    def writeln(msg):
        """
        Write new line
        :param str msg: input message
        :return: None
        """

        sys.stdout.write('{0}\n'.format(msg))

    @staticmethod
    def version():
        """
        Interpreter version
        :return: string
        """

        version = platform.python_version().split(".")
        return "{0}.{1}".format(version[0], version[1])

    @staticmethod
    def is_windows():
        """
        Check for windows signature
        :return: bool
        """

        return sys.platform.startswith('win')
