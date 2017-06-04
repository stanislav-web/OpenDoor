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
from configparser import ConfigParser

from src.core import filesystem
from src.lib.reporter import Reporter, ReporterError
from src.lib.reporter.plugins.provider import PluginProvider
from ddt import ddt, data
from src.core.logger.logger import Logger
import shutil


@ddt
class TestReporter(unittest.TestCase):
    """TestReporter class"""
    
    @property
    def __configuration(self):
        test_config =  filesystem.getabsname(os.path.join('tests', 'data', 'setup.cfg'))
        config = ConfigParser.RawConfigParser()
        config.read(test_config)
        return config
    
    def setUp(self):
        self.mockdata = {
            "items": {
                "failed": [
      "http://test.local/swfobject.js",
      "http://test.local/swfobject.php",
      "http://test.local/swfobject/",
      "http://test.local/swfs/",
      "http://test.local/swfupload.php",
      "http://test.local/swfupload/",
      "http://test.local/swift/",
      "http://test.local/login/",
      "http://test.local/users/",
      "http://test.local/swiss/",
      "http://test.local/switch.php",
      "http://test.local/switch/",
      "http://test.local/switcher/",
      "http://test.local/switchover/",
      "http://test.local/switchoverfiles/"
    ],
                "success": [
      "http://test.local/cron/exp.php",
      "http://test.local/cron/cron-online.php"
    ]
            },
            "total": {
    "failed": 15,
    "items": 17,
    "success": 2,
    "workers": 1
            }
        }
        PluginProvider.CONFIG_FILE = 'tests/data/setup.cfg'
        
    def tearDown(self):
        logger = Logger.log()
        for handler in logger.handlers:
            logger.removeHandler(handler)
        
    def test_is_reported(self):
        """ Reporter.is_reported() test """

        expected = Reporter.is_reported('resource')
        self.assertIs(type(expected), bool)
        
    def test_is_reported_error(self):
        """ Reporter.is_reported() exception test """
        rp = Reporter
        setattr(rp, 'config', 'wrong.cfg')
        with self.assertRaises(ReporterError) as context:
            rp.is_reported('resource')
            
            self.assertTrue(ReporterError == context.expected)
        
    def test_plugin_provider_invalid_data_exception(self):
        """ PluginProvider.init() exception test """

        with self.assertRaises(TypeError) as context:
            PluginProvider('test.local', 'wrongdata')
            self.assertTrue(TypeError == context.expected)

    def test_plugin_provider_invalid_record(self):
        """ PluginProvider.record() exception test """

        provider = PluginProvider('test.local', self.mockdata)
        with self.assertRaises(Exception) as context:
            provider.record('wrongdir', self.mockdata)
            self.assertTrue(Exception == context.expected)

    @data('std', 'txt', 'json', 'html')
    def test_load(self, value):
        """ Reporter.load() test """

        expected = Reporter.load(value, 'test.local', {})
        self.assertIsInstance(expected, PluginProvider)
        
    @data('std', 'txt', 'json', 'html')
    def test_process(self, ext):
        """ Reporter.load().process() test """

        report = Reporter.load(ext, 'test.local', self.mockdata)
        self.assertIsNone(report.process())
        if ext in ['html','json']:
            self.assertTrue(filesystem.is_exist('tests/reports/test.local', 'test.local.{0}'.format(ext)))
        if ext in ['txt']:
            self.assertTrue(filesystem.is_exist('tests/reports/test.local', 'success.{0}'.format(ext)))
        shutil.rmtree('tests/reports')
        
    @data('std', 'txt', 'json', 'html')
    def test_load_plugin_exception(self, ext):
        """ Reporter.load() exception test """
        
        if ext in ['html','json', 'txt']:

            PluginProvider.CONFIG_FILE = 'wrong.cfg'
            with self.assertRaises(Exception) as context:
                Reporter.load(ext, 'test.local', self.mockdata)
                self.assertTrue(Exception == context.expected)
       

    def test_load_exception(self):
        """ Reporter.load() exception test """

        undefined = 'undefined'
        with self.assertRaises(ReporterError) as context:
            Reporter.load(undefined,'test.local', {})
            self.assertTrue('Unable to get reporter `{plugin}`'.format(plugin=undefined) in context.exception)
            self.assertTrue(ReporterError == context.expected)

if __name__ == "__main__":
    unittest.main()
