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

    Development: Stanislav WEB
"""

import threading
import time
from queue import Empty as QueueEmptyError
from threading import BoundedSemaphore, Event

from src.core import process
# noinspection PyPep8Naming
from src.lib.tpl import Tpl as tpl


class Worker(threading.Thread):

    """Worker class"""

    def __init__(self, queue, num_threads, timeout=0):
        """
        Init thread worker
        :param Queue.Queue queue: simple queue object
        :param int num_threads: threads numbers
        :param int timeout: delay timeout
        """

        super(Worker, self).__init__()
        self.__semaphore = BoundedSemaphore(num_threads)
        self.__event = Event()
        self.__event.set()
        self.__empty = False
        self.__running = True
        self.__queue = queue
        self.__timeout = timeout
        self.counter = 0
        self.completed = 0
        self.failed = 0
        self.__task_label = None
        self.__task_started_at = None

    def pause(self):
        """
        Pause current worker
        :return: None
        """

        self.__running = False
        self.__event.clear()

    def resume(self):
        """
        Resume current worker
        :return: None
        """

        self.__running = True
        self.__event.set()

    def run(self):
        """
        Run current worker
        :return: None
        """

        try:

            self.__event.wait()

            while self.__running:

                if 0 < self.__timeout:
                    time.sleep(self.__timeout)

                try:
                    self.__process()
                except QueueEmptyError:
                    self.__empty = True

                finally:
                    if not self.__event.is_set():
                        self.__semaphore.release()
                        self.__event.wait()
        except Exception as error:
            self.terminate(str(error))

    @property
    def active_task(self):
        """
        Return metadata for the task currently processed by this worker.

        :return: dict | None
        """

        if self.__task_label is None or self.__task_started_at is None:
            return None

        return {
            'label': self.__task_label,
            'started_at': self.__task_started_at,
        }

    @staticmethod
    def __build_task_label(args, kargs):
        """
        Build a compact human-readable label for diagnostics.

        :param tuple args: positional task arguments
        :param dict kargs: keyword task arguments
        :return: str
        """

        if len(args) > 0:
            return str(args[0])

        if isinstance(kargs, dict) and len(kargs) > 0:
            for key in sorted(kargs.keys()):
                return '{0}={1}'.format(key, kargs.get(key))

        return 'unknown task'

    def __process(self):
        """
        Task process
        :return: None
        """

        func, args, kargs = self.__queue.get(block=True)
        self.counter += 1
        self.__task_label = self.__build_task_label(args, kargs)
        self.__task_started_at = time.monotonic()

        try:
            func(*args, **kargs)
            self.completed += 1
        except Exception:
            self.failed += 1
            raise
        finally:
            self.__task_label = None
            self.__task_started_at = None
            self.__queue.task_done()

    @classmethod
    def terminate(cls, msg):
        """
        Terminate thread
        :param str msg: output message
        :return: None
        """

        tpl.error(msg)
        process.kill()
