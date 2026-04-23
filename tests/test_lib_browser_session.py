# -*- coding: utf-8 -*-

import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch, mock_open

from src.lib.browser.session import SessionError, SessionManager


class TestBrowserSession(unittest.TestCase):
    """High-coverage tests for SessionManager."""

    def make_snapshot(self):
        """Build a valid base snapshot."""

        snapshot = {
            'schemaVersion': 1,
            'appVersion': '5.8.0',
            'createdAt': 1,
            'updatedAt': 1,
            'params': {'host': 'example.com', 'scheme': 'http://'},
            'targets': [{'host': 'example.com', 'scheme': 'http://', 'ssl': False}],
            'pending': [{'url': 'http://example.com/admin', 'depth': 0}],
            'seen': ['0::http://example.com/login'],
            'queuedRecursive': ['http://example.com/admin'],
            'visitedRecursive': ['http://example.com/login'],
            'result': {'total': {}, 'items': {}, 'report_items': {}},
            'stats': {'processed': 1, 'total_items': 2},
        }
        snapshot['checksum'] = SessionManager.build_checksum(snapshot)
        return snapshot

    def test_properties_and_version_fallback(self):
        """SessionManager should expose ctor properties and tolerate missing VERSION file."""

        manager = SessionManager('/tmp/opendoor-session.json', autosave_sec=7, autosave_items=11)

        self.assertEqual(manager.path, '/tmp/opendoor-session.json')
        self.assertEqual(manager.backup_path, '/tmp/opendoor-session.json.bak')
        self.assertEqual(manager.autosave_sec, 7)
        self.assertEqual(manager.autosave_items, 11)

        with patch('builtins.open', side_effect=OSError()):
            self.assertEqual(SessionManager.app_version(), 'unknown')

    def test_validate_task_list_rejects_invalid_shapes(self):
        """SessionManager.validate_task_list() should reject malformed task entries."""

        with self.assertRaises(SessionError):
            SessionManager.validate_task_list('bad', 'pending')

        with self.assertRaises(SessionError):
            SessionManager.validate_task_list([1], 'pending')

        with self.assertRaises(SessionError):
            SessionManager.validate_task_list([{'url': '', 'depth': 0}], 'pending')

        with self.assertRaises(SessionError):
            SessionManager.validate_task_list([{'url': 'http://example.com', 'depth': 'x'}], 'pending')

        with self.assertRaises(SessionError):
            SessionManager.validate_task_list([{'url': 'http://example.com', 'depth': -1}], 'pending')

    def test_validate_string_list_rejects_invalid_shapes(self):
        """SessionManager.validate_string_list() should reject malformed list[str] values."""

        with self.assertRaises(SessionError):
            SessionManager.validate_string_list('bad', 'seen')

        with self.assertRaises(SessionError):
            SessionManager.validate_string_list([1], 'seen')

    def test_validate_snapshot_rejects_missing_and_invalid_values(self):
        """SessionManager.validate_snapshot() should reject missing fields and invalid counters."""

        snapshot = self.make_snapshot()
        broken = dict(snapshot)
        del broken['params']

        with self.assertRaises(SessionError):
            SessionManager.validate_snapshot(broken)

        broken = self.make_snapshot()
        broken['schemaVersion'] = 99
        broken['checksum'] = SessionManager.build_checksum(broken)

        with self.assertRaises(SessionError):
            SessionManager.validate_snapshot(broken)

        broken = self.make_snapshot()
        broken['stats'] = {'processed': -1, 'total_items': 2}
        broken['checksum'] = SessionManager.build_checksum(broken)

        with self.assertRaises(SessionError):
            SessionManager.validate_snapshot(broken)

        broken = self.make_snapshot()
        broken['params'] = []
        broken['checksum'] = SessionManager.build_checksum(broken)

        with self.assertRaises(SessionError):
            SessionManager.validate_snapshot(broken)

    def test_validate_snapshot_rejects_checksum_mismatch(self):
        """SessionManager.validate_snapshot() should reject tampered payloads."""

        snapshot = self.make_snapshot()
        snapshot['params']['host'] = 'tampered.local'

        with self.assertRaises(SessionError):
            SessionManager.validate_snapshot(snapshot)

    def test_should_save_respects_dirty_force_time_and_item_thresholds(self):
        """SessionManager.should_save() should honor dirty, force, timer and item thresholds."""

        manager = SessionManager('/tmp/opendoor-session.json', autosave_sec=20, autosave_items=5)

        self.assertFalse(manager.should_save(False, 0, force=False))
        self.assertTrue(manager.should_save(False, 0, force=True))

        manager._last_saved_at = time.time()
        manager._last_saved_processed = 10

        self.assertFalse(manager.should_save(True, 11, force=False))

        manager._last_saved_at -= 60
        self.assertTrue(manager.should_save(True, 11, force=False))

        manager._last_saved_at = time.time()
        self.assertTrue(manager.should_save(True, 16, force=False))

    def test_save_roundtrip_and_backup_fallback(self):
        """SessionManager should save valid snapshots, create backups and load from .bak when needed."""

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'nested', 'session.json')
            manager = SessionManager(path)

            first = self.make_snapshot()
            second = self.make_snapshot()
            second['stats'] = {'processed': 5, 'total_items': 6}
            second['checksum'] = SessionManager.build_checksum(second)

            with patch.object(SessionManager, 'app_version', return_value='5.8.0'):
                manager.save(first)
                manager.save(second)

            self.assertTrue(os.path.exists(path))
            self.assertTrue(os.path.exists(path + '.bak'))

            loaded = SessionManager.load(path)
            self.assertEqual(loaded['stats']['processed'], 5)

            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('{broken')

            loaded = SessionManager.load(path)
            self.assertEqual(loaded['_loaded_from'], path + '.bak')

    def test_load_missing_raises(self):
        """SessionManager.load() should fail for missing session files."""

        with self.assertRaises(SessionError):
            SessionManager.load('/tmp/definitely-missing-opendoor-session.json')

    def test_save_wraps_replace_errors(self):
        """SessionManager.save() should wrap atomic replace failures."""

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'session.json')
            manager = SessionManager(path)
            snapshot = self.make_snapshot()

            with patch.object(SessionManager, 'app_version', return_value='5.8.0'), \
                    patch('src.lib.browser.session.os.replace', side_effect=OSError('boom')):
                with self.assertRaises(SessionError):
                    manager.save(snapshot)

    def test_load_single_reads_and_validates_json(self):
        """SessionManager._load_single() should read and validate a valid JSON snapshot."""

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'session.json')
            snapshot = self.make_snapshot()

            with open(path, 'w', encoding='utf-8') as handle:
                json.dump(snapshot, handle)

            loaded = SessionManager._load_single(path)

        self.assertEqual(loaded['params']['host'], 'example.com')

    def test_validate_snapshot_rejects_non_dict_result_and_stats(self):
        """SessionManager.validate_snapshot() should reject invalid result/stats container types."""

        broken = self.make_snapshot()
        broken['result'] = []
        broken['checksum'] = SessionManager.build_checksum(broken)

        with self.assertRaises(SessionError):
            SessionManager.validate_snapshot(broken)

        broken = self.make_snapshot()
        broken['stats'] = []
        broken['checksum'] = SessionManager.build_checksum(broken)

        with self.assertRaises(SessionError):
            SessionManager.validate_snapshot(broken)

    def test_load_aggregates_errors_from_main_and_backup(self):
        """SessionManager.load() should surface aggregated errors when both main and backup are invalid."""

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'session.json')

            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('{broken')

            backup_snapshot = self.make_snapshot()
            backup_snapshot['checksum'] = 'bad'
            with open(path + '.bak', 'w', encoding='utf-8') as handle:
                json.dump(backup_snapshot, handle)

            with self.assertRaises(SessionError) as context:
                SessionManager.load(path)

        self.assertIn('session.json', str(context.exception))
        self.assertIn('.bak', str(context.exception))

    def test_save_ignores_backup_copy_failures_and_updates_internal_counters(self):
        """SessionManager.save() should tolerate backup-copy failures and still update bookkeeping."""

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'session.json')
            manager = SessionManager(path)

            first = self.make_snapshot()
            second = self.make_snapshot()
            second['stats'] = {'processed': 7, 'total_items': 8}
            second['checksum'] = SessionManager.build_checksum(second)

            with patch.object(SessionManager, 'app_version', return_value='5.8.0'):
                manager.save(first)

                with patch('src.lib.browser.session.shutil.copyfile', side_effect=OSError()):
                    manager.save(second)

            self.assertTrue(os.path.exists(path))
            self.assertGreater(manager._last_saved_at, 0)
            self.assertEqual(manager._last_saved_processed, 7)

    def test_app_version_reads_version_file_successfully(self):
        """SessionManager.app_version() should return the stripped VERSION file content."""

        with patch('builtins.open', mock_open(read_data='5.8.0\n')):
            self.assertEqual(SessionManager.app_version(), '5.8.0')

    def test_validate_string_list_skips_blank_values(self):
        """SessionManager.validate_string_list() should ignore blank string items."""

        actual = SessionManager.validate_string_list(['alpha', '   ', 'beta'], 'seen')

        self.assertEqual(actual, ['alpha', 'beta'])

    def test_validate_snapshot_rejects_non_object_and_invalid_targets_and_stats(self):
        """SessionManager.validate_snapshot() should reject invalid snapshot shapes and stat types."""

        with self.assertRaises(SessionError):
            SessionManager.validate_snapshot([])

        broken = self.make_snapshot()
        broken['targets'] = 'bad'
        broken['checksum'] = SessionManager.build_checksum(broken)

        with self.assertRaises(SessionError):
            SessionManager.validate_snapshot(broken)

        broken = self.make_snapshot()
        broken['stats'] = {'processed': 'abc', 'total_items': 2}
        broken['checksum'] = SessionManager.build_checksum(broken)

        with self.assertRaises(SessionError):
            SessionManager.validate_snapshot(broken)

    def test_save_wraps_replace_errors_even_when_tmp_cleanup_also_fails(self):
        """SessionManager.save() should still raise SessionError when tmp cleanup also fails."""

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'session.json')
            manager = SessionManager(path)
            snapshot = self.make_snapshot()

            with patch.object(SessionManager, 'app_version', return_value='5.8.0'), \
                    patch('src.lib.browser.session.os.replace', side_effect=OSError('replace failed')), \
                    patch('src.lib.browser.session.os.unlink', side_effect=OSError('unlink failed')):
                with self.assertRaises(SessionError):
                    manager.save(snapshot)

if __name__ == '__main__':
    unittest.main()