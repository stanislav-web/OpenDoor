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

import platform
import shlex
import struct
import subprocess


class Terminal(object):

    """ Terminal class"""
    
    def get_ts(self):
        """
        Get width and height of console
        :return: tuple
        """
    
        current_os = platform.system()
        tuple_xy = (80, 25)  # default value
        if current_os == 'Windows':
            tuple_xy = self.__get_ts_windows()
            if tuple_xy is None:
                tuple_xy = self.__get_ts_tput()
        if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
            tuple_xy = self.__get_ts_unix()
        return tuple_xy
    
    @staticmethod
    def __get_ts_windows():
        """
        Get windows terminal size
        :return: tuple
        """

        # noinspection PyBroadException
        try:
            from ctypes import windll, create_string_buffer
            (sizex, sizey) = 25, 80  # default value
            h = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
            if res:
                (bufx, bufy, curx, cury, wattr,
                 left, top, right, bottom,
                 maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
                sizex = right - left + 1
                sizey = bottom - top + 1
            return sizex, sizey
        except Exception:
            pass

    @staticmethod
    def __get_ts_unix():
        """
        Get unix terminal size
        :return tuple
        """
        (height, width) = 25, 80
        
        try:
            (height, width) = subprocess.check_output(['stty', 'size']).split()
        except (AttributeError, subprocess.CalledProcessError):
            subprocess.check_output = Terminal.__legacy_call
            (height, width) = subprocess.check_output(['stty', 'size']).split()
        finally:
            return width, height

    @staticmethod
    def __legacy_call(*popenargs, **kwargs):
        """
        Subprocess check output for legacy python version 2.6
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
        Get terminal height / width
        :return: tuple
        """
    
        try:
            cols = int(subprocess.check_call(shlex.split('tput cols')))
            rows = int(subprocess.check_call(shlex.split('tput lines')))
            return cols, rows
        except subprocess.CalledProcessError:
            pass
