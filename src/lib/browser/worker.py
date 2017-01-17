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

from Queue import Empty as QueueEmptyError
from threading import Semaphore, Event

class Worker(threading.Thread):
    """Worker class"""

    def __init__(self, queue):

        """
        Init thread worker

        :param Queue.Queue queue:
        """

        super(Worker, self).__init__()

        self.__semaphore = Semaphore(0)
        self.__event = Event()
        self.__event.set()

        self.queue = queue
        self.counter = 0

    def pause(self):
        """
        Pause current worker

        :return: None
        """

        self.__event.clear()
        if True is self.isAlive():
            self.__semaphore.acquire()

    def resume(self):
        """
        Resume current worker

        :return: None
        """

        self.running = True
        self.__event.set()

    def run(self):
        """
        Run current worker

        :return: None
        """

        self.__event.wait()

        while self.__event.isSet():

            try:
                func, args, kargs = self.queue.get()
                self.counter +=1
                func(*args, **kargs)
                self.queue.task_done()
            except QueueEmptyError:
                break
            finally:
                if not self.__event.isSet():
                    self.__semaphore.release()
                    self.__event.wait()



