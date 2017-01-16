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

import threading

class ThreadControl():
    """ThreadControl class"""

    def __init__(self):
        """
        Init lockers
        """
        self.condition = threading.Condition(threading.Lock())
        self.paused = False

    def wait(self):
        """
        If in sleep, we acquire immediately, otherwise we wait for thread
        to release condition. In race, worker will still see self.paused
        and begin waiting until it's set back to False
        :return: None
        """

        self.condition.wait()

    def stop(self):
        """
        If in sleep, we acquire immediately, otherwise we wait for thread
        to release condition. In race, worker will still see self.paused
        and begin waiting until it's set back to False
        :return: None
        """

        self.paused = True
        self.condition.acquire()
        return self.condition

    def resume(self):
        """
        Resume thread
        Notify so thread will wake after lock released
        Now release the lock
        :return: None
        """

        self.paused = False
        self.condition.notify()
        self.condition.release()

    @property
    def is_stopped(self):
        return self.paused

