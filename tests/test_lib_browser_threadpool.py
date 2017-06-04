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
from mock import patch
from src.lib.browser.threadpool import ThreadPool
from src.core.logger.logger import Logger


class TestBrowserThreadPool(unittest.TestCase):
    """TestBrowserThreadPool class"""
    
    THREADS = 2
    
    def __test_function(self,arg):
        pass
    
    def setUp(self):
        self._pool = ThreadPool(num_threads=self.THREADS, total_items=10, timeout=0)
    
    def tearDown(self):
        logger = Logger.log()
        for handler in logger.handlers:
            logger.removeHandler(handler)
        self._pool.join()

    def test_size(self):
        """ ThreadPool.size test """
        
        self.assertIs(type(self._pool.size), int)
        self.assertEqual(self._pool.size, 0)

    def test_worker_size(self):
        """ ThreadPool.worker_size test """
    
        self.assertIs(type(self._pool.workers_size), int)
        self.assertEqual(self._pool.workers_size, self.THREADS)

    def test_items_size(self):
        """ ThreadPool.items_size test """
    
        self.assertIs(type(self._pool.items_size), int)
        self.assertEqual(self._pool.items_size, 0)

    def test_add(self):
        """ ThreadPool.add() test """
    
        self.assertIs(self._pool.add(self.__test_function, 1), None)
    
    def pause(self):
        ans = self._pool.pause()
        return ans
    
    def test_pause(self):
        """ ThreadPool.pause() test """
        
        with self.assertRaises(KeyboardInterrupt) as context:
            with patch('builtins.input', return_value='e') as _raw_input:
                self.assertEqual(self.pause(), 'e')
                _raw_input.assert_called_once_with('e')
            self.assertTrue(KeyboardInterrupt == context.expected)

    def test_resume(self):
        """ ThreadPool.resume() test """
        
        self._pool.is_started = False
        self.assertIs(self._pool.resume(), None)


if __name__ == "__main__":
    unittest.main()