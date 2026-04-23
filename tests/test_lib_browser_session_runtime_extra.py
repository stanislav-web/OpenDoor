# -*- coding: utf-8 -*-

import threading
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core import helper
from src.lib.browser.browser import Browser
from src.lib.browser.session import SessionError


class TestBrowserSessionRuntimeExtra(unittest.TestCase):
    """High-impact coverage tests for Browser session runtime hooks."""

    def make_config(self, **overrides):
        """Build a fully populated browser config namespace."""

        base = {
            'scan': 'directories',
            'DEFAULT_SCAN': 'directories',
            'scheme': 'http://',
            'is_ssl': False,
            'host': 'example.com',
            'port': 80,
            'proxy': '',
            'headers': ['X-Test: 1'],
            'cookies': ['sid=abc'],
            'raw_request': None,
            'request_body': 'a=1',
            'accept_cookies': False,
            'keep_alive': False,
            'is_fingerprint': True,
            'wordlist': '/tmp/wordlist.txt',
            'reports': ['std', 'json'],
            'reports_dir': '/tmp/reports',
            'prefix': '',
            'is_random_user_agent': False,
            'is_random_list': False,
            'extensions': ['php', 'json'],
            'ignore_extensions': ['bak'],
            'is_recursive': True,
            'recursive_depth': 2,
            'recursive_status': ['200', '403'],
            'recursive_exclude': ['png', 'jpg'],
            'sniffers': ['indexof', 'file'],
            'include_status': ['200'],
            'exclude_status': ['404'],
            'exclude_size': [0],
            'exclude_size_range': [(10, 20)],
            'match_text': ['admin'],
            'exclude_text': ['forbidden'],
            'match_regex': ['admin'],
            'exclude_regex': ['deny'],
            'min_response_length': 1,
            'max_response_length': 1024,
            'threads': 4,
            'delay': 0,
            'timeout': 10,
            'retries': 3,
            'debug': 1,
            'is_internal_torlist': False,
            'is_external_torlist': False,
            'torlist': '',
            'requested_method': 'HEAD',
            'session_save': '/tmp/opendoor-session.json',
            'session_load': None,
            'session_autosave_sec': 20,
            'session_autosave_items': 200,
            'is_session_enabled': True,
            'is_proxy': False,
            'is_external_reports_dir': False,
            'is_extension_filter': False,
            'is_ignore_extension_filter': False,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    def make_browser(self, **config_overrides):
        """Build a Browser instance through __new__ for private-method testing."""

        br = Browser.__new__(Browser)
        setattr(br, '_Browser__config', self.make_config(**config_overrides))
        setattr(br, '_Browser__debug', SimpleNamespace(
            debug_user_agents=MagicMock(),
            debug_list=MagicMock(),
        ))
        setattr(br, '_Browser__pool', SimpleNamespace(
            items_size=3,
            total_items_size=10,
            workers_size=2,
            size=0,
            is_started=True,
            join=MagicMock(),
            add=MagicMock(),
        ))
        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__result', {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
        })
        setattr(br, '_Browser__visited_recursive', set())
        setattr(br, '_Browser__queued_recursive', set())
        setattr(br, '_Browser__session_lock', threading.RLock())
        setattr(br, '_Browser__session', None)
        setattr(br, '_Browser__session_dirty', False)
        setattr(br, '_Browser__completed_requests', set())
        setattr(br, '_Browser__pending_requests', {})
        setattr(br, '_Browser__processed_offset', 0)
        setattr(br, '_Browser__session_snapshot', None)
        return br

    def test_ensure_session_runtime_state_initializes_missing_attrs(self):
        """Browser should lazily initialize session runtime state for legacy __new__ objects."""

        br = Browser.__new__(Browser)
        setattr(br, '_Browser__config', self.make_config(is_session_enabled=False, session_save=None))

        br._Browser__ensure_session_runtime_state()

        self.assertTrue(hasattr(br, '_Browser__session_lock'))
        self.assertTrue(hasattr(br, '_Browser__pending_requests'))
        self.assertTrue(hasattr(br, '_Browser__completed_requests'))
        self.assertTrue(hasattr(br, '_Browser__session_snapshot'))
        self.assertTrue(hasattr(br, '_Browser__result'))

    def test_build_session_snapshot_exports_full_state(self):
        """Browser should export a rich logical snapshot for persistent resume."""

        br = self.make_browser()
        setattr(br, '_Browser__session_snapshot', {'createdAt': 111})
        setattr(br, '_Browser__pending_requests', {
            '0::http://example.com/admin': {'url': 'http://example.com/admin', 'depth': 0}
        })
        setattr(br, '_Browser__completed_requests', {'0::http://example.com/login'})
        setattr(br, '_Browser__visited_recursive', {'http://example.com/login'})
        setattr(br, '_Browser__queued_recursive', {'http://example.com/admin'})

        snapshot = br._Browser__build_session_snapshot(reason='items')

        self.assertEqual(snapshot['createdAt'], 111)
        self.assertEqual(snapshot['checkpointReason'], 'items')
        self.assertEqual(snapshot['stats']['processed'], 3)
        self.assertEqual(snapshot['stats']['total_items'], 10)
        self.assertEqual(snapshot['pending'][0]['url'], 'http://example.com/admin')
        self.assertEqual(snapshot['seen'], ['0::http://example.com/login'])
        self.assertEqual(snapshot['queuedRecursive'], ['http://example.com/admin'])
        self.assertEqual(snapshot['visitedRecursive'], ['http://example.com/login'])

        params = snapshot['params']
        self.assertEqual(params['reports'], 'std,json')
        self.assertEqual(params['extensions'], 'php,json')
        self.assertEqual(params['ignore_extensions'], 'bak')
        self.assertEqual(params['recursive_status'], '200,403')
        self.assertEqual(params['recursive_exclude'], 'png,jpg')
        self.assertEqual(params['sniff'], 'indexof,file')
        self.assertEqual(params['session_save'], '/tmp/opendoor-session.json')
        self.assertTrue(params['fingerprint'])

    def test_restore_session_state_rehydrates_pending_sets_and_total_size(self):
        """Browser should restore logical checkpoint state into runtime structures."""

        br = self.make_browser()
        snapshot = {
            'createdAt': 1,
            'result': {'total': helper.counter(), 'items': helper.list()},
            'visitedRecursive': ['http://example.com/login'],
            'queuedRecursive': ['http://example.com/admin'],
            'seen': ['0::http://example.com/login'],
            'pending': [{'url': 'http://example.com/admin', 'depth': 1}],
            'stats': {'processed': 7, 'total_items': 25},
        }

        br._Browser__restore_session_state(snapshot)

        self.assertIn('report_items', getattr(br, '_Browser__result'))
        self.assertEqual(getattr(br, '_Browser__processed_offset'), 7)
        self.assertEqual(getattr(br, '_Browser__pool').total_items_size, 25)
        self.assertEqual(
            getattr(br, '_Browser__pending_requests')['1::http://example.com/admin']['depth'],
            1
        )
        self.assertEqual(getattr(br, '_Browser__queued_recursive'), {'http://example.com/admin'})
        self.assertEqual(getattr(br, '_Browser__visited_recursive'), {'http://example.com/login'})
        self.assertFalse(getattr(br, '_Browser__session_dirty'))

    def test_save_session_is_noop_when_session_is_disabled(self):
        """Browser should not persist session state unless the option is enabled."""

        br = self.make_browser(session_save=None, is_session_enabled=False)
        manager = MagicMock()
        setattr(br, '_Browser__session', manager)

        br._Browser__save_session(reason='items', force=False)

        manager.should_save.assert_not_called()
        manager.save.assert_not_called()

    def test_save_session_enabled_calls_manager_and_resets_dirty(self):
        """Browser should persist snapshots through SessionManager when enabled."""

        br = self.make_browser()
        manager = MagicMock()
        manager.should_save.return_value = True
        setattr(br, '_Browser__session', manager)
        setattr(br, '_Browser__session_dirty', True)

        br._Browser__save_session(reason='items', force=False)

        manager.should_save.assert_called_once()
        manager.save.assert_called_once()
        self.assertFalse(getattr(br, '_Browser__session_dirty'))

    def test_resume_pending_requests_expands_pool_and_enqueues_tasks(self):
        """Browser should restore pending tasks into a fresh thread pool."""

        br = self.make_browser()
        setattr(br, '_Browser__processed_offset', 5)
        setattr(br, '_Browser__pending_requests', {
            '0::http://example.com/a': {'url': 'http://example.com/a', 'depth': 0},
            '1::http://example.com/b': {'url': 'http://example.com/b', 'depth': 1},
        })

        br._Browser__resume_pending_requests()

        self.assertEqual(getattr(br, '_Browser__pool').total_items_size, 10)
        self.assertEqual(getattr(br, '_Browser__pool').add.call_count, 2)

    def test_finalize_processed_request_is_noop_when_session_is_disabled(self):
        """Browser should not mutate session state when session mode is disabled."""

        br = self.make_browser(session_save=None, is_session_enabled=False)

        with patch.object(br, '_Browser__complete_request') as complete_mock, \
                patch.object(br, '_Browser__save_session') as save_mock:
            br._Browser__finalize_processed_request('http://example.com/admin', 0)

        complete_mock.assert_not_called()
        save_mock.assert_not_called()

    def test_finalize_processed_request_enabled_calls_complete_and_save(self):
        """Browser should complete and maybe save when session mode is enabled."""

        br = self.make_browser()

        with patch.object(br, '_Browser__complete_request') as complete_mock, \
                patch.object(br, '_Browser__save_session') as save_mock:
            br._Browser__finalize_processed_request('http://example.com/admin', 0)

        complete_mock.assert_called_once_with('http://example.com/admin', 0)
        save_mock.assert_called_once_with(reason='items', force=False)

    def test_scan_restores_pending_requests_when_session_snapshot_is_loaded(self):
        """Browser.scan() should restore pending queue instead of reading dictionary lines."""

        br = self.make_browser()
        setattr(br, '_Browser__session_snapshot', {'createdAt': 1})
        setattr(br, '_Browser__pending_requests', {
            '0::http://example.com/admin': {'url': 'http://example.com/admin', 'depth': 0}
        })

        with patch.object(br, '_Browser__start_request_provider') as start_mock, \
                patch.object(br, '_Browser__resume_pending_requests') as resume_mock:
            br.scan()

        start_mock.assert_called_once()
        resume_mock.assert_called_once()
        getattr(br, '_Browser__reader').get_lines.assert_not_called()

    def test_scan_interrupt_forces_session_save_and_warns_on_failure(self):
        """Browser.scan() should try a forced checkpoint when interrupted."""

        br = self.make_browser()

        with patch.object(br, '_Browser__start_request_provider', side_effect=KeyboardInterrupt), \
                patch.object(br, '_Browser__save_session', side_effect=SessionError('boom')), \
                patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            with self.assertRaises(KeyboardInterrupt):
                br.scan()

        warning_mock.assert_called_once()

    def test_fingerprint_returns_cached_result_without_recomputing(self):
        """Browser.fingerprint() should return cached data without touching detection flow."""

        br = self.make_browser()
        getattr(br, '_Browser__result')['fingerprint'] = {'name': 'WordPress', 'confidence': 95}

        with patch.object(br, '_Browser__start_request_provider') as start_mock:
            actual = br.fingerprint()

        self.assertEqual(actual['name'], 'WordPress')
        start_mock.assert_not_called()

    def test_register_pending_request_rejects_completed_and_duplicate_tasks(self):
        """Browser session bookkeeping should reject completed and duplicate task keys."""

        br = self.make_browser()
        completed_key = '0::http://example.com/admin'
        getattr(br, '_Browser__completed_requests').add(completed_key)

        self.assertFalse(br._Browser__register_pending_request('http://example.com/admin', 0))

        getattr(br, '_Browser__completed_requests').clear()
        self.assertTrue(br._Browser__register_pending_request('http://example.com/admin', 0))
        self.assertFalse(br._Browser__register_pending_request('http://example.com/admin', 0))

    def test_complete_request_moves_task_from_pending_to_completed(self):
        """Browser should move finished tasks from pending to completed sets."""

        br = self.make_browser()
        key = '0::http://example.com/admin'
        getattr(br, '_Browser__pending_requests')[key] = {'url': 'http://example.com/admin', 'depth': 0}

        br._Browser__complete_request('http://example.com/admin', 0)

        self.assertNotIn(key, getattr(br, '_Browser__pending_requests'))
        self.assertIn(key, getattr(br, '_Browser__completed_requests'))
        self.assertTrue(getattr(br, '_Browser__session_dirty'))

    def test_export_targets_returns_empty_without_host(self):
        """Browser should export an empty targets list when no host is configured."""

        br = self.make_browser(host=None)

        self.assertEqual(br._Browser__export_targets(), [])

    def test_restore_session_state_keeps_existing_total_when_saved_total_is_lower(self):
        """Browser restore should not shrink an already larger pool total."""

        br = self.make_browser()
        getattr(br, '_Browser__pool').total_items_size = 50

        snapshot = {
            'createdAt': 1,
            'result': {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()},
            'visitedRecursive': [],
            'queuedRecursive': [],
            'seen': [],
            'pending': [],
            'stats': {'processed': 2, 'total_items': 10},
        }

        br._Browser__restore_session_state(snapshot)

        self.assertEqual(getattr(br, '_Browser__pool').total_items_size, 50)
        self.assertEqual(getattr(br, '_Browser__processed_offset'), 2)

    def test_save_session_returns_early_when_manager_declines(self):
        """Browser should skip save when SessionManager says no checkpoint is needed."""

        br = self.make_browser()
        manager = MagicMock()
        manager.should_save.return_value = False
        setattr(br, '_Browser__session', manager)
        setattr(br, '_Browser__session_dirty', True)

        br._Browser__save_session(reason='items', force=False)

        manager.should_save.assert_called_once()
        manager.save.assert_not_called()
        self.assertTrue(getattr(br, '_Browser__session_dirty'))

    def test_resume_pending_requests_returns_early_when_nothing_is_pending(self):
        """Browser resume should do nothing when there are no pending session tasks."""

        br = self.make_browser()
        setattr(br, '_Browser__pending_requests', {})

        br._Browser__resume_pending_requests()

        getattr(br, '_Browser__pool').add.assert_not_called()

    def test_ensure_session_runtime_state_keeps_existing_result_object(self):
        """Browser lazy session init should not overwrite an already prepared result basket."""

        br = Browser.__new__(Browser)
        existing = {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()}
        setattr(br, '_Browser__result', existing)

        br._Browser__ensure_session_runtime_state()

        self.assertIs(getattr(br, '_Browser__result'), existing)

if __name__ == '__main__':
    unittest.main()