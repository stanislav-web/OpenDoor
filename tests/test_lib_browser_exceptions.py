# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from src.lib.browser.exceptions import BrowserError


class TestBrowserExceptions(unittest.TestCase):
    """Regression tests for BrowserError logging branches."""

    def test_browser_error_logs_non_browser_exceptions(self):
        """BrowserError should log wrapped non-BrowserError exceptions."""

        with patch('src.lib.browser.exceptions.exception.log') as log_mock:
            error = BrowserError(ValueError('boom'))

        self.assertEqual(str(error), 'ValueError: boom')
        log_mock.assert_called_once_with(class_name='ValueError', message='boom')

    def test_browser_error_does_not_log_nested_browser_error(self):
        """BrowserError should not log again when wrapping BrowserError."""

        with patch('src.lib.browser.exceptions.exception.log') as log_mock:
            inner = BrowserError(Exception('inner'))
            log_mock.reset_mock()

            outer = BrowserError(inner)

        self.assertEqual(str(outer), 'BrowserError: Exception: inner')
        log_mock.assert_not_called()

if __name__ == '__main__':
    unittest.main()