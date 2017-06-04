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

from __future__ import absolute_import
import unittest2 as unittest
from src.core.logger.logger import Logger
from src.lib.io import Arguments, ArgumentsError
from src.core.options.exceptions import ThrowingArgumentParser
# noinspection PyCompatibility
from argparse import RawDescriptionHelpFormatter

class TestArguments(unittest.TestCase):
    """TestArguments class"""
    
    def tearDown(self):
        logger = Logger.log()

        for handler in logger.handlers:
            logger.removeHandler(handler)

    def test_get_arguments_exception(self):
        """ Arguments.get_arguments() exception test """

        with self.assertRaises(SystemExit) as context:
            Arguments.get_arguments()
        self.assertTrue(SystemExit is context.expected)

if __name__ == "__main__":
    unittest.main()
