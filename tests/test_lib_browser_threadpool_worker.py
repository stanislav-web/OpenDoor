# -*- coding: utf-8 -*-

import unittest
from queue import Queue, Empty as QueueEmptyError
from unittest.mock import MagicMock, patch

from src.lib.browser.threadpool import ThreadPool
from src.lib.browser.worker import Worker


class FakeWorker(object):
    def __init__(self, queue, num_threads, timeout):
        self.queue = queue
        self.num_threads = num_threads
        self.timeout = timeout
        self.daemon = False
        self.counter = 0
        self.started = False
        self.paused = False
        self.resumed = False
        self.alive = False

    def is_alive(self):
        return self.alive

    def start(self):
        self.started = True

    def pause(self):
        self.paused = True

    def resume(self):
        self.resumed = True


class MainThreadLike(object):
    pass


class BackgroundLike(object):
    pass


MainThreadLike.__name__ = '_MainThread'
BackgroundLike.__name__ = 'Background'


class TestBrowserThreadpoolWorkerExtra(unittest.TestCase):
    """TestBrowserThreadpoolWorkerExtra class."""

    def test_threadpool_skips_alive_workers(self):
        """ThreadPool.__init__() should ignore already-alive workers."""

        worker = FakeWorker(None, 0, 0)
        worker.alive = True

        with patch('src.lib.browser.threadpool.Worker', return_value=worker):
            pool = ThreadPool(num_threads=1, total_items=5, timeout=0)

        self.assertEqual(pool.workers_size, 0)

    def test_add_respects_started_and_total_limits(self):
        """ThreadPool.add() should skip queueing when paused or when submission limit is reached."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        queue_mock = getattr(pool, '_ThreadPool__queue')

        with patch.object(queue_mock, 'put', return_value=None) as put_mock:
            pool.add(lambda: None)
            pool.add(lambda: None)
            self.assertEqual(put_mock.call_count, 1)

        pool.is_started = False
        with patch.object(queue_mock, 'put', return_value=None) as put_mock:
            pool.add(lambda: None)
            put_mock.assert_not_called()

    def test_add_calls_pause_on_keyboard_interrupt(self):
        """ThreadPool.add() should sleep and pause when queue.put() is interrupted."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=5, timeout=0)

        queue_mock = getattr(pool, '_ThreadPool__queue')

        with patch.object(queue_mock, 'put', side_effect=KeyboardInterrupt), \
                patch('src.lib.browser.threadpool.time.sleep') as sleep_mock, \
                patch.object(pool, 'pause') as pause_mock:
            pool.add(lambda: None)

        sleep_mock.assert_called_once_with(2)
        pause_mock.assert_called_once_with()

    def test_threadpool_add_uses_submitted_counter_not_processed_items(self):
        """ThreadPool.add() should limit queue submissions using submitted_size."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=2, timeout=0)

        queue_mock = getattr(pool, '_ThreadPool__queue')

        with patch.object(queue_mock, 'put', return_value=None) as put_mock:
            pool.add(lambda: None)
            pool.add(lambda: None)
            pool.add(lambda: None)

        self.assertEqual(put_mock.call_count, 2)
        self.assertEqual(pool.submitted_size, 2)

    def test_threadpool_items_size_still_reports_processed_worker_counters(self):
        """ThreadPool.items_size should still reflect processed worker counters."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=2, total_items=5, timeout=0)

        workers = getattr(pool, '_ThreadPool__workers')
        workers[0].counter = 3
        workers[1].counter = 4

        self.assertEqual(pool.items_size, 7)

    def test_pause_resumes_on_c_and_can_pause_workers(self):
        """ThreadPool.pause() should pause workers and resume on 'c'."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=5, timeout=0)

        worker = MagicMock()
        setattr(pool, '_ThreadPool__workers', [worker])

        with patch('src.lib.browser.threadpool.tpl.info') as info_mock, \
                patch('src.lib.browser.threadpool.tpl.prompt', side_effect=['x', 'c']), \
                patch('src.lib.browser.threadpool.time.sleep'), \
                patch('src.lib.browser.threadpool.threading.active_count', side_effect=[1, 1]), \
                patch('src.lib.browser.threadpool.threading.enumerate', return_value=[worker]), \
                patch('src.lib.browser.threadpool.threading.current_thread', return_value=BackgroundLike()):
            pool.pause()

        self.assertTrue(worker.pause.called)
        self.assertTrue(worker.resume.called)
        self.assertTrue(pool.is_started)
        self.assertTrue(info_mock.called)

    def test_pause_raises_keyboard_interrupt_on_e(self):
        """ThreadPool.pause() should raise KeyboardInterrupt on 'e'."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=5, timeout=0)

        with patch('src.lib.browser.threadpool.tpl.info'), \
                patch('src.lib.browser.threadpool.tpl.prompt', return_value='e'), \
                patch('src.lib.browser.threadpool.time.sleep'), \
                patch('src.lib.browser.threadpool.threading.active_count', return_value=1), \
                patch('src.lib.browser.threadpool.threading.enumerate', return_value=[]), \
                patch('src.lib.browser.threadpool.threading.current_thread', return_value=MainThreadLike()):
            with self.assertRaises(KeyboardInterrupt):
                pool.pause()

    def test_worker_resume_and_process_and_terminate(self):
        """Worker should resume, process a task and terminate via helpers."""

        queue = Queue(1)
        result = []
        worker = Worker(queue, num_threads=1, timeout=0)

        worker.pause()
        self.assertFalse(getattr(worker, '_Worker__running'))

        worker.resume()
        self.assertTrue(getattr(worker, '_Worker__running'))

        queue.put((result.append, ('ok',), {}))
        worker._Worker__process()

        self.assertEqual(result, ['ok'])
        self.assertEqual(worker.counter, 1)

        with patch('src.lib.browser.worker.tpl.error') as error_mock, \
                patch('src.lib.browser.worker.process.kill') as kill_mock:
            Worker.terminate('boom')

        error_mock.assert_called_once_with('boom')
        kill_mock.assert_called_once_with()

    def test_worker_run_sets_empty_and_releases_on_pause(self):
        """Worker.run() should mark queue empty and release semaphore when paused."""

        worker = Worker(Queue(1), num_threads=1, timeout=0)
        event = getattr(worker, '_Worker__event')
        semaphore = getattr(worker, '_Worker__semaphore')

        def fake_process():
            raise QueueEmptyError

        released = {'value': False}

        def fake_release():
            released['value'] = True
            setattr(worker, '_Worker__running', False)
            event.set()

        with patch.object(worker, '_Worker__process', side_effect=fake_process), \
                patch.object(semaphore, 'release', side_effect=fake_release), \
                patch.object(event, 'wait', return_value=True), \
                patch('src.lib.browser.worker.time.sleep'):
            event.clear()
            worker.run()

        self.assertTrue(getattr(worker, '_Worker__empty'))
        self.assertTrue(released['value'])

    def test_worker_run_terminates_on_unexpected_exception(self):
        """Worker.run() should terminate on unexpected exceptions."""

        worker = Worker(Queue(1), num_threads=1, timeout=0)

        with patch.object(worker, '_Worker__process', side_effect=RuntimeError('boom')), \
                patch.object(worker, 'terminate') as terminate_mock, \
                patch.object(getattr(worker, '_Worker__event'), 'wait', return_value=True), \
                patch('src.lib.browser.worker.time.sleep'):
            setattr(worker, '_Worker__running', True)
            worker.run()

        terminate_mock.assert_called_once()

    def test_worker_run_honors_timeout_before_processing(self):
        """Worker.run() should sleep for timeout-enabled workers before processing."""

        worker = Worker(Queue(1), num_threads=1, timeout=0.5)

        def fake_process():
            setattr(worker, '_Worker__running', False)

        with patch.object(worker, '_Worker__process', side_effect=fake_process) as process_mock, \
                patch.object(getattr(worker, '_Worker__event'), 'wait', return_value=True), \
                patch('src.lib.browser.worker.time.sleep') as sleep_mock:
            worker.run()

        sleep_mock.assert_called_once_with(0.5)
        process_mock.assert_called_once_with()

if __name__ == '__main__':
    unittest.main()