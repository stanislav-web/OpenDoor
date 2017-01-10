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
from Queue import LifoQueue
from threading import Thread

class Pool:
    """Pool class"""

    def __init__(self):
        self.queue = LifoQueue()

    def get_pool_instance(self):
        return self

    def set_pool_threads(self, threads):
        self.threads = threads

    def add_to_queue(self, item):
        self.queue.put(item)

    def join_to_queue(self):
        self.queue.join()

    def count_in_queue(self):
        return self.queue.qsize()

    def read_from_queue(self):
        for i in range(self.threads):
            t1 = Thread(target=self._process)
            t1.start()

    def process_queue(self):
        while not self.queue.empty():  # check that the queue isn't empty

            item = self.queue.get()  # get the item from the queue
            print item
            self.queue.task_done()  # specify that you are done with the item