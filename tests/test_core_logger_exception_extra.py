# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch

from src.core.logger.exception import LoggerException


class TestLoggerExceptionExtra(unittest.TestCase):
    """TestLoggerExceptionExtra class."""

    def test_log_writes_structured_error_message(self):
        """LoggerException.log() should create and write a formatted exception log."""

        logger_mock = MagicMock()

        def invoke_logger():
            LoggerException.log(class_name='TestError', message='boom')

        with patch('src.core.logger.exception.filesystem.makedir') as makedir_mock, \
                patch('src.core.logger.exception.logging.config.dictConfig') as dictconfig_mock, \
                patch('src.core.logger.exception.logging.getLogger', return_value=logger_mock):
            invoke_logger()

        makedir_mock.assert_called_once()
        dictconfig_mock.assert_called_once()
        logger_mock.error.assert_called_once()

        message = logger_mock.error.call_args[0][0]
        self.assertIn('TestError: boom', message)
        self.assertIn('invoke_logger()', message)

    def test_log_swallows_internal_logging_errors(self):
        """LoggerException.log() should swallow internal logger setup failures."""

        with patch('src.core.logger.exception.filesystem.makedir', side_effect=Exception('boom')):
            LoggerException.log(class_name='TestError', message='boom')