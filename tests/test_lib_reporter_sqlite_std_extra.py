# -*- coding: utf-8 -*-

import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.lib.reporter.plugins.sqlite import SqliteReportPlugin
from src.lib.reporter.plugins.std import StdReportPlugin


class TestSqliteAndStdReporterExtra(unittest.TestCase):
    """Extra coverage for sqlite/std reporter plugins."""

    def make_data(self, with_fingerprint=True, with_infrastructure=True, with_signals=True):
        """Build report payload."""

        data = {
            'total': {
                'success': 2,
                'blocked': 1,
            },
            'items': {
                'success': ['https://example.com/admin', 'https://example.com/login'],
                'blocked': ['https://example.com/predictions'],
            },
            'report_items': {
                'success': [
                    {'url': 'https://example.com/admin', 'code': '200', 'size': '10B'},
                    {'url': 'https://example.com/login', 'code': '200', 'size': '12B'},
                ],
                'blocked': [
                    {
                        'url': 'https://example.com/predictions',
                        'code': '403',
                        'size': '32B',
                        'waf': 'Cloudflare',
                        'waf_confidence': 92,
                    }
                ],
            },
        }

        if with_fingerprint:
            fingerprint = {
                'category': 'cms',
                'name': 'WordPress',
                'confidence': 95,
            }

            if with_infrastructure:
                fingerprint['infrastructure'] = {
                    'provider': 'cloudflare',
                    'confidence': 92,
                }

            fingerprint['security_headers'] = {
                'hsts': {
                    'present': True,
                    'grade': 'preload-ready',
                    'max_age': 31536000,
                    'include_subdomains': True,
                    'preload': True,
                    'preload_ready': True,
                    'http_to_https_redirect': True,
                    'warnings': [],
                }
            }

            if with_signals:
                fingerprint['signals'] = [
                    {'type': 'body', 'value': 'wp-content'},
                    {'type': 'header', 'value': 'server: cloudflare'},
                    'skip-me',
                ]
            else:
                fingerprint['signals'] = []

            data['fingerprint'] = fingerprint

        return data

    def test_sqlite_process_persists_items_fingerprint_infrastructure_and_signals(self):
        """SqliteReportPlugin should persist summary, items, fingerprint, infrastructure and dict signals."""

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = SqliteReportPlugin('test.local', self.make_data(), directory=tmpdir)

            with patch('src.lib.reporter.plugins.sqlite.tpl.info') as info_mock:
                plugin.process()

            db_path = os.path.join(tmpdir, 'test.local', 'test.local.sqlite')
            self.assertTrue(os.path.exists(db_path))

            connection = sqlite3.connect(db_path)
            try:
                cursor = connection.cursor()

                summary = dict(cursor.execute('SELECT status, total FROM summary').fetchall())
                self.assertEqual(summary['success'], 2)
                self.assertEqual(summary['blocked'], 1)

                items = cursor.execute(
                    'SELECT status, url, code, size FROM items ORDER BY id'
                ).fetchall()
                self.assertEqual(len(items), 3)
                self.assertEqual(items[0], ('success', 'https://example.com/admin', '200', '10B'))
                self.assertEqual(items[2], ('blocked', 'https://example.com/predictions', '403', '32B'))

                fingerprint = cursor.execute(
                    'SELECT category, name, confidence, infrastructure_provider, infrastructure_confidence, '
                    'hsts_grade, hsts_max_age, hsts_preload_ready FROM fingerprint'
                ).fetchone()
                self.assertEqual(
                    fingerprint,
                    ('cms', 'WordPress', 95, 'cloudflare', 92, 'preload-ready', 31536000, 1)
                )

                signals = cursor.execute(
                    'SELECT type, value FROM fingerprint_signals ORDER BY id'
                ).fetchall()
                self.assertEqual(
                    signals,
                    [
                        ('body', 'wp-content'),
                        ('header', 'server: cloudflare'),
                    ]
                )
            finally:
                connection.close()

            info_mock.assert_called_once()

    def test_sqlite_process_handles_empty_rows_and_missing_infrastructure(self):
        """SqliteReportPlugin should handle empty item rows and fingerprints without infrastructure/signals."""

        data = {
            'total': {
                'success': 0,
            },
            'items': {},
            'report_items': {},
            'fingerprint': {
                'category': 'custom',
                'name': 'Unknown custom stack',
                'confidence': 0,
                'infrastructure': {},
                'signals': [],
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = SqliteReportPlugin('test.local', data, directory=tmpdir)
            plugin.process()

            db_path = os.path.join(tmpdir, 'test.local', 'test.local.sqlite')
            connection = sqlite3.connect(db_path)
            try:
                cursor = connection.cursor()

                item_count = cursor.execute('SELECT COUNT(*) FROM items').fetchone()[0]
                self.assertEqual(item_count, 0)

                fingerprint = cursor.execute(
                    'SELECT category, name, confidence, infrastructure_provider, infrastructure_confidence '
                    'FROM fingerprint'
                ).fetchone()
                self.assertEqual(
                    fingerprint,
                    ('custom', 'Unknown custom stack', 0, None, None)
                )

                signal_count = cursor.execute('SELECT COUNT(*) FROM fingerprint_signals').fetchone()[0]
                self.assertEqual(signal_count, 0)
            finally:
                connection.close()

    def test_sqlite_process_wraps_sqlite_errors_and_closes_connection(self):
        """SqliteReportPlugin should wrap sqlite failures and close opened connections."""

        plugin = SqliteReportPlugin('test.local', self.make_data(), directory=tempfile.gettempdir())

        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value = cursor
        cursor.execute.side_effect = sqlite3.Error('boom')

        with patch('src.lib.reporter.plugins.sqlite.filesystem.clear'), \
                patch('src.lib.reporter.plugins.sqlite.filesystem.makefile'), \
                patch('src.lib.reporter.plugins.sqlite.sqlite3.connect', return_value=connection):
            with self.assertRaises(Exception) as context:
                plugin.process()

        self.assertIn('boom', str(context.exception))
        connection.close.assert_called_once_with()

    def test_std_process_without_fingerprint_writes_plain_summary(self):
        """StdReportPlugin should write plain summary when fingerprint data is absent."""

        plugin = StdReportPlugin('test.local', {
            'total': {
                'success': 2,
                'blocked': 1,
            }
        })

        with patch('src.lib.reporter.plugins.std.sys.writeln') as writeln_mock:
            plugin.process()

        rendered = writeln_mock.call_args[0][0]
        self.assertIn('Statistics (test.local)', rendered)
        self.assertIn('Summary', rendered)
        self.assertIn('success', rendered)
        self.assertIn('blocked', rendered)
        self.assertIn('2', rendered)
        self.assertIn('1', rendered)

    def test_std_process_appends_fingerprint_and_infrastructure_summary(self):
        """StdReportPlugin should append fingerprint and infrastructure summary rows when present."""

        plugin = StdReportPlugin('test.local', self.make_data())

        with patch('src.lib.reporter.plugins.std.sys.writeln') as writeln_mock:
            plugin.process()

        rendered = writeln_mock.call_args[0][0]

        self.assertNotIn('fingerprint_category', rendered)
        self.assertIn('fingerprint_name', rendered)
        self.assertIn('WordPress', rendered)
        self.assertIn('fingerprint_confidence', rendered)
        self.assertIn('95%', rendered)
        self.assertIn('fingerprint_infra', rendered)
        self.assertIn('cloudflare', rendered)
        self.assertNotIn('fingerprint_infra_confidence', rendered)
        self.assertIn('hsts', rendered)
        self.assertIn('preload-ready', rendered)
        self.assertNotIn('hsts_preload_ready', rendered)


if __name__ == '__main__':
    unittest.main()
