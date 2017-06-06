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


class Color(object):

    """Color class"""

    default = 'white'

    @staticmethod
    def __get(key):
        """
        Get color key
        :param str key: color name
        :return: int
        """

        colorlist = {'black': 0, 'red': 1, 'green': 2, 'yellow': 3, 'blue': 4, 'magenta': 5, 'cyan': 6, 'white': 7}
        color_text = colorlist[key] if key in colorlist else colorlist[Color.default]
        return color_text

    @staticmethod
    def __has_colors(stream):
        """
        Is tty output check
        :param object stream: input stream
        :return: bool
        """

        if not hasattr(stream, "isatty"):
            return False
        # noinspection PyUnresolvedReferences
        if not stream.isatty():
            return False  # auto color only on TTYs
        # noinspection PyBroadException
        try:
            import curses
            curses.setupterm()
            return curses.tigetnum("colors") > 2
        except Exception:
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

        if Color.__has_colors(sys.stdout):

            if isinstance(text, bytes):
                text = str(text, "utf-8")

            text = text.strip('\n')
            seq = "\x1b[%dm" % (30 + Color.__get(color)) + text + "\x1b[0m"
            return seq
        else:
            return text
