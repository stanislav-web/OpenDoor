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

import logging
import re

from colorize import ColorizingStreamHandler
from src.core.system import Process


class RainbowLoggingHandler(ColorizingStreamHandler):
    """ Class RainbowLoggingHandler """

    # Define color for message payload
    level_map = {logging.DEBUG: (None, 'cyan', False), logging.INFO: (None, 'white', False),
        logging.WARNING: (None, 'yellow', False), logging.ERROR: (None, 'red', True),
        logging.CRITICAL: ('red', 'white', True),}

    date_format = "%H:%M:%S"

    #: How many characters reserve to function name logging
    who_padding = 7

    #: Show logger name
    show_name = False

    def get_color(self, fg=None, bg=None, bold=False):
        """
        Construct a terminal color code
        :param str fg: Symbolic name of foreground color
        :param str bg: Symbolic name of background color
        :param str bold: Brightness bit
        """

        params = []
        if bg in self.color_map:
            params.append(str(self.color_map[bg] + 40))
        if fg in self.color_map:
            params.append(str(self.color_map[fg] + 30))
        if bold:
            params.append('1')

        color_code = ''.join((self.csi, ';'.join(params), 'm'))

        return color_code

    def colorize(self, record):
        """
        Get a special format string with ASCII color codes
        :param object record:
        :return: str
        """

        # Dynamic message color based on logging level
        if record.levelno in self.level_map:
            fg, bg, bold = self.level_map[record.levelno]
        else:
            # Defaults
            bg = None
            fg = "white"
            bold = False

        template = ["[", self.get_color("black", None, True), "%(asctime)s", self.reset, "] ",
            self.get_color("white", None, True) if self.show_name else "", "%(name)s " if self.show_name else "",
            "%(padded_who)s", self.reset, " ", self.get_color(bg, fg, bold), "%(message)s", self.reset, ]

        format = "".join(template)

        who = [self.get_color("green"), getattr(record, "funcName", ""), self.get_color("black", None, True), ":",
               self.get_color("cyan")]

        who = "".join(who)
        # We need to calculate padding length manualy
        # as color codes mess up string length based calcs
        unformatted_who = getattr(record, "funcName", "")

        if len(unformatted_who) < self.who_padding:
            spaces = " " * (self.who_padding - len(unformatted_who))
        else:
            spaces = ""

        record.padded_who = who + spaces

        formatter = logging.Formatter(format, self.date_format)
        self.colorize_traceback(formatter, record)
        output = formatter.format(record)
        # Clean cache so the color codes of traceback don't leak to other formatters
        record.ext_text = None

        width = int(Process.terminal_size.get('width'))
        if record.levelno != logging.DEBUG:
            if len(output) > width and record.levelno != logging.ERROR:
                output = (output[:(width)] + '...')

        length = width - self.__pure_line_len(output)
        end = (' ' * length)[:length]
        return output + end

    @classmethod
    def __pure_line_len(cls, string):
        """
        Get pure line
        :param str string:
        :return:
        """

        ansi_escape = re.compile(r'\x1b[^m]*m')
        return len(ansi_escape.sub('', string))

    def colorize_traceback(self, formatter, record):
        """
        Turn traceback text to red
        :param object formatter:
        :param object record:
        :return: None
        """

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            record.exc_text = "".join([self.get_color("red"), formatter.formatException(record.exc_info), self.reset, ])

    def format(self, record):
        """
        Formats a record for output.
        Takes a custom formatting path on a terminal.
        :param str record: input message
        :return: str
        """

        if self.is_tty:
            message = self.colorize(record)
        else:
            message = logging.StreamHandler.format(self, record)

        return message
