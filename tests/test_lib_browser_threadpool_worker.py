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
        """ThreadPool.add() should open the pause menu when queue.put() is interrupted."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=5, timeout=0)

        queue_mock = getattr(pool, '_ThreadPool__queue')

        with patch.object(queue_mock, 'put', side_effect=KeyboardInterrupt), \
                patch.object(pool, 'pause') as pause_mock:
            pool.add(lambda: None)

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
                patch('src.lib.browser.threadpool.tpl.prompt', side_effect=['x', 'c']):
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
                patch('src.lib.browser.threadpool.tpl.prompt', return_value='e'):
            with self.assertRaises(KeyboardInterrupt):
                pool.pause()

    def test_worker_resume_and_process_and_terminate(self):
        """Worker should resume, process a task and terminate via helpers."""

        queue = Queue(1)
        result = []
        worker = Worker(queue, num_threads=1, timeout=0)

        event = getattr(worker, '_Worker__event')

        worker.pause()
        self.assertFalse(event.is_set())
        self.assertTrue(getattr(worker, '_Worker__running'))

        worker.resume()
        self.assertTrue(event.is_set())
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

    def test_worker_run_sets_empty_without_terminating_after_queue_empty(self):
        """Worker.run() should mark queue empty without treating pause as a fatal error."""

        worker = Worker(Queue(1), num_threads=1, timeout=0)
        event = getattr(worker, '_Worker__event')

        def fake_process():
            setattr(worker, '_Worker__running', False)
            raise QueueEmptyError

        with patch.object(worker, '_Worker__process', side_effect=fake_process), \
                patch.object(event, 'wait', return_value=True), \
                patch.object(worker, 'terminate') as terminate_mock, \
                patch('src.lib.browser.worker.time.sleep'):
            event.clear()
            worker.run()

        self.assertTrue(getattr(worker, '_Worker__empty'))
        terminate_mock.assert_not_called()

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

    def test_worker_process_marks_queue_done_when_callback_raises(self):
        """Worker.__process() should not leave Queue.join() blocked after task errors."""

        queue = Queue(1)
        worker = Worker(queue, num_threads=1, timeout=0)

        def boom():
            raise RuntimeError('boom')

        queue.put((boom, (), {}))

        with self.assertRaises(RuntimeError):
            worker._Worker__process()

        self.assertEqual(queue.unfinished_tasks, 0)
        self.assertEqual(worker.failed, 1)
        self.assertIsNone(worker.active_task)

    def test_threadpool_join_warns_when_task_makes_no_progress(self):
        """ThreadPool.join() should emit a watchdog warning for long-running active tasks."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        queue = getattr(pool, '_ThreadPool__queue')
        queue.put((lambda: None, ('https://example.test/hang',), {}))
        setattr(pool, '_ThreadPool__submitted', 1)
        setattr(pool, '_ThreadPool__workers', [type('ActiveWorker', (), {
            'completed': 0,
            'active_task': {
                'label': 'https://example.test/hang',
                'started_at': 1.0,
            },
        })()])

        def release_after_wait(timeout=None):
            self.assertEqual(timeout, pool.JOIN_POLL_INTERVAL_SEC)
            queue.unfinished_tasks = 0
            return True

        with patch.object(pool, 'JOIN_STALL_WARNING_SEC', 0.0), \
                patch.object(queue.all_tasks_done, 'wait', side_effect=release_after_wait), \
                patch('src.lib.browser.threadpool.time.monotonic', side_effect=[1.0, 62.0]), \
                patch('src.lib.browser.threadpool.tpl.warning') as warning_mock:
            pool.join()

        warning_mock.assert_called_once()
        self.assertIn('Scan worker has not completed a request', warning_mock.call_args.kwargs.get('msg'))
        self.assertIn('https://example.test/hang', warning_mock.call_args.kwargs.get('msg'))


    def test_worker_active_task_returns_metadata_when_processing(self):
        """Worker.active_task should expose current task metadata."""

        worker = Worker(Queue(1), num_threads=1, timeout=0)
        setattr(worker, '_Worker__task_label', 'https://example.test/active')
        setattr(worker, '_Worker__task_started_at', 12.5)

        self.assertEqual(worker.active_task, {
            'label': 'https://example.test/active',
            'started_at': 12.5,
        })

    def test_worker_build_task_label_uses_keyword_arguments_and_fallback(self):
        """Worker.__build_task_label() should describe keyword-only and unknown tasks."""

        build_label = getattr(Worker, '_Worker__build_task_label')

        self.assertEqual(build_label((), {'url': 'https://example.test/kw'}), 'url=https://example.test/kw')
        self.assertEqual(build_label((), {}), 'unknown task')

    def test_threadpool_completed_and_active_tasks_ignore_missing_or_invalid_worker_metadata(self):
        """ThreadPool diagnostics should tolerate workers without completed/active task metadata."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        setattr(pool, '_ThreadPool__workers', [
            type('NoMetaWorker', (), {})(),
            type('InvalidActiveWorker', (), {'completed': None, 'active_task': 'bad'})(),
            type('ValidActiveWorker', (), {
                'completed': 2,
                'active_task': {'label': 'https://example.test/ok', 'started_at': 4.0},
            })(),
        ])

        self.assertEqual(pool.completed_size, 2)
        self.assertEqual(pool.active_tasks, [{'label': 'https://example.test/ok', 'started_at': 4.0}])

    def test_threadpool_join_does_not_warn_before_stall_threshold(self):
        """ThreadPool.join() should stay quiet while the stall threshold has not elapsed."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        queue = getattr(pool, '_ThreadPool__queue')
        queue.put((lambda: None, (), {}))
        setattr(pool, '_ThreadPool__submitted', 1)
        setattr(pool, '_ThreadPool__workers', [type('IdleWorker', (), {'completed': 0, 'active_task': None})()])

        def release_after_wait(timeout=None):
            self.assertEqual(timeout, pool.JOIN_POLL_INTERVAL_SEC)
            queue.unfinished_tasks = 0
            return True

        with patch.object(queue.all_tasks_done, 'wait', side_effect=release_after_wait), \
                patch('src.lib.browser.threadpool.time.monotonic', side_effect=[1.0, 2.0]), \
                patch('src.lib.browser.threadpool.tpl.warning') as warning_mock:
            pool.join()

        warning_mock.assert_not_called()

    def test_threadpool_join_does_not_warn_when_recent_activity_reset_stall_timer(self):
        """ThreadPool.join() should not warn only because the warning interval elapsed."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        queue = getattr(pool, '_ThreadPool__queue')
        queue.put((lambda: None, ('https://example.test/slow',), {}))
        setattr(pool, '_ThreadPool__submitted', 1)
        setattr(pool, '_ThreadPool__workers', [type('ActiveWorker', (), {
            'completed': 0,
            'active_task': {
                'label': 'https://example.test/slow',
                'started_at': 59.0,
            },
        })()])

        wait_calls = {'count': 0}

        def wait_with_recent_activity(timeout=None):
            self.assertEqual(timeout, pool.JOIN_POLL_INTERVAL_SEC)
            wait_calls['count'] += 1

            if wait_calls['count'] == 1:
                worker = getattr(pool, '_ThreadPool__workers')[0]
                worker.completed = 1
            else:
                queue.unfinished_tasks = 0

            return True

        with patch.object(queue.all_tasks_done, 'wait', side_effect=wait_with_recent_activity), \
                patch('src.lib.browser.threadpool.time.monotonic', side_effect=[1.0, 60.0, 61.0]), \
                patch('src.lib.browser.threadpool.tpl.warning') as warning_mock:
            pool.join()

        self.assertEqual(wait_calls['count'], 2)
        warning_mock.assert_not_called()

    def test_threadpool_format_active_tasks_handles_empty_and_truncated_lists(self):
        """ThreadPool.__format_active_tasks() should render empty and truncated active task sets."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        setattr(pool, '_ThreadPool__workers', [])
        self.assertEqual(getattr(pool, '_ThreadPool__format_active_tasks')(10.0), 'none')

        setattr(pool, '_ThreadPool__workers', [
            type('ActiveWorker', (), {'active_task': {'label': 'u1', 'started_at': 1.0}})(),
            type('ActiveWorker', (), {'active_task': {'label': 'u2', 'started_at': 2.0}})(),
            type('ActiveWorker', (), {'active_task': {'label': None, 'started_at': None}})(),
            type('ActiveWorker', (), {'active_task': {'label': 'u4', 'started_at': 4.0}})(),
        ])

        rendered = getattr(pool, '_ThreadPool__format_active_tasks')(11.0)

        self.assertIn('u1 (10s)', rendered)
        self.assertIn('unknown task (0s)', rendered)
        self.assertIn('+1 more', rendered)

    def test_threadpool_pause_prompts_even_from_main_thread(self):
        """ThreadPool.pause() should show the runtime menu when Ctrl+C reaches the main thread."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        with patch('src.lib.browser.threadpool.tpl.prompt', return_value='c') as prompt_mock, \
                patch('src.lib.browser.threadpool.tpl.info'):
            pool.pause()

        prompt_mock.assert_called_once_with(key='option_prompt')
        self.assertTrue(pool.is_started)

    def test_threadpool_resume_is_noop_when_already_started(self):
        """ThreadPool.resume() should not notify or resume workers while already started."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        worker = MagicMock()
        setattr(pool, '_ThreadPool__workers', [worker])
        pool.is_started = True

        with patch('src.lib.browser.threadpool.tpl.info') as info_mock:
            pool.resume()

        info_mock.assert_not_called()
        worker.resume.assert_not_called()

    def test_threadpool_join_opens_pause_menu_on_keyboard_interrupt_and_continues(self):
        """ThreadPool.join() should pause/resume instead of bubbling Ctrl+C immediately."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        queue = getattr(pool, '_ThreadPool__queue')
        queue.put((lambda: None, (), {}))

        wait_calls = {'count': 0}

        def wait_or_interrupt(timeout=None):
            self.assertEqual(timeout, pool.JOIN_POLL_INTERVAL_SEC)
            wait_calls['count'] += 1

            if wait_calls['count'] == 1:
                raise KeyboardInterrupt

            queue.unfinished_tasks = 0
            return True

        with patch.object(queue.all_tasks_done, 'wait', side_effect=wait_or_interrupt), \
                patch.object(pool, 'pause') as pause_mock, \
                patch('src.lib.browser.threadpool.time.monotonic', side_effect=[1.0, 2.0]):
            pool.join()

        pause_mock.assert_called_once_with()
        self.assertEqual(wait_calls['count'], 2)


if __name__ == '__main__':
    unittest.main()