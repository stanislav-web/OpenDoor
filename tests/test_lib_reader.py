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
import os
from configparser import RawConfigParser
from src.core.helper.helper import Helper
from src.lib.reader import Reader, ReaderError
from src.core.filesystem.filesystem import FileSystem
from src.core.system.output import Output as sys
from src.core.logger.logger import Logger


class TestReader(unittest.TestCase):
    """TestReader class"""
    
    def tearDown(self):
        logger = Logger.log()
        for handler in logger.handlers:
            logger.removeHandler(handler)

    def __uri_validator(self, urllist):
        for url in urllist:
            try:
                result = Helper.parse_url(url)
                return True if [result.scheme, result.netloc, result.path] else False
            except:
                return False

    def __callback_function(self, string):
        """ Test callback url from list """

        self.assertTrue(self.__uri_validator(string))

    @property
    def __configuration(self):
        test_config =  FileSystem.getabsname(os.path.join('tests', 'data', 'setup.cfg'))
        config = RawConfigParser()
        config.read(test_config)
        return config

    @property
    def __configuration_for_exception(self):
        test_config =  FileSystem.getabsname(os.path.join('tests', 'data', 'setupwrong.cfg'))
        config = RawConfigParser()
        config.read(test_config)
        return config

    def test_get_user_agents_exception(self):
        """ Reader.get_user_agents() exception test """

        reader = Reader(browser_config={})
        setattr(reader, '_Reader__config', self.__configuration_for_exception)
        with self.assertRaises(ReaderError) as context:
            reader.get_user_agents()
            self.assertTrue(ReaderError == context.expected)

    def test_get_proxies_exception(self):
        """ Reader.get_proxies() exception test """

        reader = Reader(browser_config={
            'is_standalone_proxy' : False,
            'is_external_torlist' : True,
            'torlist' : '/notfound'
        })
        setattr(reader, '_Reader__config', self.__configuration_for_exception)
        with self.assertRaises(ReaderError) as context:
            reader.get_proxies()
            self.assertTrue(ReaderError == context.expected)

    def test_get_ignored_list_exception(self):
        """ Reader.get_ignored_list() exception test """

        reader = Reader(browser_config={})
        setattr(reader, '_Reader__config', self.__configuration_for_exception)
        with self.assertRaises(ReaderError) as context:
            reader.get_ignored_list()
            self.assertTrue(ReaderError == context.expected)

    def test_get_user_agents_empty(self):
        """ Reader.get_user_agents() empty test """

        empty_reader = Reader(browser_config={})
        self.assertIs(type(empty_reader.get_user_agents()), list)

    def test_get_ignored_list_empty(self):
        """ Reader.get_ignored_list() empty test """

        empty_reader = Reader(browser_config={})
        self.assertIs(type(empty_reader.get_ignored_list()), list)

    def test_get_proxies(self):
        """ Reader.get_proxies() test """

        reader = Reader(browser_config={
            'is_standalone_proxy' : False
        })
        setattr(reader, '_Reader__config', self.__configuration)
        proxies = reader.get_proxies()
        self.assertIs(type(proxies), list)
        self.assertTrue(0 < len(proxies))

    def test_get_proxies_empty(self):
        """ Reader.get_proxies() empty test """

        empty_reader = Reader(browser_config={})
        self.assertIs(type(empty_reader.get_proxies()), list)

    def test_get_lines_exception(self):
        """ Reader.get_lines() exception test """

        reader = Reader(browser_config={
            'is_standalone_proxy' : False,
            'list' : 'directories'
        })
        setattr(reader, '_Reader__config', self.__configuration_for_exception)
        with self.assertRaises(ReaderError) as context:
            reader.get_lines(params={}, loader=self.__callback_function)
            self.assertTrue(ReaderError == context.expected)

    def test_get_lines_directories(self):
        """ Reader.get_lines() directories test """

        reader = Reader(browser_config={
            'is_standalone_proxy' : False,
            'list' : 'directories',
            'prefix': '',
        })
        setattr(reader, '_Reader__config', self.__configuration)
        self.assertIsNone(reader.get_lines(params={
            'scheme': 'http://',
            'host': 'localhost.local',
            'port': 80
        }, loader=self.__callback_function))

    def test_get_lines_subdomains(self):
        """ Reader.get_lines() subdomains test """

        reader = Reader(browser_config={
            'is_standalone_proxy' : False,
            'list' : 'subdomains',
            'prefix': '',
        })
        setattr(reader, '_Reader__config', self.__configuration)
        self.assertIsNone(reader.get_lines(params={
            'scheme': 'http://',
            'host': 'localhost.local',
            'port': 80
        }, loader=self.__callback_function))

    def test_count_total_lines_exception(self):
        """ Reader.count_total_lines() exception test """

        reader = Reader(browser_config={
            'is_standalone_proxy' : False,
            'list' : 'subdomains',
            'prefix': '',
        })
        setattr(reader, '_Reader__config', self.__configuration_for_exception)
        with self.assertRaises(ReaderError) as context:
            reader.count_total_lines()
            self.assertTrue(ReaderError == context.expected)

    def test_count_total_lines(self):
        """ Reader.count_total_lines() test """

        reader = Reader(browser_config={
            'is_external_wordlist' : True,
            'list' : 'tests/data/directories.dat',
        })
        setattr(reader, '_Reader__config', self.__configuration)
        setattr(reader, '_Reader__counter', 0)
        self.assertIs(type(reader.count_total_lines()), int)
        self.assertTrue(0 < reader.count_total_lines())
        self.assertIs(15 ,reader.count_total_lines())

    def test_total_lines(self):
        """ Reader.total_lines test """

        empty_reader = Reader(browser_config={})
        self.assertIs(type(empty_reader.total_lines), int)

    def test_randomize_list_exception(self):
        """ Reader.randomize_list exception test """

        reader = Reader(browser_config={})
        setattr(reader, '_Reader__config', self.__configuration_for_exception)
        setattr(sys, '_Output__is_windows', False)
        with self.assertRaises(ReaderError) as context:
            reader.randomize_list('directories', 'tmplist')
            self.assertTrue(ReaderError == context.expected)

    @unittest.skipIf(True is sys().is_windows, "Skip test for windows")
    def test_randomize_list_unix(self):
        """ Reader.randomize_list unix test """

        reader = Reader(browser_config={
            'is_external_wordlist': True,
            'list': 'tests/data/directories.dat',
        })
        setattr(reader, '_Reader__config', self.__configuration)
        reader.count_total_lines()
        self.assertIsNone(reader.randomize_list('directories', 'tmplist'))
        fe = open('tests/data/directories.dat', 'r')
        fa = open('tests/tmp/list.tmp', 'r')
        expected = sum(1 for l in fe)
        actual = sum(1 for l in fa)
        self.assertIs(expected, actual)

    def test_randomize_list_windows(self):
        """ Reader.randomize_list windows test """

        reader = Reader(browser_config={
            'is_external_wordlist': True,
            'list': 'tests/data/directories.dat',
        })
        setattr(reader, '_Reader__config', self.__configuration)
        setattr(sys, 'is_windows', True)
        reader.count_total_lines()
        self.assertIsNone(reader.randomize_list('directories', 'tmplist'))
        fe = open('tests/data/directories.dat', 'r')
        fa = open('tests/tmp/list.tmp', 'r')
        expected = sum(1 for l in fe)
        actual = sum(1 for l in fa)
        self.assertIs(expected, actual)

if __name__ == "__main__":
    unittest.main()