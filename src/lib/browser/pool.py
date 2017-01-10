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
from threading import Thread

class Pool:
    """Pool class"""

    def __init__(self, threads):
        self.queue = Queue()
        self.threads = threads

    def get_pool_instance(self):
        return self

    def add_to_queue(self, item):
        self.queue.put(item)

    def queue_join(self):
        self.queue.join()

    def count_in_queue(self):
        return self.queue.qsize()

    def read_from_queue(self, process):
        self.callback = process

        for i in range(self.threads):
            worker = Thread(target=self.process_queue, args=(i, self.queue))
            worker.setDaemon(True)
            worker.start()
        self.queue_join()

    def process_queue(self, i, q):

        while not q.empty():  # check that the queue isn't empty
            print '%s: Looking for the next enclosure' % i
            item = q.get()  # get the item from the queue
            print '%s: Downloading:' % i, item
            self.callback(item)
            q.task_done()

