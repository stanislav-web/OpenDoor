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

import os
import platform
import sys
import threading


class Output(object):

    """Output class"""

    __is_windows = None
    __dynamic_line_active = False
    __dynamic_line_last_length = 0
    __dynamic_line_lock = threading.RLock()

    @staticmethod
    def exit(msg):
        """
        Abort session.

        :param str msg: input message
        :return: None
        """

        sys.exit(msg)

    @staticmethod
    def mark_dynamic_line(length=0):
        """Mark that stdout currently contains an active rotating line.

        Persistent logger output must first terminate this line, otherwise the
        next log record is appended to the same terminal row.

        :param int length: length of the rendered rotating line
        :return: None
        """

        try:
            rendered_length = max(int(length or 0), 0)
        except (TypeError, ValueError):
            rendered_length = 0

        with Output.__dynamic_line_lock:
            Output.__dynamic_line_active = True
            Output.__dynamic_line_last_length = rendered_length

    @staticmethod
    def clear_dynamic_line():
        """Forget active rotating-line state after explicit cleanup.

        :return: None
        """

        with Output.__dynamic_line_lock:
            Output.__dynamic_line_active = False
            Output.__dynamic_line_last_length = 0

    @staticmethod
    def finish_dynamic_line():
        """Move persistent output to a clean line after rotating progress.

        :return: None
        """

        with Output.__dynamic_line_lock:
            if Output.__dynamic_line_active is not True:
                return

            try:
                sys.stdout.write('\n')
                sys.stdout.flush()
            except (AttributeError, OSError, ValueError):
                pass

            Output.__dynamic_line_active = False
            Output.__dynamic_line_last_length = 0

    @staticmethod
    def writels(msg, flush=True):
        """
        Write to stdout on one line dynamically.

        The legacy ANSI clear-line sequence is only safe for interactive terminals.
        Log files and piped output should remain plain text, especially when
        color is disabled by CLI_COLOR=0 or NO_COLOR.

        :param str msg: input message
        :param bool flush: force clear line
        :return: None
        """

        sys.stdout.write(Output.__line_prefix() + str(msg))
        if flush:
            sys.stdout.flush()

    @staticmethod
    def __line_prefix():
        """
        Return the dynamic-line prefix for the current stdout target.

        :return: carriage-return prefix, with ANSI clear-line only for TTY output
        :rtype: str
        """

        if os.environ.get('CLI_COLOR') == '0' or os.environ.get('NO_COLOR'):
            return "\r"

        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return "\r"

        return "\r\x1b[K"

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
