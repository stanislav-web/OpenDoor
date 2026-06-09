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
from threading import Event

from src.core import process
# noinspection PyPep8Naming
from src.lib.tpl import Tpl as tpl


class Worker(threading.Thread):

    """Worker class"""

    STOP_TASK = object()

    def __init__(self, queue, num_threads, timeout=0, error_callback=None):
        """
        Init thread worker
        :param Queue.Queue queue: simple queue object
        :param int num_threads: threads numbers
        :param int timeout: delay timeout
        :param callable|None error_callback: optional fatal worker error callback
        """

        super(Worker, self).__init__()
        self.__event = Event()
        self.__event.set()
        self.__empty = False
        self.__running = True
        self.__queue = queue
        self.__timeout = timeout
        self.__error_callback = error_callback
        self.counter = 0
        self.completed = 0
        self.failed = 0
        self.__task_label = None
        self.__task_started_at = None
        self.__task_last_activity_at = None
        self.__task_detail = None

    def set_error_callback(self, error_callback):
        """
        Set fatal worker error callback.

        :param callable|None error_callback: callback receiving the raised exception
        :return: None
        """

        self.__error_callback = error_callback

    def pause(self):
        """
        Pause current worker before it starts the next queued task.

        A pause must not mark the worker as stopped. The worker may currently be
        processing a request; after that request finishes it will block on the
        event until the pool resumes it.

        :return: None
        """

        self.__event.clear()

    def resume(self):
        """
        Resume current worker.

        :return: None
        """

        self.__event.set()

    def run(self):
        """
        Run current worker
        :return: None
        """

        try:

            while self.__running:

                self.__event.wait()

                if 0 < self.__timeout:
                    time.sleep(self.__timeout)

                try:
                    self.__process()
                except QueueEmptyError:
                    self.__empty = True

        except Exception as error:
            self.__running = False
            if callable(self.__error_callback):
                self.__error_callback(error)
            else:
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
            'last_activity_at': self.__task_last_activity_at or self.__task_started_at,
            'detail': self.__task_detail,
        }

    def touch_active_task(self, detail=None):
        """
        Mark progress inside a long-running queued task.

        Header-bypass and active sniffer probes can perform many subrequests while
        the queue item itself is still active. The pool watchdog uses this heartbeat
        to avoid reporting false stalls.

        :param str|None detail: optional human-readable sub-step label
        :return: None
        """

        if self.__task_label is None:
            return

        self.__task_last_activity_at = time.monotonic()
        if detail is not None:
            self.__task_detail = str(detail)

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

        task = self.__queue.get(block=True)
        if task is self.STOP_TASK:
            self.__running = False
            self.__queue.task_done()
            return

        func, args, kargs = task
        self.counter += 1
        self.__task_label = self.__build_task_label(args, kargs)
        self.__task_started_at = time.monotonic()
        self.__task_last_activity_at = self.__task_started_at
        self.__task_detail = None

        try:
            func(*args, **kargs)
            self.completed += 1
        except Exception:
            self.failed += 1
            raise
        finally:
            self.__task_label = None
            self.__task_started_at = None
            self.__task_last_activity_at = None
            self.__task_detail = None
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
