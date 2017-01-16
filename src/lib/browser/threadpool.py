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
           self.stop()


    def complete(self):
        """
        Wait for completion of all the tasks in the queue

        :return: None
        """
        self.queue.join()

    def stop(self):

        tpl.info(key='stop_threads')
        for worker in self.workers:
            if True is worker.isAlive():
                worker.join()
            else:
                break

        # start = tpl.prompt(key='resume_threads')
        # if start:
        #     print 'OK'
        start = raw_input('RESUME')
        if start:
            print 'OK'

