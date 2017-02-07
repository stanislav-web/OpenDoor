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
from src.lib.browser.debug import Debug
from src.lib.browser.config import Config
from mock import patch, Mock, PropertyMock
from StringIO import StringIO

class TestBrowserDebug(unittest.TestCase):
    """TestBrowserDebug class"""

    CONFIG = Config({
        'debug' : 1,
        'method' : 'HEAD',
        'indexof' : None,
        'random_agent': False,
        'random_list' : True,
        'threads' : 1
    })

    def setUp(self):
        with patch('sys.stdout', new=StringIO()):
            self.debug = Debug(self.CONFIG)

    def tearDown(self):
        StringIO().flush()
        del self.debug

    def test_level(self):
        """ Debug.level test """

        self.assertIs(type(self.debug.level), int)
        self.assertTrue(0 < self.debug.level)

    def test_debug_request_uri(self):
        """ Debug.debug_request_uri() test """

        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(self.debug.debug_request_uri(200,'http://test.local/data/'))

    def test_debug_request(self):
        """ Debug.debug_request() test """

        self.assertTrue(self.debug.debug_request({},'http://test.local/data/', 'HEAD'))

    def test_debug_response(self):
        """ Debug.debug_response() test """

        self.assertTrue(self.debug.debug_response(response_header={}))

    def test_debug_list(self):
        """ Debug.debug_list() test """

        self.assertTrue(self.debug.debug_list(1))

    def test_debug_connection_pool(self):
        """ Debug.debug_connection_pool() test """

        self.assertTrue(self.debug.debug_connection_pool('http_pool_start', ''))

    def test_debug_proxy_pool(self):
        """ Debug.debug_proxy_pool() test """

        self.assertTrue(self.debug.debug_proxy_pool())

    def test_debug_user_agents(self):
        """ Debug.debug_user_agents() test """
        self.assertTrue(self.debug.debug_user_agents())


if __name__ == "__main__":
    unittest.main()