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