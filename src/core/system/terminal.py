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

import platform
import shlex
import shutil
import struct
import subprocess


class Terminal(object):

    """Terminal class"""

    DEFAULT_WIDTH = 80
    DEFAULT_HEIGHT = 25

    def get_ts(self):
        """
        Get width and height of console.

        :return: tuple
        """

        current_os = platform.system()

        if current_os == 'Windows':
            return self.__get_ts_windows() or self.__get_ts_tput() or self.__get_ts_fallback()

        if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
            return self.__get_ts_unix() or self.__get_ts_fallback()

        return self.__get_ts_fallback()

    @staticmethod
    def __get_ts_windows():
        """
        Get windows terminal size.

        :return: tuple
        """

        try:
            from ctypes import windll, create_string_buffer

            sizex, sizey = Terminal.DEFAULT_WIDTH, Terminal.DEFAULT_HEIGHT
            handle = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            result = windll.kernel32.GetConsoleScreenBufferInfo(handle, csbi)
            if result:
                (
                    _bufx,
                    _bufy,
                    _curx,
                    _cury,
                    _wattr,
                    left,
                    top,
                    right,
                    bottom,
                    _maxx,
                    _maxy,
                ) = struct.unpack("hhhhHhhhhhh", csbi.raw)
                sizex = right - left + 1
                sizey = bottom - top + 1
            return sizex, sizey
        except Exception:
            return None

    @staticmethod
    def __get_ts_unix():
        """
        Get unix terminal size.

        :return tuple
        """

        try:
            output = subprocess.check_output(['stty', 'size'], stderr=subprocess.DEVNULL)
        except (AttributeError, subprocess.CalledProcessError, OSError, ValueError):
            try:
                output = Terminal.__legacy_call(['stty', 'size'])
            except (subprocess.CalledProcessError, OSError, ValueError):
                return None

        if isinstance(output, bytes):
            output = output.decode('utf-8', errors='ignore')

        parts = str(output).strip().split()
        if len(parts) != 2:
            return None

        try:
            height, width = map(int, parts)
        except ValueError:
            return None

        return width, height

    @staticmethod
    def __legacy_call(*popenargs, **kwargs):
        """
        Subprocess check output for legacy python version 2.6.

        :param popenargs:
        :param kwargs:
        :return:
        """

        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        del unused_err
        return output

    @staticmethod
    def __get_ts_tput():
        """
        Get terminal height / width.

        :return: tuple
        """

        try:
            cols = int(subprocess.check_output(shlex.split('tput cols'), stderr=subprocess.DEVNULL).strip())
            rows = int(subprocess.check_output(shlex.split('tput lines'), stderr=subprocess.DEVNULL).strip())
            return cols, rows
        except (subprocess.CalledProcessError, OSError, ValueError):
            return None

    @staticmethod
    def __get_ts_fallback():
        """
        Get terminal size using Python standard-library fallback.

        :return: tuple
        """

        size = shutil.get_terminal_size((Terminal.DEFAULT_WIDTH, Terminal.DEFAULT_HEIGHT))
        return size.columns, size.lines