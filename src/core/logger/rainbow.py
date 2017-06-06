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

from .colorize import ColorizingStreamHandler
from src.core.system import Term


class RainbowLoggingHandler(ColorizingStreamHandler):

    """ Class RainbowLoggingHandler """

    # Define color for message payload
    level_map = {
        logging.DEBUG: ('cyan', False),
        logging.INFO: ('white', False),
        logging.WARNING: ('yellow', False),
        logging.ERROR: ('red', True),
        logging.CRITICAL: ('red', True)
    }

    date_format = "%H:%M:%S"

    #: How many characters reserve to function name logging
    who_padding = 7

    def get_color(self, fg=None, bold=False):
        """
        Construct a terminal color code
        :param str fg: Symbolic name of foreground color
        :param bool bold: Brightness bit
        """

        params = []

        if fg in self.color_map:
            params.append(str(self.color_map[fg] + 30))
        if bold:
            params.append('1')

        color_code = ''.join((self.csi, ';'.join(params), 'm'))

        return color_code

    def colorize(self, record):
        """
        Get a special format string with ASCII color codes
        :param dict|None record: logging record
        :return: str
        """

        # Dynamic message color based on logging level
        if not hasattr(record, 'levelno'):
            record.levelno = 20
        fg, bold = self.level_map[record.levelno]

        template = [
            "[", self.get_color("black"),
            "%(asctime)s", self.reset, "] ",
            "",
            "",
            "%(padded_who)s", self.reset, " ", self.get_color(fg, bold), "%(message)s", self.reset]

        format_string = "".join(template)

        who = [self.get_color("green"), getattr(record, "funcName", ""), self.get_color("black", True), ":",
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

        formatter = logging.Formatter(format_string, self.date_format)
        output = formatter.format(record)
        # Clean cache so the color codes of traceback don't leak to other formatters
        record.ext_text = None
        # noinspection PyUnresolvedReferences
        width = int(Term.terminal_size['width'])
        pure_length = self.__pure_line_len(output)
        length = width - pure_length
        if record.levelno != logging.DEBUG:
            if pure_length > width and record.levelno != logging.ERROR:
                output = (output[:width] + '...')

        end = (' ' * length)[:length]
        return output + end

    @classmethod
    def __pure_line_len(cls, string):
        """
        Get pure line
        :param str string: input string
        :return: str
        """

        ansi_escape = re.compile(r'\x1b[^m]*m')
        return len(ansi_escape.sub('', string))

    def format(self, record):
        """
        Formats a record for output.
        Takes a custom formatting path on a terminal.
        :param dict record: input record logging
        :return: str
        """

        if self.is_tty:
            message = self.colorize(record)
        else:
            message = logging.StreamHandler.format(self, record)

        return message
