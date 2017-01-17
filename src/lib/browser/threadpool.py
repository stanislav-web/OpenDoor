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
import time
import threading
from Queue import Queue
from .worker import Worker
from .exceptions import WorkerError
from .exceptions import ThreadPoolError
from src.lib import tpl

class ThreadPool():
    """ThreadPool class"""

    def __init__(self, num_threads, total_items):
        """
        Initialize thread pool

        :param int num_threads:
        :return None
        """

        self.__queue = Queue(num_threads)
        self.workers = []
        self.total_items_sizes = total_items
        self.is_pool_started = True

        try:
            for _ in range(num_threads):

                try:

                    worker = Worker(self.__queue)

                    if False is worker.isAlive():
                        worker.setDaemon(True)
                        worker.start()
                        self.workers.append(worker)

                except Exception as e:
                    raise WorkerError(e)
        except WorkerError as e:
            raise ThreadPoolError(e)

    @property
    def pool_items_size(self):
        """
        Get pool items size

        :return: int
        """
        counter = 0
        for worker in self.workers:
            counter += worker.counter
        return counter

    def add(self, func, *args, **kargs):
        """
        Add a task to the queue

        :param func func: callback function
        :param dict args: arguments
        :param kargs: key arguments
        :return: None
        """

        try:
            if True is self.is_pool_started:
                if self.pool_items_size < self.total_items_sizes:
                    self.__queue.put((func, args, kargs))
                else:
                    self.__queue.join()
        except (SystemExit, KeyboardInterrupt):
           self.pause()

    def pause(self):
        """
        ThreadPool pause
        :raise KeyboardInterrupt
        :return: None
        """

        self.is_pool_started = False
        tpl.message('\n')
        tpl.info(key='stop_threads', threads=len(self.workers))

        try:
            while 0 < threading.active_count():
                if False is self.is_pool_started and False:
                    for worker in threading._enumerate():
                        if threading.current_thread().__class__.__name__ != '_MainThread':
                            worker.pause()
                    time.sleep(3)


                char = tpl.prompt(key='option_prompt')
                if char.lower() == 'e':
                    raise KeyboardInterrupt
                elif char.lower() == 'c':
                    self.resume()
                    break
                else:
                    continue

        except (SystemExit, KeyboardInterrupt):
            raise KeyboardInterrupt

    def resume(self):
        """
        Resume threadpool

        :return: None
        """

        if False is self.is_pool_started:
            tpl.info(key='resume_threads')
            for worker in self.workers:
                worker.resume()
            self.is_pool_started = True
        pass