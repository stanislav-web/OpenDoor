# -*- coding: utf-8 -*-

"""Color class"""

from .exceptions import ColorError

class Color:
    """Color class"""

    # Special END separator
    END = '0e8ed89a-47ba-4cdb-938e-b8af8e084d5c'

    # Text attributes
    ALL_OFF = '\033[0m'
    BOLD = '\033[1m'
    UNDERSCORE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    CONCEALED = '\033[7m'

    # Foreground colors
    FG_BLACK = '\033[30m'
    FG_RED = '\033[31m'
    FG_GREEN = '\033[32m'
    FG_YELLOW = '\033[33m'
    FG_BLUE = '\033[34m'
    FG_MAGENTA = '\033[35m'
    FG_CYAN = '\033[36m'
    FG_WHITE = '\033[37m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    @staticmethod
    def colored(self, msg, *attr):
        style = ''.join(attr)
        return '{}{}{}'.format(style, msg.replace(Color.END, Color.ALL_OFF + style), Color.ALL_OFF)

