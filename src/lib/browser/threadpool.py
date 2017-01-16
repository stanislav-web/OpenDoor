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

from Queue import Queue
from .worker import Worker
from .exceptions import WorkerError
from .exceptions import ThreadPoolError

from src.lib import tpl
from src.core import sys

class ThreadPool():
    """ThreadPool class"""

    def __init__(self, num_threads):
        """
        Initialize thread pool

        :param int num_threads:
        :return None
        """

        self.queue = Queue(num_threads)
        self.workers = []

        self.__is_pool_started = True

        try:
            for _ in range(num_threads):

                try:

                    worker = Worker(self.queue)

                    if False is worker.isAlive():
                        worker.daemon = True
                        worker.start()
                        self.workers.append(worker)

                except Exception as e:
                    raise WorkerError(e)
        except WorkerError as e:
            raise ThreadPoolError(e)

    @property
    def get_queue_instance(self):
        """
        Get queue instance

        :return: Queue
        """

        return self.queue

    @property
    def get_pool_items_size(self):
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
            self.queue.put((func, args, kargs))
        except (SystemExit, KeyboardInterrupt):
           self.pause()


    def complete(self):
        """
        Wait for completion of all the tasks in the queue

        :return: None
        """
        self.queue.join()

    def pause(self):
        """
        ThreadPool pause

        :return:
        """

        tpl.info(key='pause_threads')
        for worker in self.workers:
            worker.stop()

        try:
            if True is self.__is_pool_started:
                self.__is_pool_started = False

            while True:
                char = tpl.prompt(key='option_prompt')
                if char.lower() == 'e':
                    raise KeyboardInterrupt
                elif char.lower() == 'c':
                    self.resume()
                    return
                else:
                    continue
        except (SystemExit, KeyboardInterrupt):
            raise KeyboardInterrupt

    def resume(self):
        """
        Resume threadpool

        :return: None
        """

        if False is self.__is_pool_started:
            tpl.info(key='resume_threads')
            for worker in self.workers:
                worker.resume()
            self.__is_pool_started = True
        pass