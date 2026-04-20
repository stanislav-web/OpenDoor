# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development Team: Brain Storm Team
"""

from io import StringIO
import unittest
from unittest.mock import MagicMock, patch

from src.core.logger.logger import Logger
from src.lib.tpl import Tpl, TplError


class TestTpl(unittest.TestCase):
    """TestTpl class."""

    def tearDown(self):
        """
        Cleanup logger handlers after each test.

        :return: None
        """
        log_instance = Logger.log()

        for handler in list(log_instance.handlers):
            log_instance.removeHandler(handler)

    def prompt_answer(self):
        """
        Call Tpl.prompt helper.

        :return: str
        """
        return Tpl.prompt(msg='fake')

    def test_cancel(self):
        """Tpl.cancel() should stop execution using template key."""

        with self.assertRaises(SystemExit) as context:
            Tpl.cancel(key='abort')

        self.assertTrue(SystemExit == context.expected)

    def test_cancel_with_plain_message(self):
        """Tpl.cancel() should also work with a plain message."""

        with self.assertRaises(SystemExit) as context:
            Tpl.cancel(msg='plain abort')

        self.assertTrue(SystemExit == context.expected)

    def test_cancel_exception(self):
        """Tpl.cancel() should wrap template lookup errors."""

        undefined = 'undefined'

        with self.assertRaises(TplError) as context:
            Tpl.cancel(key=undefined)

        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)

    def test_prompt(self):
        """Tpl.prompt() should prompt with a plain message."""

        with patch('builtins.input', return_value='fake') as input_mock:
            self.assertEqual(self.prompt_answer(), 'fake')
            input_mock.assert_called_once_with('fake')

    def test_prompt_with_key(self):
        """Tpl.prompt() should prompt using a template key."""

        with patch('builtins.input', return_value='C') as input_mock:
            result = Tpl.prompt(key='option_prompt')

        self.assertEqual(result, 'C')
        input_mock.assert_called_once()

    def test_prompt_exception(self):
        """Tpl.prompt() should wrap template lookup errors."""

        undefined = 'undefined'

        with self.assertRaises(TplError) as context:
            Tpl.prompt(key=undefined)

        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)

    def test_line(self):
        """Tpl.line() should return a colored plain message."""

        expected = Tpl.line('test')
        self.assertTrue('test' in expected)

    def test_line_with_key(self):
        """Tpl.line() should format and color a template message."""

        expected = Tpl.line(key='report', plugin='testplugin', dest='testdst')
        self.assertTrue('testplugin' in expected)
        self.assertTrue('testdst' in expected)

    def test_line_exception(self):
        """Tpl.line() should wrap missing template errors."""

        undefined = 'undefined'

        with self.assertRaises(TplError) as context:
            Tpl.line(key=undefined)

        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)

    def test_line_log(self):
        """Tpl.line_log() should write plain messages to stdout."""

        with patch('sys.stdout', new=StringIO()) as fake_output:
            Tpl.line_log('test_line_log')
            self.assertTrue('test_line_log' in fake_output.getvalue().strip())

    def test_line_log_with_key_and_write_false(self):
        """Tpl.line_log() should return formatted inline content when write is disabled."""

        result = Tpl.line_log(key='report', status='info', write=False, plugin='plug', dest='dst')

        self.assertTrue('plug' in result)
        self.assertTrue('dst' in result)

    def test_line_log_plain_write_false(self):
        """Tpl.line_log() should return plain message unchanged when write is disabled."""

        result = Tpl.line_log('plain_line', write=False)
        self.assertEqual(result, 'plain_line')

    def test_line_log_exception(self):
        """Tpl.line_log() should wrap missing template errors."""

        undefined = 'undefined'

        with self.assertRaises(TplError) as context:
            Tpl.line_log(key=undefined)

        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)

    def test_message(self):
        """Tpl.message() should write a plain formatted message."""

        with patch('sys.stdout', new=StringIO()) as fake_output:
            Tpl.message('test_message')
            self.assertTrue('test_message' in fake_output.getvalue().strip())

    def test_message_with_args(self):
        """Tpl.message() should format provided args."""

        with patch('sys.stdout', new=StringIO()) as fake_output:
            Tpl.message('hello {name}', args={'name': 'Stanislav'})
            self.assertTrue('hello Stanislav' in fake_output.getvalue().strip())

    def test_error(self):
        """Tpl.error() should log a plain error message."""

        with patch('sys.stderr', new=StringIO()) as fake_output:
            Tpl.error('test_error')
            self.assertTrue('' in fake_output.getvalue().strip())

    def test_error_with_key(self):
        """Tpl.error() should log a formatted template message."""

        with patch('src.lib.tpl.tpl.logger.log') as log_mock:
            logger_instance = MagicMock()
            log_mock.return_value = logger_instance

            Tpl.error(key='report', plugin='ErrPlugin', dest='ErrDest')

        log_mock.assert_called_once_with('error')
        logger_instance.error.assert_called_once()
        logged_message = logger_instance.error.call_args[0][0]
        self.assertTrue('ErrPlugin' in logged_message)
        self.assertTrue('ErrDest' in logged_message)

    def test_error_exception(self):
        """Tpl.error() should wrap missing template errors."""

        undefined = 'undefined'

        with self.assertRaises(TplError) as context:
            Tpl.error(key=undefined)

        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)

    def test_warning(self):
        """Tpl.warning() should log a plain warning message."""

        with patch('sys.stdout', new=StringIO()) as fake_output:
            Tpl.warning('test_warning')
            self.assertTrue('' in fake_output.getvalue().strip())

    def test_warning_with_key(self):
        """Tpl.warning() should log a formatted template message."""

        with patch('src.lib.tpl.tpl.logger.log') as log_mock:
            logger_instance = MagicMock()
            log_mock.return_value = logger_instance

            Tpl.warning(key='report', plugin='WarnPlugin', dest='WarnDest')

        log_mock.assert_called_once_with('warning')
        logger_instance.warning.assert_called_once()
        logged_message = logger_instance.warning.call_args[0][0]
        self.assertTrue('WarnPlugin' in logged_message)
        self.assertTrue('WarnDest' in logged_message)

    def test_warning_exception(self):
        """Tpl.warning() should wrap missing template errors."""

        undefined = 'undefined'

        with self.assertRaises(TplError) as context:
            Tpl.warning(key=undefined)

        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)

    def test_info(self):
        """Tpl.info() should log a plain info message."""

        with patch('sys.stdout', new=StringIO()) as fake_output:
            Tpl.info('test_info')
            self.assertTrue('' in fake_output.getvalue().strip())

    def test_info_with_key(self):
        """Tpl.info() should log a formatted template message."""

        with patch('src.lib.tpl.tpl.logger.log') as log_mock:
            logger_instance = MagicMock()
            log_mock.return_value = logger_instance

            Tpl.info(key='report', plugin='InfoPlugin', dest='InfoDest')

        log_mock.assert_called_once_with('info')
        logger_instance.info.assert_called_once()
        logged_message = logger_instance.info.call_args[0][0]
        self.assertTrue('InfoPlugin' in logged_message)
        self.assertTrue('InfoDest' in logged_message)

    def test_info_with_clear(self):
        """Tpl.info() should clear previous line when requested."""

        with patch('src.lib.tpl.tpl.sys.writels') as writels_mock, \
                patch('src.lib.tpl.tpl.logger.log') as log_mock:
            logger_instance = MagicMock()
            log_mock.return_value = logger_instance

            Tpl.info('clear_info', clear=True)

        writels_mock.assert_called_once_with("")
        log_mock.assert_called_once_with('info')
        logger_instance.info.assert_called_once_with('clear_info')

    def test_info_exception(self):
        """Tpl.info() should wrap missing template errors."""

        undefined = 'undefined'

        with self.assertRaises(TplError) as context:
            Tpl.info(key=undefined)

        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)

    def test_debug_plain_message(self):
        """Tpl.debug() should log a plain debug message."""

        with patch('src.lib.tpl.tpl.logger.log') as log_mock:
            logger_instance = MagicMock()
            log_mock.return_value = logger_instance

            Tpl.debug('debug_message')

        log_mock.assert_called_once_with('debug')
        logger_instance.debug.assert_called_once_with('debug_message')

    def test_debug_with_key(self):
        """Tpl.debug() should log a formatted template message."""

        with patch('src.lib.tpl.tpl.logger.log') as log_mock:
            logger_instance = MagicMock()
            log_mock.return_value = logger_instance

            Tpl.debug(key='report', plugin='DbgPlugin', dest='DbgDest')

        log_mock.assert_called_once_with('debug')
        logger_instance.debug.assert_called_once()
        logged_message = logger_instance.debug.call_args[0][0]
        self.assertTrue('DbgPlugin' in logged_message)
        self.assertTrue('DbgDest' in logged_message)

    def test_debug_exception(self):
        """Tpl.debug() should wrap missing template errors."""

        undefined = 'undefined'

        with self.assertRaises(TplError) as context:
            Tpl.debug(key=undefined)

        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)


if __name__ == "__main__":
    unittest.main()