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

    def test_threadpool_accepts_custom_stall_warning_interval(self):
        """ThreadPool should allow Browser to tune stall visibility from request timeout."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0, stall_warning_interval=15)

        self.assertEqual(getattr(pool, '_ThreadPool__stall_warning_interval'), 15.0)

    def test_threadpool_uses_default_stall_warning_interval_for_invalid_values(self):
        """ThreadPool should fall back to the default stall interval for invalid values."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            negative_pool = ThreadPool(num_threads=1, total_items=1, timeout=0, stall_warning_interval=-1)
            invalid_pool = ThreadPool(num_threads=1, total_items=1, timeout=0, stall_warning_interval='bad')

        self.assertEqual(
            getattr(negative_pool, '_ThreadPool__stall_warning_interval'),
            float(ThreadPool.JOIN_STALL_WARNING_SEC),
        )
        self.assertEqual(
            getattr(invalid_pool, '_ThreadPool__stall_warning_interval'),
            float(ThreadPool.JOIN_STALL_WARNING_SEC),
        )

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
        message = warning_mock.call_args.kwargs.get('msg')
        self.assertIn('Network request is still waiting/retrying', message)
        self.assertIn('without progress', message)
        self.assertIn('queued=', message)
        self.assertIn('https://example.test/hang', message)
        self.assertIn('no-progress=', message)
        self.assertNotIn('idle', message)

    def test_should_not_warn_when_active_task_heartbeat_advances(self):
        """ThreadPool.join() should not report a stall while subrequest heartbeat advances."""

        class HeartbeatWorker:
            completed = 0

            def __init__(self):
                self.heartbeat = 1.0

            @property
            def active_task(self):
                current = self.heartbeat
                self.heartbeat += 1.0
                return {
                    'label': 'https://example.test/admin',
                    'started_at': 1.0,
                    'last_activity_at': current,
                    'detail': 'header-bypass probe',
                }

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        queue = getattr(pool, '_ThreadPool__queue')
        queue.put((lambda: None, ('https://example.test/admin',), {}))
        setattr(pool, '_ThreadPool__submitted', 1)
        setattr(pool, '_ThreadPool__workers', [HeartbeatWorker()])

        waits = {'count': 0}

        def release_after_two_waits(timeout=None):
            waits['count'] += 1
            if waits['count'] >= 2:
                queue.unfinished_tasks = 0
            return True

        with patch.object(pool, 'JOIN_STALL_WARNING_SEC', 0.0), \
                patch.object(queue.all_tasks_done, 'wait', side_effect=release_after_two_waits), \
                patch('src.lib.browser.threadpool.time.monotonic', side_effect=[1.0, 2.0, 3.0]), \
                patch('src.lib.browser.threadpool.tpl.warning') as warning_mock:
            pool.join()

        warning_mock.assert_not_called()

    def test_worker_active_task_returns_metadata_when_processing(self):
        """Worker.active_task should expose current task metadata."""

        worker = Worker(Queue(1), num_threads=1, timeout=0)
        setattr(worker, '_Worker__task_label', 'https://example.test/active')
        setattr(worker, '_Worker__task_started_at', 12.5)

        self.assertEqual(worker.active_task, {
            'label': 'https://example.test/active',
            'started_at': 12.5,
            'last_activity_at': 12.5,
            'detail': None,
        })

    def test_should_update_active_task_heartbeat_metadata(self):
        """Worker.touch_active_task() should expose long-running substep progress."""

        worker = Worker(Queue(1), num_threads=1, timeout=0)
        setattr(worker, '_Worker__task_label', 'https://example.test/active')
        setattr(worker, '_Worker__task_started_at', 12.5)
        setattr(worker, '_Worker__task_last_activity_at', 12.5)

        with patch('src.lib.browser.worker.time.monotonic', return_value=14.0):
            worker.touch_active_task('header-bypass 2/8')

        self.assertEqual(worker.active_task, {
            'label': 'https://example.test/active',
            'started_at': 12.5,
            'last_activity_at': 14.0,
            'detail': 'header-bypass 2/8',
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

        self.assertIn('u1 (elapsed=10s, no-progress=10s)', rendered)
        self.assertIn('unknown task (elapsed=0s, no-progress=0s)', rendered)
        self.assertNotIn('idle', rendered)
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


    def test_runtime_pause_answer_should_accept_continue_variants(self):
        """Runtime pause answer normalization should accept continue variants."""

        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('c'), 'C')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('C'), 'C')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('CC'), 'C')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('cCccc'), 'C')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('continue'), 'C')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('Continue'), 'C')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('с'), 'C')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('С'), 'C')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('сссс'), 'C')

    def test_runtime_pause_answer_should_accept_exit_variants(self):
        """Runtime pause answer normalization should accept exit variants."""

        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('e'), 'E')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('E'), 'E')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('EE'), 'E')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('exit'), 'E')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('Exit'), 'E')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('q'), 'E')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('quit'), 'E')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('е'), 'E')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('Е'), 'E')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('ееее'), 'E')

    def test_runtime_pause_answer_should_preserve_empty_and_reject_unknown_values(self):
        """Runtime pause answer normalization should preserve Enter and reject unknown commands."""

        self.assertEqual(ThreadPool.normalize_runtime_pause_answer(''), '')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer(None), '')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('x'), 'x')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('  x  '), 'x')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('   '), '')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('  e  '), 'E')

    def test_runtime_pause_answer_should_use_first_normalized_character(self):
        """Runtime pause answer normalization should use the first typed character."""

        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('continue later'), 'C')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('quit now'), 'E')
        self.assertEqual(ThreadPool.normalize_runtime_pause_answer('Zzz'), 'z')

    def test_pause_should_resume_on_repeated_or_cyrillic_continue_input(self):
        """ThreadPool.pause() should resume on repeated and Cyrillic continue answers."""

        cases = ('CC', 'cCccc', 'сссс')

        for answer in cases:
            with self.subTest(answer=answer):
                with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
                    pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

                with patch('src.lib.browser.threadpool.tpl.prompt', return_value=answer), \
                        patch('src.lib.browser.threadpool.tpl.info'):
                    pool.pause()

                self.assertTrue(pool.is_started)

    def test_should_format_active_task_with_detail_metadata(self):
        """ThreadPool diagnostics should include active task detail metadata."""

        with patch('src.lib.browser.threadpool.Worker', side_effect=lambda q, n, t: FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=1, total_items=1, timeout=0)

        setattr(pool, '_ThreadPool__workers', [type('ActiveWorker', (), {
            'active_task': {
                'label': 'https://example.test/admin',
                'detail': 'header-bypass 3/8',
                'started_at': 1.0,
                'last_activity_at': 9.0,
            },
        })()])

        rendered = getattr(pool, '_ThreadPool__format_active_tasks')(11.0)

        self.assertIn('https://example.test/admin [header-bypass 3/8] (elapsed=10s, no-progress=2s)', rendered)

    def test_should_ignore_worker_heartbeat_without_active_task(self):
        """Worker.touch_active_task() should be safe before a queued task starts."""

        worker = Worker(Queue(1), num_threads=1, timeout=0)

        worker.touch_active_task('probe 1/2')

        self.assertIsNone(worker.active_task)

    def test_should_update_worker_heartbeat_without_replacing_detail_when_none(self):
        """Worker.touch_active_task() should preserve detail when no new detail is supplied."""

        worker = Worker(Queue(1), num_threads=1, timeout=0)
        setattr(worker, '_Worker__task_label', 'https://example.test/admin')
        setattr(worker, '_Worker__task_started_at', 10.0)
        setattr(worker, '_Worker__task_last_activity_at', 10.0)
        setattr(worker, '_Worker__task_detail', 'header-bypass 1/8')

        with patch('src.lib.browser.worker.time.monotonic', return_value=12.0):
            worker.touch_active_task()

        task = worker.active_task
        self.assertEqual(task['last_activity_at'], 12.0)
        self.assertEqual(task['detail'], 'header-bypass 1/8')



if __name__ == '__main__':
    unittest.main()
