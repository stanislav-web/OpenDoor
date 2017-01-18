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

import os
import signal


class MainHandler:
    """MainHandler class"""

    @staticmethod
    def termation_handler():
        """
        Exit Ctrl-Z handler
        :return: None
        """

        def kill_process(signum, frame):
            """
            Kill process os signal
            :param int signum: signal code
            :param object frame: frame object
            :return: None
            """

            os.kill(os.getpid(), signal.SIGTERM)

        signal.signal(signal.SIGTSTP, kill_process)
        pass
