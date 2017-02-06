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
from src.lib.reader import Reader
from src.core.filesystem.filesystem import FileSystem
import os, ConfigParser

class TestReader(unittest.TestCase):
    """TestReader class"""

    @property
    def __configuration(self):
        test_config =  FileSystem.getabsname(os.path.join('tests', 'data', 'setup.cfg'))
        config = ConfigParser.RawConfigParser()
        config.read(test_config)
        return config

    def test_total_lines(self):
        """ Reader.total_lines test """

        empty_reader = Reader(browser_config={})
        self.assertIs(type(empty_reader.total_lines), int)


    def test_get_user_agents_empty(self):
        """ Reader.get_user_agents() empty test """

        empty_reader = Reader(browser_config={})
        self.assertIs(type(empty_reader.get_user_agents()), list)

    def test_get_ignored_list_empty(self):
        """ Reader.get_ignored_list() empty test """

        empty_reader = Reader(browser_config={})
        self.assertIs(type(empty_reader.get_ignored_list()), list)

    def test_get_proxies_empty(self):
        """ Reader.get_proxies() empty test """
        
        empty_reader = Reader(browser_config={})
        self.assertIs(type(empty_reader.get_user_agents()), list)

if __name__ == "__main__":
    unittest.main()