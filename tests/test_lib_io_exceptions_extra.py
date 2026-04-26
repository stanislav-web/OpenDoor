# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from src.lib.io.exceptions import ArgumentsError


class TestIoExceptionsExtra(unittest.TestCase):
    """Extra tests for ArgumentsError coverage."""

    def test_arguments_error_does_not_log_nested_arguments_error(self):
        """ArgumentsError should not log again when wrapping ArgumentsError."""

        with patch('src.lib.io.exceptions.exception.log') as log_mock:
            inner = ArgumentsError(ValueError('inner'))
            log_mock.reset_mock()

            outer = ArgumentsError(inner)

        self.assertEqual(str(outer), 'ArgumentsError: ValueError: inner')
        log_mock.assert_not_called()

    def test_arguments_error_logs_non_arguments_error(self):
        """ArgumentsError should log non-ArgumentsError inputs."""

        with patch('src.lib.io.exceptions.exception.log') as log_mock:
            error = ArgumentsError(ValueError('boom'))

        self.assertEqual(str(error), 'ValueError: boom')
        log_mock.assert_called_once()
        kwargs = log_mock.call_args.kwargs
        self.assertEqual(kwargs['class_name'], 'ValueError')
        self.assertEqual(str(kwargs['message']), 'boom')

if __name__ == '__main__':
    unittest.main()