# -*- coding: utf-8 -*-

"""Debug classes """

from src.core import sys
from src.lib import tpl

class Debug:
    """Debug class"""

    def __init__(self):
        if 0 < self._debug:
            tpl.debug(key='debug', level=self._debug)
        pass


    def _debug_user_agents(self):
        if 0 >= self._debug:
            pass
        else:
            if True is self._is_random_user_agent:
                tpl.debug(key='random_browser')
            else:
                tpl.debug(key='browser', browser=self._user_agent)


    def _debug_proxy(self):
        if 0 >= self._debug:
            pass
        else:
            if True is self._is_proxy:
                tpl.debug(key='proxy')

    def _debug_list(self):
        if 0 >= self._debug:
            pass
        else:
            if self._default_scan is self._scan:
                tpl.debug(key='directories')
            else :
                tpl.debug(key='subdomains')


    def _debug_line(self, line):
        if 0 >= self._debug:
            tpl.line(line)
        else:
            tpl.info(line)

