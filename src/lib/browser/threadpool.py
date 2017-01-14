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

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""

    def __init__(self, num_threads):
        """
        Initialize thread pool

        :param int num_threads:
        :return None
        """

        self.queue = Queue(num_threads)
        self.counter = 0
        for _ in range(num_threads): Worker(self.queue)

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

        return self.counter

    def add(self, func, *args, **kargs):
        """
        Add a task to the queue

        :param func func: callback function
        :param dict args: arguments
        :param kargs: key arguments
        :return: None
        """
        self.counter += 1
        try:
            self.queue.put((func, args, kargs))
        except (SystemExit, KeyboardInterrupt) as e:
            print "Exit"


    def complete(self):
        """
        Wait for completion of all the tasks in the queue

        :return: None
        """
        self.queue.join()
