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
from src.core import sys
from src.lib.package import Package, PackageError
from src.lib.package.config import Config
from src.core.filesystem import FileSystem
from src.core.logger.logger import Logger


class TestPackage(unittest.TestCase):
    """TestPackage class"""
    
    def tearDown(self):
        logger = Logger.log()

        for handler in logger.handlers:
            logger.removeHandler(handler)
            
    def test_check_interpreter(self):
        """ Package.check_interpreter() test """

        expected = Package.check_interpreter()
        self.assertTrue(expected)

    def test_examples(self):
        """ Package.examples() test """

        expected = Package.examples()
        self.assertIsNotNone(expected)
        self.assertIs(type(expected), str)

    def test_banner(self):
        """ Package.banner() test """

        Config.params['cfg'] = 'setup.cfg'
        expected = Package.banner()
        self.assertIsNotNone(expected)
        self.assertIs(type(expected), str)

    def test_version(self):
        """ Package.version() test """

        Config.params['cfg'] = 'setup.cfg'
        expected = Package.version()
        self.assertIsNotNone(expected)
        self.assertIs(type(expected), str)

    def test_update_unix(self):
        """ Package.update() unix test """

        Config.params['cfg'] = 'setup.cfg'
        Config.params['update'] = '{status}'
        expected = Package.update()
        self.assertIsNotNone(expected)
        self.assertIs(type(expected), str)

    def test_update_windows(self):
        """ Package.update() test """

        Config.params['cfg'] = 'setup.cfg'
        Config.params['update'] = '{status}'
        setattr(sys, 'is_windows', True)
        expected = Package.update()
        self.assertIsNotNone(expected)

    def test_local_version(self):
        """ Package.local_version() test """

        Config.params['cfg'] = 'setup.cfg'
        actual = FileSystem.readcfg('setup.cfg').get('info', 'version')
        expected = Package.local_version()
        self.assertEqual(actual, expected)

    def test_local_version_exception(self):
        """ Package.local_version() exception test """

        Config.params['cfg'] = 'wrong.cfg'
        with self.assertRaises(PackageError) as context:
            Package.local_version()
            self.assertTrue(PackageError == context.expected)

    def test_update_exception(self):
        """ Package.update() exception test """
        Config.params['cvsupdate'] = 'wrongcvs'
        with self.assertRaises(PackageError) as context:
            Package.update()
            self.assertTrue(PackageError == context.expected)
        Config.params['cvsupdate'] = '/usr/bin/git pull origin master'

    def test_version_exception(self):
        """ Package.version() exception test """

        Config.params['cfg'] = 'wrong.cfg'
        with self.assertRaises(PackageError) as context:
            Package.version()
            self.assertTrue(PackageError == context.expected)

    def test_banner_exception(self):
        """ Package.banner() exception test """

        Config.params['cfg'] = 'wrong.cfg'
        with self.assertRaises(PackageError) as context:
            Package.banner()
            self.assertTrue(PackageError == context.expected)
            
if __name__ == "__main__":
    unittest.main()
