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
from src.lib.reporter import Reporter, ReporterError
from src.lib.reporter.plugins.provider import PluginProvider
from ddt import ddt, data

@ddt
class TestReporter(unittest.TestCase):
    """TestReporter class"""

    def test_is_reported(self):
        """ Reporter.is_reported() test """

        expected = Reporter.is_reported('resource')
        self.assertIs(type(expected), bool)

    @data('std', 'txt', 'json', 'html')
    def test_load(self, value):
        """ Reporter.load() test """

        expected = Reporter.load(value, 'test.local', {})
        self.assertIsInstance(expected, PluginProvider)

    def test_load_exception(self):
        """ Reporter.load() exception test """

        undefined = 'undefined'
        with self.assertRaises(ReporterError) as context:
            Reporter.load(undefined,'test.local', {})
        self.assertTrue('Unable to get reporter `{plugin}`'.format(plugin=undefined) in context.exception)

if __name__ == "__main__":
    unittest.main()
