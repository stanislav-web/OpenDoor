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
from queue import Empty as QueueEmptyError, Queue

# noinspection PyPep8Naming
from src.lib.tpl import Tpl as tpl
from .worker import Worker


class ThreadPool(object):

    """ThreadPool class"""

    JOIN_POLL_INTERVAL_SEC = 1.0
    JOIN_STALL_WARNING_SEC = 60.0
    PAUSE_PROMPT_DRAIN_TIMEOUT_SEC = 0.5
    PAUSE_PROMPT_DRAIN_POLL_SEC = 0.05

    def __init__(self, num_threads, total_items, timeout, stall_warning_interval=None):
        """
        Initialize thread pool
        :param int num_threads: active workers
        :param int total_items: total items
        :param int timeout: delay between threads
        :param int|float|None stall_warning_interval: worker stall warning interval
        """

        self.__queue = Queue()
        self.__workers = []
        self.__submitted = 0
        self.__worker_error = None
        self.__pause_requested = False
        self.__pause_lock = threading.RLock()
        self.__closed = False
        self.total_items_size = total_items
        self.is_started = True
        self.__stall_warning_interval = self.__normalize_stall_warning_interval(stall_warning_interval)

        for _ in range(num_threads):

            worker = Worker(self.__queue, num_threads, timeout)
            if hasattr(worker, 'set_error_callback'):
                worker.set_error_callback(self.__record_worker_error)
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

        if True is not self.is_started or self.__closed is True:
            return

        if self.__submitted >= self.total_items_size:
            return

        self.__pause_if_requested()

        if True is not self.is_started or self.__closed is True:
            return

        self.__enqueue_with_pause_resume(func, args, kargs)

    def __enqueue_with_pause_resume(self, func, args, kargs):
        """
        Enqueue a task and preserve it across the runtime pause prompt.

        If Ctrl+C is pressed while the main thread is submitting a task, the
        pause prompt must not silently drop the current queue item when the user
        continues the scan.

        :param func func: callback function
        :param tuple args: callback positional arguments
        :param dict kargs: callback keyword arguments
        :raise KeyboardInterrupt: when the user aborts from the pause prompt
        :return: None
        """

        while True:
            try:
                self.__queue.put((func, args, kargs))
                self.__submitted += 1
                return
            except (SystemExit, KeyboardInterrupt):
                self.pause()


    def request_pause(self):
        """
        Request the regular runtime pause prompt from another thread.

        Worker threads must not show the interactive prompt directly because an
        abort answer raises ``KeyboardInterrupt`` outside the main scan thread.
        This method only marks the pool as pause-requested and pauses workers
        before their next queued task. ``add()`` or ``join()`` will show the
        existing prompt on the controlling thread.

        :return: True when a new pause request was registered
        :rtype: bool
        """

        with self.__pause_lock:
            if self.__pause_requested is True or self.is_started is not True:
                return False

            self.__pause_requested = True

        for worker in self.__workers:
            worker.pause()

        return True

    def __pause_if_requested(self):
        """Open the regular pause menu when a worker requested it.

        :raise KeyboardInterrupt: when the user aborts from the pause prompt
        :return: None
        """

        with self.__pause_lock:
            requested = self.__pause_requested is True

        if requested is True:
            self.pause()

    def join(self):
        """
        Join queue and periodically warn when workers stop making progress.

        :raise Exception: first fatal exception reported by a worker
        :return: None
        """

        self.__raise_worker_error_if_any()

        last_completed = self.completed_size
        last_queue_size = self.size
        last_activity_at = time.monotonic()
        last_warning_at = last_activity_at
        last_active_signature = self.__active_tasks_signature()

        with self.__queue.all_tasks_done:
            while int(getattr(self.__queue, 'unfinished_tasks', 0) or 0) > 0:
                self.__pause_if_requested()

                try:
                    self.__queue.all_tasks_done.wait(timeout=self.JOIN_POLL_INTERVAL_SEC)
                except (SystemExit, KeyboardInterrupt):
                    self.pause()
                    continue

                self.__pause_if_requested()
                self.__raise_worker_error_if_any()

                completed = self.completed_size
                queue_size = self.__queue._qsize()
                active_signature = self.__active_tasks_signature()
                if (
                    completed != last_completed
                    or queue_size != last_queue_size
                    or active_signature != last_active_signature
                ):
                    last_completed = completed
                    last_queue_size = queue_size
                    last_active_signature = active_signature
                    last_activity_at = time.monotonic()
                    continue

                now = time.monotonic()
                if (now - last_activity_at >= self.__stall_warning_interval
                        and now - last_warning_at >= self.__stall_warning_interval):
                    tpl.warning(
                        msg='Slow item {0:.0f}s: {1} | done={2}/{3} queued={4}'.format(
                            now - last_activity_at,
                            self.__format_active_tasks(now),
                            completed,
                            self.submitted_size,
                            queue_size
                        )
                    )
                    last_warning_at = now

        self.__raise_worker_error_if_any()

    def __record_worker_error(self, error):
        """
        Store the first fatal worker exception for propagation on the main thread.

        Worker threads must not terminate the whole process directly. The main
        scan flow owns BrowserError handling, session checkpoints and final
        process exit semantics.

        :param Exception error: fatal worker exception
        :return: None
        """

        if self.__worker_error is None:
            self.__worker_error = error

    def __raise_worker_error_if_any(self):
        """
        Raise the first fatal worker exception, if any.

        :raise Exception: stored worker exception
        :return: None
        """

        if self.__worker_error is not None:
            raise self.__worker_error

    def close(self, join_timeout=1.0):
        """Stop worker threads and discard queued-but-not-started tasks.

        The CLI normally exits after a scan, but OpenDoor can also be used from
        tests or long-running Python processes. Worker threads block on the queue
        after work is drained, so they must receive explicit stop sentinels during
        cleanup.

        :param int|float join_timeout: maximum seconds to wait for each worker
        :return: None
        """

        if self.__closed is True:
            return

        self.__closed = True
        self.is_started = False
        self.__discard_pending_tasks()

        for worker in self.__workers:
            worker.resume()
            self.__queue.put(Worker.STOP_TASK)

        for worker in self.__workers:
            worker.join(timeout=float(join_timeout))

    def __discard_pending_tasks(self):
        """Drop queued tasks that have not started before pool shutdown.

        :return: None
        """

        while True:
            try:
                self.__queue.get_nowait()
            except QueueEmptyError:
                return
            else:
                self.__queue.task_done()

    @classmethod
    def __normalize_stall_warning_interval(cls, value):
        """
        Normalize worker stall warning interval.

        :param int|float|None value: configured interval
        :return: positive interval in seconds
        :rtype: float
        """

        try:
            interval = float(value)
        except (TypeError, ValueError):
            return float(cls.JOIN_STALL_WARNING_SEC)

        if interval <= 0:
            return float(cls.JOIN_STALL_WARNING_SEC)

        return interval

    def __active_tasks_signature(self):
        """
        Return a stable signature for active task heartbeat changes.

        :return: tuple describing active task progress
        :rtype: tuple
        """

        signature = []
        for task in self.active_tasks:
            signature.append((
                str(task.get('label') or ''),
                str(task.get('detail') or ''),
                float(task.get('last_activity_at') or task.get('started_at') or 0.0),
            ))

        return tuple(signature)

    def __wait_for_pause_prompt_drain(self):
        """
        Give in-flight worker output a short chance to drain before prompting.

        Runtime pause does not kill active requests. A worker can therefore
        finish and print its scan result right after Ctrl+C. Waiting briefly
        before showing the prompt keeps the prompt visible instead of letting it
        be interleaved with the last in-flight result.

        The wait is intentionally bounded so a slow or retrying request cannot
        hide the pause prompt indefinitely.

        :return: None
        """

        deadline = time.monotonic() + float(self.PAUSE_PROMPT_DRAIN_TIMEOUT_SEC)

        while len(self.active_tasks) > 0 and time.monotonic() < deadline:
            time.sleep(float(self.PAUSE_PROMPT_DRAIN_POLL_SEC))

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
            detail = str(task.get('detail') or '').strip()

            if detail:
                items.append('{0} [{1}]'.format(label, detail))
            else:
                items.append(label)

        if len(tasks) > 3:
            items.append('+{0} more'.format(len(tasks) - 3))

        return '; '.join(items)

    @staticmethod
    def normalize_runtime_pause_answer(answer):
        """
        Normalize runtime pause prompt answer.

        Runtime pause input must be tolerant to case, repeated key presses
        and keyboard layout mistakes where Cyrillic letters look like Latin ones.

        :param str answer: raw terminal answer
        :return: normalized runtime command
        """

        value = str(answer or '').strip().casefold()

        if len(value) <= 0:
            return ''

        aliases = {
            'c': 'C',
            'continue': 'C',
            'с': 'C',  # Cyrillic small es, visually similar to latin c.
            'e': 'E',
            'exit': 'E',
            'q': 'E',
            'quit': 'E',
            'е': 'E',  # Cyrillic small ie, visually similar to latin e.
        }

        if value in aliases:
            return aliases[value]

        first_char = value[0]

        return aliases.get(first_char, first_char)

    def pause(self):
        """
        Pause all pool workers and show the runtime continue/exit prompt.

        :raise KeyboardInterrupt: when the user chooses exit or interrupts the prompt
        :return: None
        """

        with self.__pause_lock:
            self.__pause_requested = False

        self.is_started = False
        tpl.info(key='stop_threads', threads=len(self.__workers))

        for worker in self.__workers:
            worker.pause()

        self.__wait_for_pause_prompt_drain()

        try:
            while True:
                option = self.normalize_runtime_pause_answer(tpl.prompt(key='option_prompt', newline=True))

                if option == 'E':
                    raise KeyboardInterrupt
                if option in ('C', ''):
                    self.resume()
                    return

                tpl.warning(key='unknown_pause_command')

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
