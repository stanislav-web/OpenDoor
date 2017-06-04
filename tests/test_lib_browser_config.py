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
from src.lib.browser.config import Config


class TestBrowserConfig(unittest.TestCase):
    """TestBrowserConfig class"""

    def test_config_properties(self):
        """ Config.init() """
        
        empty_config = Config({})
        self.assertIs(type(Config.scan), property)
        self.assertTrue(str(Config.DEFAULT_SCAN) is str(empty_config.scan))
        
        self.assertIs(type(Config.scheme), property)
        self.assertTrue('http://' is str(Config({'scheme' : 'http://'}).scheme))
        
        self.assertIs(type(Config.is_ssl), property)
        self.assertFalse(empty_config.is_ssl)

        self.assertIs(type(Config.prefix), property)
        self.assertTrue('test/' is str(Config({'prefix': 'test/'}).prefix))

        self.assertIs(type(Config.host), property)
        self.assertTrue('example.com' is str(Config({'host': 'example.com'}).host))

        self.assertIs(type(Config.port), property)
        self.assertTrue(80 is Config({'port': 80}).port)
        
        self.assertIs(type(Config.is_indexof), property)
        self.assertFalse(Config({'is_indexof': False}).is_indexof)
        
        self.assertIs(type(Config.method), property)
        self.assertTrue(str(Config.DEFAULT_HTTP_METHOD) is str(Config({'method' : 'HEAD'}).method))

        self.assertIs(type(Config.delay), property)
        self.assertTrue(1 is Config({'delay' : 1}).delay)

        self.assertIs(type(Config.timeout), property)
        self.assertTrue(Config.DEFAULT_SOCKET_TIMEOUT is Config({'timeout' : 10}).timeout)

        self.assertIs(type(Config.retries), property)
        self.assertTrue(3 is Config({'retries' : 3}).retries)

        self.assertIs(type(Config.debug), property)
        self.assertTrue(1 is Config({'debug' : 1}).debug)
        
        self.assertIs(type(Config.proxy), property)
        self.assertTrue('' is empty_config.proxy)
        
        self.assertIs(type(Config.is_proxy), property)
        self.assertFalse(empty_config.is_proxy)

        self.assertIs(type(Config.is_random_user_agent), property)
        self.assertFalse(empty_config.is_random_user_agent)

        self.assertIs(type(Config.is_random_list), property)
        self.assertFalse(empty_config.is_random_list)
        
        self.assertIs(type(Config.is_standalone_proxy), property)
        self.assertFalse(empty_config.is_standalone_proxy)

        self.assertIs(type(Config.is_internal_torlist), property)
        self.assertFalse(empty_config.is_internal_torlist)

        self.assertIs(type(Config.is_external_torlist), property)
        self.assertFalse(empty_config.is_external_torlist)

        self.assertIs(type(Config.is_external_wordlist), property)
        self.assertFalse(empty_config.is_external_wordlist)
        
        self.assertIs(type(Config.torlist), property)
        self.assertTrue('' is empty_config.torlist)

        self.assertIs(type(Config.reports), property)
        self.assertIs(type(Config({'reports' : 'std'}).reports), list)
        self.assertTrue(Config.DEFAULT_REPORT in Config({'reports' : 'std'}).reports)
        
        self.assertIs(type(Config.user_agent), property)
        self.assertTrue(Config.DEFAULT_USER_AGENT is empty_config.user_agent)

        empty_config.set_threads(Config.DEFAULT_MIN_THREADS)
        self.assertIs(type(Config.threads), property)
        self.assertTrue(empty_config.threads == Config.DEFAULT_MIN_THREADS)
        
        self.assertIs(type(Config.accept_cookies), property)
        self.assertFalse(empty_config.accept_cookies)

if __name__ == "__main__":
    unittest.main()