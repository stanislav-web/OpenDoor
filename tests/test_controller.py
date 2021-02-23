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

    Development Team: Brain Storm Team
"""

from __future__ import absolute_import
import unittest
from ddt import ddt, data
from src.core import CoreConfig
from src import Controller, SrcError


@ddt
class TestController(unittest.TestCase):
    """TestController class"""

    def setUp(self):
        self.controller = Controller.__new__(Controller)
        self.config = CoreConfig

    def tearDown(self):
        del self.controller
        del self.config

    def test_init_exception(self):
        """ Controller.init() exception test """

        self.config['info']['required_versions'] = {
            'minor': '4.0',
            'major': '4.5'
        }
        with self.assertRaises(SrcError) as context:
            Controller().scan_action({})
        self.assertTrue(SrcError == context.expected)

    @data( {'version': True}, {'examples': True}, {'update' : True}) #, {'docs' : True}
    def test_run(self, args):
        """ Controller.run() test """
        
        setattr(self.controller, 'ioargs', args)
        self.controller.run()
        self.assertTrue(True)
        
    def test_run_exception(self):
        """ Controller.run() exception test """

        with self.assertRaises(SrcError) as context:
            self.controller.run()
        self.assertTrue(SrcError == context.expected)
    
    def test_scan_action_exception(self):
        """ Controller.scan_action() exception test """
        
        with self.assertRaises(SrcError) as context:
            self.controller.scan_action(params={
                'host': 'http://example.com',
                'port': 80
            })
        self.assertTrue(SrcError == context.expected)

    def test_examples_action(self):
        """ Controller.examples_action() test """

        self.assertIsNone(self.controller.examples_action())

    def test_update_action(self):
        """ Controller.update_action() test """

        self.assertIsNone(self.controller.update_action())

    def test_version_action(self):
        """ Controller.version_action() test """

        self.assertIsNone(self.controller.version_action())

    def test_local_version(self):
        """ Controller.local_version() test """

        self.assertIsNone(self.controller.local_version())


if __name__ == "__main__":
    unittest.main()
