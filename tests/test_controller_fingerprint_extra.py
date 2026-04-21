# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, call, patch

from src import Controller


class TestControllerFingerprintExtra(unittest.TestCase):
    """Extra Controller coverage for fingerprint flow."""

    def test_scan_action_calls_fingerprint_between_ping_and_scan(self):
        """
        Controller.scan_action() should call fingerprint after ping and before scan.

        :return: None
        """

        browser_instance = MagicMock()
        params = {'host': 'http://example.com', 'reports': 'std', 'fingerprint': True}

        with patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.reporter.default', 'std'), \
                patch('src.controller.tpl.info'):
            Controller.scan_action(params)

        self.assertEqual(
            browser_instance.mock_calls,
            [
                call.ping(),
                call.fingerprint(),
                call.scan(),
                call.done(),
            ]
        )

    def test_resolve_scan_targets_returns_explicit_targets_first(self):
        """
        Controller._resolve_scan_targets() should prefer explicit targets.

        :return: None
        """

        targets = [{'host': 'a.test'}, {'host': 'b.test'}]
        self.assertEqual(Controller._resolve_scan_targets({'targets': targets, 'host': 'x'}), targets)

    def test_resolve_scan_targets_builds_host_target_with_scheme_and_ssl(self):
        """
        Controller._resolve_scan_targets() should preserve host, scheme and ssl.

        :return: None
        """

        self.assertEqual(
            Controller._resolve_scan_targets({'host': 'example.com', 'scheme': 'https://', 'ssl': True}),
            [{'host': 'example.com', 'scheme': 'https://', 'ssl': True}]
        )

    def test_resolve_scan_targets_returns_empty_list_without_targets(self):
        """
        Controller._resolve_scan_targets() should return an empty list when nothing is scanable.

        :return: None
        """

        self.assertEqual(Controller._resolve_scan_targets({}), [])