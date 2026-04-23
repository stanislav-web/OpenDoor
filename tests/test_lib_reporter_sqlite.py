# -*- coding: utf-8 -*-

import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from src.core.filesystem.exceptions import FileSystemError
from src.lib.reporter import Reporter
from src.lib.reporter.plugins.provider.provider import PluginProvider
from src.lib.reporter.plugins.sqlite import SqliteReportPlugin


class TestSqliteReportPlugin(unittest.TestCase):
    """SQLite report plugin tests."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.target = 'test.local'
        self.data = {
            'items': {
                'success': ['http://example.com/admin'],
                'indexof': ['http://example.com/public'],
                'failed': ['http://example.com/missing'],
            },
            'report_items': {
                'success': [{'url': 'http://example.com/admin', 'size': '9B', 'code': '200'}],
                'indexof': [{'url': 'http://example.com/public', 'size': '1KB', 'code': '200'}],
                'failed': [{'url': 'http://example.com/missing', 'size': '0B', 'code': '404'}],
            },
            'total': {
                'success': 1,
                'indexof': 1,
                'failed': 1,
                'items': 3,
                'workers': 1,
            },
            'fingerprint': {
                'category': 'framework',
                'name': 'Next.js',
                'confidence': 96,
                'signals': [
                    {'type': 'header', 'value': 'x-powered-by: Next.js'},
                    {'type': 'body', 'value': '/_next/static/'},
                ],
                'infrastructure': {
                    'provider': 'AWS CloudFront',
                    'confidence': 98,
                }
            }
        }

    def tearDown(self):
        Reporter.external_directory = None
        self.temp_dir.cleanup()

    def test_reporter_load_returns_sqlite_plugin(self):
        """Reporter.load() should resolve the sqlite reporter."""

        plugin = Reporter.load('sqlite', self.target, self.data)
        self.assertIsInstance(plugin, PluginProvider)
        self.assertIsInstance(plugin, SqliteReportPlugin)

    def test_sqlite_plugin_process_creates_database_with_summary_items_and_fingerprint(self):
        """SqliteReportPlugin should persist summary, items and fingerprint rows."""

        plugin = SqliteReportPlugin(self.target, self.data, directory=self.base_dir)
        plugin.process()

        database_path = os.path.join(self.base_dir, self.target, self.target + '.sqlite')
        self.assertTrue(os.path.isfile(database_path))

        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()

        metadata = dict(cursor.execute('SELECT key, value FROM metadata').fetchall())
        self.assertEqual(metadata['target'], self.target)
        self.assertEqual(metadata['plugin'], 'SqliteReport')

        summary = dict(cursor.execute('SELECT status, total FROM summary').fetchall())
        self.assertEqual(summary['success'], 1)
        self.assertEqual(summary['items'], 3)
        self.assertEqual(summary['workers'], 1)

        items = cursor.execute(
            'SELECT status, url, code, size FROM items ORDER BY id ASC'
        ).fetchall()
        self.assertEqual(
            items,
            [
                ('success', 'http://example.com/admin', '200', '9B'),
                ('indexof', 'http://example.com/public', '200', '1KB'),
                ('failed', 'http://example.com/missing', '404', '0B'),
            ]
        )

        fingerprint = cursor.execute(
            'SELECT category, name, confidence, infrastructure_provider, infrastructure_confidence FROM fingerprint'
        ).fetchone()
        self.assertEqual(fingerprint, ('framework', 'Next.js', 96, 'AWS CloudFront', 98))

        signals = cursor.execute(
            'SELECT type, value FROM fingerprint_signals ORDER BY id ASC'
        ).fetchall()
        self.assertEqual(
            signals,
            [
                ('header', 'x-powered-by: Next.js'),
                ('body', '/_next/static/'),
            ]
        )
        connection.close()

    def test_sqlite_plugin_falls_back_to_legacy_items(self):
        """SqliteReportPlugin should remain backward compatible with URL-only payloads."""

        plugin = SqliteReportPlugin(
            self.target,
            {'items': {'success': ['http://example.com/legacy']}, 'total': {'success': 1}},
            directory=self.base_dir
        )
        plugin.process()

        database_path = os.path.join(self.base_dir, self.target, self.target + '.sqlite')
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()
        items = cursor.execute('SELECT status, url, code, size FROM items').fetchall()
        connection.close()

        self.assertEqual(items, [('success', 'http://example.com/legacy', '-', '0B')])

    def test_sqlite_plugin_wraps_constructor_and_process_errors(self):
        """SqliteReportPlugin should wrap filesystem and sqlite processing errors."""

        with patch('src.lib.reporter.plugins.sqlite.filesystem.makedir', side_effect=FileSystemError('boom')):
            with self.assertRaises(Exception):
                SqliteReportPlugin(self.target, self.data, directory='/custom/')

        with patch('src.lib.reporter.plugins.sqlite.filesystem.makedir', return_value='/tmp/reports'), \
                patch('src.lib.reporter.plugins.sqlite.filesystem.clear', side_effect=FileSystemError('boom')):
            plugin = SqliteReportPlugin(self.target, self.data, directory='/custom/')
            with self.assertRaises(Exception):
                plugin.process()
