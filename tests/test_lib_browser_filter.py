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

from io import StringIO
from mock import patch
import unittest2 as unittest
from src.lib.browser.filter import Filter
from src.lib.browser.config import Config
from src.core.logger.logger import Logger


class TestBrowserFilter(unittest.TestCase):
    """TestBrowserFilter class"""
    
    def setUp(self):
        
        logger = Logger.log()
        for handler in logger.handlers:
            logger.removeHandler(handler)
            
        self.config = Config({
        'debug' : 1,
        'method' : 'HEAD',
        'indexof' : None,
        'random_agent': False,
        'random_list' : True,
        'threads' : 1000
    })
        
    def test_filter_threads_to_max(self):
        """ Filter.init() test max threads """
        
        with patch('sys.stdout', new=StringIO()):
            Filter(self.config, 300)
            self.assertEqual(self.config.threads, Config.DEFAULT_MAX_THREADS)
            
    def test_filter_threads_to_list_lines(self):
        """ Filter.init() test max lines"""

        with patch('sys.stdout', new=StringIO()):
            Filter(self.config, 10)
            self.assertEqual(self.config.threads, 10)


if __name__ == "__main__":
    unittest.main()