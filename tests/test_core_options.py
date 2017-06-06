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
# noinspection PyCompatibility
import argparse
from ddt import ddt, data
from src.core.options import Options
from src.core.options.exceptions import OptionsError

@ddt
class TestOptions(unittest.TestCase):
    """TestOptions class"""

    @data(
            {'version': True, 'examples': False, 'update': None, 'docs' : None},
            {'examples': True, 'version': None, 'update': False, 'docs' : None},
            {'update': True , 'version': False, 'examples': False, 'docs' : None}
    )
    def test_get_arg_values_standalone(self, data):
        """ Arguments.get_arg_values() standalone call test """
    
        opt = Options.__new__(Options)
        args = argparse.Namespace()
        args.host = ''
        args.version = data.get('version')
        args.update = data.get('update')
        args.examples = data.get('examples')
        args.docs = data.get('docs')
        setattr(opt, '_Options__standalone', ["version", "update", "examples","docs"])
        setattr(opt, 'args', args)
        actual = opt.get_arg_values()
        self.assertTrue(isinstance(actual, dict))
        self.assertTrue(1 == len(actual))

    @data(
            {'host': 'example.com', 'port': 80},
            {'host': 'https://example.com', 'port': 223},
            {'host': 'example.com','scan': 'directories'},
            {'host': 'example.com','scan': 'subdomains'},
            {'host': 'example.com', 'proxy': '127.0.0.1'},
    )
    def test_get_arg_values(self, data):
        """ Arguments.get_arg_values() test """

        opt = Options.__new__(Options)
        args = argparse.Namespace()
        args.host = data.get('host')
        args.port = data.get('port')
        args.scan = data.get('scan')
        args.version = False
        args.update = False
        args.examples = False
        args.docs = False
        setattr(opt, '_Options__standalone', ["version", "update", "examples", "docs"])
        setattr(opt, 'args', args)
        actual = opt.get_arg_values()
        self.assertTrue(isinstance(actual, dict))

    def test_get_arg_values_exception2(self):
        """ Arguments.get_arg_values() exception2 test """

        opt = Options.__new__(Options)
        setattr(opt, '_Options__standalone', ["version", "update", "examples", "docs"])
        setattr(opt, 'args', {})
        with self.assertRaises(OptionsError) as context:
            opt.get_arg_values()
        self.assertTrue(OptionsError == context.expected)

    def test_get_arg_values_exception3(self):
        """ Arguments.get_arg_values() exception3 test """

        opt = Options.__new__(Options)
        args = argparse.Namespace()
        args.host = ''
        args.version = False
        args.update = False
        args.examples = False
        args.docs = False
        setattr(opt, '_Options__standalone', ["version", "update", "examples", "docs"])
        setattr(opt, 'args', args)
        with self.assertRaises(OptionsError) as context:
            opt.get_arg_values()
        self.assertTrue(OptionsError == context.expected)

if __name__ == "__main__":
    unittest.main()
