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

from .config import Config

class Color:
    """Color class"""

    @staticmethod
    def __has_colors(stream):
        """
        Is tty output check
        :param object stream: input stream
        :return: bool
        """

        if not hasattr(stream, "isatty"):
            return False
        if not stream.isatty():
            return False  # auto color only on TTYs
        try:
            import curses
            curses.setupterm()
            return curses.tigetnum("colors") > 2
        except:
            # guess false in case of error
            return False

    @staticmethod
    def colored(text, color):
        """
        Output colorized text
        :param str text: message
        :param str color: prefered color
        :return: string
        """

        if type(text) is not str:
            text = str(text)
        if Color.__has_colors(sys.stdout):
            text = text.strip('\n')
            seq = "\x1b[%dm" % (30 + Config.get(color)) + text + "\x1b[0m"
            return seq
        else:
            return text
