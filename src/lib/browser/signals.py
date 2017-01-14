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

    Development Team: Stanislav Menshov
"""
import signal

class ThreadWatchHandler(object):
    """ ThreadWatchHandler class """

    def __init__(self, sig=signal.SIGINT):
        """
        Define keyboard iterrupt signal
        :param int sig:
        """
        self.sig = sig

    def __enter__(self):
        """
        Init keyboard interception handler using with "with()" statement

        :return: ThreadPauseHandler

        """

        self.interrupted = False
        self.released = False

        self.original_handler = signal.getsignal(self.sig)

        def handler(signum, frame):
            self.release()
            self.interrupted = True

        if True is self.is_main_thread():
            signal.signal(self.sig, handler)

        return self

    def __exit__(self, type, value, tb):
        """
        It will be called after the interception

        :param type:
        :param value:
        :param tb:
        :return: bool
        """
        self.release()

    def is_main_thread(self):
        """
        Only Main Thread can handle signals

        :return: bool
        """

        try:
            signal.signal(signal.SIGINT, signal.SIG_DFL)
        except ValueError:
            return False
        return True

    def release(self):
        """
        Release interceptor


        :return: bool
        """

        if self.released:
            return False

        if True is self.is_main_thread():
            signal.signal(self.sig, self.original_handler)

        self.released = True

        return True