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

import ctypes
import logging
import os
import re


class ColorizingStreamHandler(logging.StreamHandler):

    """ ColorizingStreamHandler class"""

    # color names to indices
    color_map = {
        'black': 0,
        'red': 1,
        'green': 2,
        'yellow': 3,
        'blue': 4,
        'magenta': 5,
        'cyan': 6,
        'white': 7
    }

    # levels to (background, foreground, bold/intense)
    level_map = {
        logging.DEBUG: (None, 'blue', False),
        logging.INFO: (None, 'black', False),
        logging.WARNING: (None, 'yellow', False),
        logging.ERROR: (None, 'red', False),
        logging.CRITICAL: ('red', 'white', True)
    }

    csi = '\x1b['
    reset = '\x1b[0m'

    @property
    def is_tty(self):
        """
        Is tty output check
        :return: bool
        """

        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def emit(self, record):
        """
        Emmit message
        :param str record: message
        :raise Error
        :return: None
        """

        try:
            message = self.format(record)
            stream = self.stream
            if not self.is_tty:
                stream.write(message)
            else:
                self.output_colorized(message)
            stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as error:
            record.msg = error
            self.handleError(record)

    if os.name != 'nt':
        def output_colorized(self, message):
            """
            Prepare colorized string
            :param str message: message
            :return: None
            """

            self.stream.write(message)

    else:
        ansi_esc = re.compile(r'\x1b\[((?:\d+)(?:;(?:\d+))*)m')

        nt_color_map = {
                            0: 0x00,  # black
                            1: 0x04,  # red
                            2: 0x02,  # green
                            3: 0x06,  # yellow
                            4: 0x01,  # blue
                            5: 0x05,  # magenta
                            6: 0x03,  # cyan
                            7: 0x07  # white
                        }

        def output_colorized(self, message):
            """
            Prepare colorized string
            :param str message: message
            :return: None
            """

            parts = self.ansi_esc.split(message)
            write = self.stream.write
            h = None
            fd = getattr(self.stream, 'fileno', None)
            if fd is not None:
                fd = fd()
                if fd in (1, 2):  # stdout or stderr
                    h = ctypes.windll.kernel32.GetStdHandle(-10 - fd)
            while parts:
                text = parts.pop(0)
                if text:
                    write(text)
                if parts:
                    params = parts.pop(0)
                    if h is not None:
                        params = [int(p) for p in params.split(';')]
                        color = 0
                        for p in params:
                            if 40 <= p <= 47:
                                color |= self.nt_color_map[p - 40] << 4
                            elif 30 <= p <= 37:
                                color |= self.nt_color_map[p - 30]
                            elif p == 1:
                                color |= 0x08  # foreground intensity on
                            elif p == 0:  # reset to default color
                                color = 0x07
                            else:
                                pass  # error condition ignored
                        ctypes.windll.kernel32.SetConsoleTextAttribute(h, color)
