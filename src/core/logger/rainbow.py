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

import logging
import re

from .colorize import ColorizingStreamHandler
from src.core.system import Term


class RainbowLoggingHandler(ColorizingStreamHandler):
    """TTY-aware colorizing stream handler for OpenDoor CLI logs."""

    # Define color for message payload.
    level_map = {
        logging.DEBUG: ('cyan', False),
        logging.INFO: ('white', False),
        logging.WARNING: ('yellow', False),
        logging.ERROR: ('red', True),
        logging.CRITICAL: ('red', True),
    }

    date_format = "%H:%M:%S"

    #: How many characters to reserve for the logging function name.
    who_padding = 7

    def get_color(self, fg=None, bold=False):
        """
        Construct a terminal color code.

        :param str fg: Symbolic foreground color name.
        :param bool bold: Whether to enable bold output.
        :return: ANSI color code.
        :rtype: str
        """

        params = []

        if fg in self.color_map:
            params.append(str(self.color_map[fg] + 30))
        if bold:
            params.append('1')

        return ''.join((self.csi, ';'.join(params), 'm'))

    def colorize(self, record):
        """
        Build a TTY-aware colorized log message.

        :param logging.LogRecord record: Log record to format.
        :return: Colorized log message.
        :rtype: str
        """

        # Dynamic message color based on logging level.
        if not hasattr(record, 'levelno'):
            record.levelno = logging.INFO

        fg, bold = self.level_map.get(record.levelno, self.level_map[logging.INFO])

        template = [
            "[",
            self.get_color("black"),
            "%(asctime)s",
            self.reset,
            "] ",
            "%(padded_who)s",
            self.reset,
            " ",
            self.get_color(fg, bold),
            "%(message)s",
            self.reset,
        ]

        format_string = "".join(template)

        func_name = getattr(record, "funcName", "")
        who = [
            self.get_color("green"),
            func_name,
            self.get_color("black", True),
            ":",
            self.get_color("cyan"),
        ]

        # Calculate padding manually because ANSI color codes affect raw string length.
        if len(func_name) < self.who_padding:
            spaces = " " * (self.who_padding - len(func_name))
        else:
            spaces = ""

        record.padded_who = "".join(who) + spaces

        formatter = logging.Formatter(format_string, self.date_format)
        output = formatter.format(record)

        # Clean cached exception text so colored tracebacks do not leak to other formatters.
        record.exc_text = None

        width = int(Term.terminal_size['width'])
        pure_length = self.__pure_line_len(output)
        length = width - pure_length

        if record.levelno != logging.DEBUG:
            if pure_length > width and record.levelno != logging.ERROR:
                output = output[:width] + '...'

        end = (' ' * length)[:length]
        return output + end

    @classmethod
    def __pure_line_len(cls, string):
        """
        Get line length without ANSI color codes.

        :param str string: Input string.
        :return: Plain text line length.
        :rtype: int
        """

        ansi_escape = re.compile(r'\x1b[^m]*m')
        return len(ansi_escape.sub('', string))

    def format(self, record):
        """
        Format a log record for output.

        Uses a colorized format on TTY and falls back to the base stream handler
        formatting for non-TTY output.

        :param logging.LogRecord record: Log record to format.
        :return: Formatted log message.
        :rtype: str
        """

        if self.is_tty:
            message = self.colorize(record)
        else:
            message = logging.StreamHandler.format(self, record)

        return message
