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

import os
import platform
import signal
import sys


class System(object):
    """System class"""

    @staticmethod
    def kill():
        """
        Immediatelly terminate process
        :return: None
        """

        os.kill(os.getpid(), signal.SIGTERM)  # or signal.SIGKILL

    @staticmethod
    def termination_handler():
        """
        Exit Ctrl-Z handler
        :return: None
        """

        def kill_process(signum, frame):
            """
            Kill process os signal
            :param int signum: signal code
            :param object frame: frame object
            :return: None
            """

            del signum
            del frame

            os.kill(os.getpid(), signal.SIGTERM)

        signal.signal(signal.SIGTSTP, kill_process)

    @staticmethod
    def exit(msg):
        """
        Abort session
        :param str msg: text message
        :return: None
        """

        sys.exit(msg)

    @staticmethod
    def writels(msg, flush=True):
        """
        Write to stdout on one line dynamically
        :param str msg: text message
        :param bool flush: force flush
        :return: None
        """

        sys.stdout.write("\r\x1b[K" + msg.__str__())
        if True is flush:
            sys.stdout.flush()

    @staticmethod
    def writeln(msg):
        """
        Write new line
        :param str msg: text message
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
