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

import sys
import unittest2 as unittest
from src.lib.package import Package
from src.core.filesystem import FileSystem

class TestPackage(unittest.TestCase):
    """TestPackage class"""

    def test_check_interpreter(self):
        """ Package.check_interpreter() test """

        expected = Package.check_interpreter()
        self.assertTrue(expected)

    @unittest.skip("unresolved")
    def test_examples(self):
        """ Package.examples() test """

        pass

    @unittest.skip("unresolved")
    def test_banner(self):
        """ Package.banner() test """

        pass

    @unittest.skip("unresolved")
    def test_version(self):
        """ Package.version() test """

        pass

    @unittest.skip("unresolved")
    def test_update(self):
        """ Package.update() test """

        pass

    def test_local_version(self):
        """ Package.local_version() test """

        actual = FileSystem.readcfg('setup.cfg').get('info', 'version')
        expected = Package.local_version()
        self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()