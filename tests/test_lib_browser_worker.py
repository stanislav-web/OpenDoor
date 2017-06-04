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
from src.lib.browser.worker import Worker
# noinspection PyCompatibility
from queue import Queue


class TestBrowserWorker(unittest.TestCase):
    """TestBrowserWorker class"""
    
    THREADS = 1
    
    def _kill_waiting_thread(self):
        exit()
        
    def setUp(self):
        self._worker = Worker(Queue(self.THREADS), num_threads=self.THREADS, timeout=0)
    
    def tearDown(self):
        with self.assertRaises(SystemExit):
            self._kill_waiting_thread()
            self._worker.join(1)

    def test_pause(self):
        """ Worker.pause() test """
        
        self.assertEqual(self._worker.pause(), None)
        self.assertFalse(getattr(self._worker, '_Worker__running', True))

if __name__ == "__main__":
    unittest.main()