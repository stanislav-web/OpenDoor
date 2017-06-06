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
import subprocess
from .exceptions import CoreSystemError
from .terminal import Terminal


class Process(object):

    """ Process class"""

    def __init__(self, classname=None, typeobj=None, params=None):
        """
        Init metaclass
        :param classname: passed classname
        :param str typeobj: passed classname type
        :param dict params: passed params
        """

        del classname, typeobj, params
        self.ts = None

    @property
    def terminal_size(self):
        """
        Get terminal window size
        :raise CoreSystemError
        :return: dict
        """

        if getattr(self, 'ts', None) is None:
            (width, height) = Terminal().get_ts()
            self.ts = {'height': height, 'width': width}
        return self.ts

    @staticmethod
    def termination_handler():
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

            del signum
            del frame

            os.kill(os.getpid(), signal.SIGTERM)

        sig = getattr(signal, 'SIGTSTP', signal.SIGABRT)
        signal.signal(sig, kill_process)

    @staticmethod
    def kill():
        """
        Immediatelly terminate process
        :return: None
        """

        os.kill(os.getpid(), signal.SIGTERM)  # or signal.SIGKILL

    @staticmethod
    def execute(process):
        """
        Excecute OS process
        :param str process: os command
        :raise CoreSystemError
        :return: dic
        """

        try:
            pr = subprocess.Popen(process, cwd=os.getcwd(), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (out, error) = pr.communicate()
            if pr.returncode != 0:
                raise OSError(error.strip())

            return out
        except (subprocess.CalledProcessError, OSError) as error:
            raise CoreSystemError(error)


class Term(metaclass=Process):
    """Term class"""

    __metaclass__ = None
    pass
