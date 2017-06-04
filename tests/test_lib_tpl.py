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

    Development Team: Stanislav WEB
"""

import unittest2 as unittest
from src.core.logger.logger import Logger
from io import StringIO
from mock import patch
from src.lib.tpl import Tpl, TplError


class TestTpl(unittest.TestCase):
    """TestTpl class"""
    
    def tearDown(self):
        logger = Logger.log()
        for handler in logger.handlers:
            logger.removeHandler(handler)

    def prompt_answer(self):
        ans = Tpl.prompt(msg='fake')
        return ans

    def test_cancel(self):
        """ Tpl.cancel() test """
    
        with self.assertRaises(SystemExit) as context:
            Tpl.cancel(key='abort')
        self.assertTrue(SystemExit == context.expected)

        
    def test_cancel_exception(self):
        """ Tpl.cancel() exception test """

        undefined = 'undefined'
        with self.assertRaises(TplError) as context:
            Tpl.cancel(key=undefined)
        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)
        
    def test_prompt(self):
        """ Tpl.prompt() test """

        with patch('builtins.input', return_value='fake') as _raw_input:
            self.assertEqual(self.prompt_answer(), 'fake')
            _raw_input.assert_called_once_with('fake')

    def test_prompt_exception(self):
        """ Tpl.prompt() exception test """
        
        undefined = 'undefined'
        with self.assertRaises(TplError) as context:
            Tpl.prompt(key=undefined)
        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)

    def test_line(self):
        """ Tpl.line() test """

        expected = Tpl.line('test')
        self.assertTrue('test' in expected)
    
    def test_line_with_key(self):
        """ Tpl.line() test with key """
        
        expected = Tpl.line(key='report', plugin='testplugin', dest='testdst')
        self.assertTrue('testplugin' in expected)
        self.assertTrue('testdst' in expected)

    def test_line_log(self):
        """ Tpl.line_log() test """

        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            Tpl.line_log('test_line_log')
            self.assertTrue('test_line_log' in fakeOutput.getvalue().strip())
    
    def test_line_log_exception(self):
        """ Tpl.line_log() exception test """

        undefined = 'undefined'
        with self.assertRaises(TplError) as context:
            Tpl.line_log(key=undefined)
        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)
        
    def test_message(self):
        """ Tpl.message() test """

        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            Tpl.message('test_message')
            self.assertTrue('test_message' in fakeOutput.getvalue().strip())

    def test_error(self):
        """ Tpl.error() test """

        with patch('sys.stderr', new=StringIO()) as fakeOutput:
            Tpl.error('test_error')
            self.assertTrue('' in fakeOutput.getvalue().strip())

    def test_warning(self):
        """ Tpl.warning() test """

        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            Tpl.warning('test_warning')
            self.assertTrue('' in fakeOutput.getvalue().strip())

    def test_line_exception(self):
        """ Tpl.line() exception test """

        undefined = 'undefined'
        with self.assertRaises(TplError) as context:
            Tpl.line(key=undefined)
        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)

    def test_info(self):
        """ Tpl.info() test """
    
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            Tpl.info('test_info')
            self.assertTrue('' in fakeOutput.getvalue().strip())
    
    def test_error_exception(self):
        """ Tpl.error() exception test """

        undefined = 'undefined'
        with self.assertRaises(TplError) as context:
            Tpl.error(key=undefined)
        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)
        
    def test_info_exception(self):
        """ Tpl.info() exception test """

        undefined = 'undefined'
        with self.assertRaises(TplError) as context:
            Tpl.info(key=undefined)
        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)
        
    def test_warning_exception(self):
        """ Tpl.warning() exception test """

        undefined = 'undefined'
        with self.assertRaises(TplError) as context:
            Tpl.warning(key=undefined)
        self.assertTrue(undefined in str(context.exception))
        self.assertTrue(TplError == context.expected)
            
if __name__ == "__main__":
    unittest.main()