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
from .exceptions import WorkerError
from .threadcontrol import ThreadControl

class Worker(threading.Thread):
    """Worker class"""

    def __init__(self, queue):

        """
        Init thread worker

        :param Queue.Queue queue:
        """

        super(Worker, self).__init__()
        self.stoprequest = threading.Event()
        self.queue = queue
        self.counter = 0

    def stop(self, timeout=None):
        self.stoprequest.set()
        super(Worker, self).join(timeout)

    def run(self):

        """
        Run current worker

        :return: None
        """

        while not self.stoprequest.isSet():

            try:
                func, args, kargs = self.queue.get()
                self.counter +=1
                func(*args, **kargs)
                self.queue.task_done()
            except QueueEmptyError:
                break



