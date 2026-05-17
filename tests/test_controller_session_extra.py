# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch

from src.controller import Controller, SrcError


class TestControllerSessionExtra(unittest.TestCase):
    """Coverage tests for controller session restore branches."""

    def test_scan_action_restores_session_and_overrides_autosave_thresholds(self):
        """Controller should restore params from snapshot and keep explicit autosave overrides."""

        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
            }
        }
        brows = MagicMock()

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=brows) as browser_factory, \
                patch('src.controller.reporter.is_reported', return_value=False):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'session_autosave_sec': 9,
                'session_autosave_items': 99,
            })

        params = browser_factory.call_args[0][0]
        self.assertEqual(params['session_save'], '/tmp/session.json')
        self.assertEqual(params['session_autosave_sec'], 9)
        self.assertEqual(params['session_autosave_items'], 99)
        self.assertEqual(params['session_snapshot'], snapshot)

        brows.ping.assert_called_once()
        brows.scan.assert_called_once()
        brows.done.assert_called_once()


    def test_scan_action_session_load_allows_response_filter_cli_overrides(self):
        """Controller should let explicit CLI response filters override restored session params."""

        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'exclude_status': ['404'],
                'match_regex': ['old'],
            }
        }
        brows = MagicMock()

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=brows) as browser_factory, \
                patch('src.controller.reporter.is_reported', return_value=False):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'exclude_status': ['403'],
                'match_regex': ['[a-z]{1,3}'],
                'min_response_length': 10,
            })

        params = browser_factory.call_args[0][0]
        self.assertEqual(params['exclude_status'], ['403'])
        self.assertEqual(params['match_regex'], ['[a-z]{1,3}'])
        self.assertEqual(params['min_response_length'], 10)
        self.assertNotEqual(params['match_regex'], ['old'])



    def test_scan_action_session_load_preserves_and_allows_tls_legacy_override(self):
        """Controller should keep --tls-legacy in resumed session params."""

        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'https://',
                'ssl': True,
                'port': 443,
                'reports': 'std',
                'tls_legacy': True,
            }
        }
        brows = MagicMock()

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=brows) as browser_factory, \
                patch('src.controller.reporter.is_reported', return_value=False):
            Controller.scan_action({'session_load': '/tmp/session.json'})

        self.assertTrue(browser_factory.call_args[0][0]['tls_legacy'])

        snapshot['params']['tls_legacy'] = False
        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=brows) as browser_factory, \
                patch('src.controller.reporter.is_reported', return_value=False):
            Controller.scan_action({'session_load': '/tmp/session.json', 'tls_legacy': True})

        self.assertTrue(browser_factory.call_args[0][0]['tls_legacy'])

    def test_scan_action_rejects_multi_target_persistent_sessions(self):
        """Controller should reject persistent sessions for multi-target runs."""

        with self.assertRaises(SrcError):
            Controller.scan_action({
                'session_save': '/tmp/session.json',
                'targets': [
                    {'host': 'a.local', 'scheme': 'http://', 'ssl': False},
                    {'host': 'b.local', 'scheme': 'http://', 'ssl': False},
                ],
                'reports': 'std',
            })


if __name__ == '__main__':
    unittest.main()
