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
import os
from configparser import RawConfigParser
from ddt import ddt, data
from src.lib.package.config import Config
from src.core import filesystem
from src import Controller, SrcError


@ddt
class TestController(unittest.TestCase):
    """TestController class"""
    
    @property
    def __configuration(self):
        test_config =  filesystem.getabsname(os.path.join('tests', 'data', 'setup.cfg'))
        config = RawConfigParser()
        config.read(test_config)
        return config
    
    def test_init_exception(self):
        """ Controller.init() exception test """

        Config.params['required_versions'] = {
            'minor': '4.0',
            'major': '4.5'
        }
        with self.assertRaises(SrcError) as context:
            Controller().scan_action({})
        self.assertTrue(SrcError == context.expected)

    @data( {'version': True}, {'examples': True}, {'update' : True}, {'docs' : True})
    def test_run(self, args):
        """ Controller.run() test """
        
        Config.params['cfg'] = 'setup.cfg'
        controller = Controller.__new__(Controller)
        setattr(controller, 'ioargs', args)
        controller.run()
        self.assertTrue(True)
        
    def test_run_exception(self):
        """ Controller.run() exception test """

        controller = Controller.__new__(Controller)
        with self.assertRaises(SrcError) as context:
            controller.run()
        self.assertTrue(SrcError == context.expected)
    
    def test_scan_action_exception(self):
        """ Controller.scan_action() exception test """
        
        controller = Controller.__new__(Controller)
        with self.assertRaises(SrcError) as context:
            controller.scan_action(params={
                'host': 'http://example.com',
                'port': 80
            })
        self.assertTrue(SrcError == context.expected)

    def test_examples_action(self):
        """ Controller.examples_action() test """

        Config.params['cfg'] = 'setup.cfg'
        controller = Controller.__new__(Controller)
        self.assertIsNone(controller.examples_action())

    def test_update_action(self):
        """ Controller.update_action() test """

        Config.params['cfg'] = 'setup.cfg'
        controller = Controller.__new__(Controller)
        self.assertIsNone(controller.update_action())

    def test_version_action(self):
        """ Controller.version_action() test """

        Config.params['cfg'] = 'setup.cfg'
        controller = Controller.__new__(Controller)
        self.assertIsNone(controller.version_action())

    def test_local_version(self):
        """ Controller.local_version() test """

        Config.params['cfg'] = 'setup.cfg'
        controller = Controller.__new__(Controller)
        self.assertIsNone(controller.local_version())

    def test_update_action_exception(self):
        """ Controller.update_action() exception test """

        del Config.params['update']
        controller = Controller.__new__(Controller)
        with self.assertRaises(SrcError) as context:
            controller.update_action()
        self.assertTrue(SrcError == context.expected)

    def test_version_action_exception(self):
        """ Controller.version_action() exception test """

        Config.params['cfg'] = 'wrong.cfg'
        controller = Controller.__new__(Controller)
        with self.assertRaises(SrcError) as context:
            controller.version_action()
        self.assertTrue(SrcError == context.expected)

    def test_local_version_action_exception(self):
        """ Controller.local_version() exception test """

        Config.params['cfg'] = 'wrong.cfg'
        controller = Controller.__new__(Controller)
        with self.assertRaises(SrcError) as context:
            controller.local_version()
        self.assertTrue(SrcError == context.expected)
        
if __name__ == "__main__":
    unittest.main()
