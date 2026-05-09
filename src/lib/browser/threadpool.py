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

import time
from queue import Queue

# noinspection PyPep8Naming
from src.lib.tpl import Tpl as tpl
from .worker import Worker


class ThreadPool(object):

    """ThreadPool class"""

    JOIN_POLL_INTERVAL_SEC = 1.0
    JOIN_STALL_WARNING_SEC = 60.0

    def __init__(self, num_threads, total_items, timeout):
        """
        Initialize thread pool
        :param int num_threads: active workers
        :param int total_items: total items
        :param int timeout: delay between threads
        """

        self.__queue = Queue()
        self.__workers = []
        self.__submitted = 0
        self.total_items_size = total_items
        self.is_started = True

        for _ in range(num_threads):

            worker = Worker(self.__queue, num_threads, timeout)
            if False is worker.is_alive():
                worker.daemon = True
                worker.start()
                self.__workers.append(worker)

    @property
    def size(self):
        """
        Get pool size
        :return: int
        """

        return self.__queue.qsize()

    @property
    def workers_size(self):
        """
        Get pool workers (threads)
        :return: int
        """

        return self.__workers.__len__()

    @property
    def items_size(self):
        """
        Get pool processed items size
        :return: int
        """

        counter = 0
        for worker in self.__workers:
            counter += worker.counter
        return counter

    @property
    def submitted_size(self):
        """
        Get pool submitted items size
        :return: int
        """

        return self.__submitted

    @property
    def completed_size(self):
        """
        Get completed task count across workers.

        :return: int
        """

        counter = 0
        for worker in self.__workers:
            counter += int(getattr(worker, 'completed', 0) or 0)
        return counter

    @property
    def active_tasks(self):
        """
        Get active worker task metadata for diagnostics.

        :return: list[dict]
        """

        tasks = []
        for worker in self.__workers:
            task = getattr(worker, 'active_task', None)
            if isinstance(task, dict):
                tasks.append(task)
        return tasks

    def extend_total_items(self, amount):
        """
        Extend allowed submitted items size.

        :param int amount:
        :return: None
        """

        if int(amount) > 0:
            self.total_items_size += int(amount)

    def add(self, func, *args, **kargs):
        """
        Add a task to the queue
        :param func func: callback function
        :param dict args: arguments
        :param kargs: keys arguments
        :return: None
        """

        try:
            if True is self.is_started:
                if self.__submitted < self.total_items_size:
                    self.__queue.put((func, args, kargs))
                    self.__submitted += 1
        except (SystemExit, KeyboardInterrupt):
            self.pause()

    def join(self):
        """
        Join queue and periodically warn when workers stop making progress.

        :return: None
        """

        last_completed = self.completed_size
        last_queue_size = self.size
        last_activity_at = time.monotonic()
        last_warning_at = last_activity_at

        with self.__queue.all_tasks_done:
            while int(getattr(self.__queue, 'unfinished_tasks', 0) or 0) > 0:
                try:
                    self.__queue.all_tasks_done.wait(timeout=self.JOIN_POLL_INTERVAL_SEC)
                except (SystemExit, KeyboardInterrupt):
                    self.pause()
                    continue

                completed = self.completed_size
                queue_size = self.__queue._qsize()
                if completed != last_completed or queue_size != last_queue_size:
                    last_completed = completed
                    last_queue_size = queue_size
                    last_activity_at = time.monotonic()
                    continue

                now = time.monotonic()
                if (now - last_activity_at >= self.JOIN_STALL_WARNING_SEC
                        and now - last_warning_at >= self.JOIN_STALL_WARNING_SEC):
                    tpl.warning(
                        msg='Scan worker has not completed a request for {0:.0f}s. '
                            'submitted={1}, completed={2}, queue={3}, active={4}'.format(
                                now - last_activity_at,
                                self.submitted_size,
                                completed,
                                queue_size,
                                self.__format_active_tasks(now)
                            )
                    )
                    last_warning_at = now

    def __format_active_tasks(self, now):
        """
        Format active worker tasks for join watchdog diagnostics.

        :param float now: current monotonic timestamp
        :return: str
        """

        tasks = self.active_tasks
        if len(tasks) == 0:
            return 'none'

        items = []
        for task in tasks[:3]:
            label = str(task.get('label') or 'unknown task')
            started_at = float(task.get('started_at') or now)
            age = max(0.0, now - started_at)
            items.append('{0} ({1:.0f}s)'.format(label, age))

        if len(tasks) > 3:
            items.append('+{0} more'.format(len(tasks) - 3))

        return '; '.join(items)

    def pause(self):
        """
        Pause all pool workers and show the runtime continue/exit prompt.

        :raise KeyboardInterrupt: when the user chooses exit or interrupts the prompt
        :return: None
        """

        self.is_started = False
        tpl.info(key='stop_threads', threads=len(self.__workers))

        for worker in self.__workers:
            worker.pause()

        try:
            while True:
                char = tpl.prompt(key='option_prompt')
                option = str(char or '').strip().lower()

                if option in ('e', 'q'):
                    raise KeyboardInterrupt
                if option in ('c', ''):
                    self.resume()
                    return

        except (SystemExit, KeyboardInterrupt):
            raise KeyboardInterrupt

    def resume(self):
        """
        Resume threadpool
        :return: None
        """

        if False is self.is_started:
            tpl.info(key='resume_threads')
            for worker in self.__workers:
                worker.resume()
            self.is_started = True