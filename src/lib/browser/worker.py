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
from .signals import ThreadWatchHandler
import signal

class Worker(threading.Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, queue):
        """
        Init thread worker

        :param Queue.Queue queue:
        """

        threading.Thread.__init__(self)

        self.resume = threading.Event()
        self.pause = threading.Event()
        self.busy = threading.Event()
        self.close = threading.Event()


        # Explicitly using Lock over RLock since the use of self.paused
        # break reentrancy anyway, and I believe using Lock could allow
        # one thread to pause the worker, while another resumes; haven't
        # checked if Condition imposes additional limitations that would
        # prevent that. In Python 2, use of Lock instead of RLock also
        # boosts performance.
        self.pause_cond = threading.Condition(threading.Lock())

        self.queue = queue
        self.setDaemon(True)
        self.start()

    def pause(self):
        """
        If in sleep, we acquire immediately, otherwise we wait for thread
        to release condition. In race, worker will still see self.paused
        and begin waiting until it's set back to False
        :return: None
        """

        self.paused = True
        self.pause_cond.acquire()

    def resume(self):
        """
        Resume thread
        Notify so thread will wake after lock released
        Now release the lock
        :return: None
        """

        self.paused = False
        self.pause_cond.notify()
        self.pause_cond.release()

    def run(self):
        """
        Run current worker
        :return: None
        """

        with ThreadWatchHandler() as watcher:
            while True:
                # if watcher.interrupted:
                #     print "Thread {exit} exiting"

                try:
                    func, args, kargs = self.queue.get()
                except QueueEmptyError:
                    continue

                func(*args, **kargs)
                self.queue.task_done()



