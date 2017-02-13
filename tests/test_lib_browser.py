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
from src.lib import browser, BrowserError
from src.lib.browser.threadpool import ThreadPool
from src.lib.browser.config import Config
from src.lib.browser.debug import Debug
from src.lib.reader.reader import Reader
from src.lib.tpl.tpl import Tpl
from src.core.http.response import Response
import os, ConfigParser
from ddt import ddt, data
from src.core import filesystem, helper


@ddt
class TestBrowser(unittest.TestCase):
    """TestBrowser class"""

    THREADS = 1

    @property
    def __configuration(self):
        test_config = filesystem.getabsname(os.path.join('tests', 'data', 'setup-scan.cfg'))
        config = ConfigParser.RawConfigParser()
        config.read(test_config)
        return config

    def setUp(self):
        self.__pool = ThreadPool(num_threads=self.THREADS, total_items=10, timeout=0)
        self.__config = Config({'host' : 'example.com', 'port' : 80, 'debug': 3})

    def tearDown(self):
        del self.__pool

    def __browser_configuration(self, params):
        test_config = Config(params)
        return test_config

    def __browser_init(self, params):
        br = browser(params)
        return br

    def test_init(self):
        """ Browser.init() test """

        br = self.__browser_init({'host' : 'test.local', 'port' : 80})
        __client = getattr(br, '_Browser__client')
        __config = getattr(br, '_Browser__config')
        __debug = getattr(br, '_Browser__debug')
        __result = getattr(br, '_Browser__result')
        __reader = getattr(br, '_Browser__reader')
        __pool = getattr(br, '_Browser__pool')
        __response = getattr(br, '_Browser__response')

        self.assertIs(__client, None)
        self.assertTrue(isinstance(__config, Config))
        self.assertTrue(isinstance(__debug, Debug))
        self.assertTrue(isinstance(__result, dict))
        self.assertTrue(isinstance(__reader, Reader))
        self.assertTrue(isinstance(__pool, ThreadPool))
        self.assertTrue(isinstance(__response, Response))

    def test_scan(self):
        """ Browser.scan() test """

        br = browser.__new__(browser)
        reader = Reader(browser_config={
                'list': self.__config.scan,
                'torlist': self.__config.torlist,
                'use_random': self.__config.is_random_list,
                'is_external_wordlist': self.__config.is_external_wordlist,
                'is_standalone_proxy': self.__config.is_standalone_proxy,
                'is_external_torlist': self.__config.is_external_torlist,
                'prefix': self.__config.prefix
            })
        result = {}
        result['total'] = helper.counter()
        result['items'] = helper.list()

        setattr(reader, '_Reader__config', self.__configuration)
        setattr(br, '_Browser__debug', Debug(self.__config))
        setattr(br, '_Browser__pool', self.__pool)
        setattr(br, '_Browser__config', self.__config)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__response', Response(config=self.__config, debug=Debug(self.__config), tpl=Tpl))
        setattr(br, '_Browser__result', result)
        self.assertIs(br.scan(), None)

    @data({'reports' : 'std', 'host' : 'example.com', 'port' : 80})
    def test_ping(self, params):
        """ Browser.ping() test """

        br = browser.__new__(browser)
        setattr(br, '_Browser__config', self.__browser_configuration(params))
        self.assertIs(br.ping(), None)

    @data({'reports' : 'std', 'host' : 'test.local'})
    def test_done(self, params):
        """ Browser.done() test """

        br = browser.__new__(browser)
        result = {}

        result['total'] = helper.counter()
        result['items'] = helper.list()
        setattr(br, '_Browser__result', result)
        setattr(br, '_Browser__pool', self.__pool)
        setattr(br, '_Browser__pool.size', 0)
        setattr(br, '_Browser__config', self.__browser_configuration(params))
        self.assertIs(br.done(), None)

    @data({'reports' : 'raisesexc', 'host' : 'test.local'})
    def test_done_exception(self, params):
        """ Browser.done() exception test """

        br = browser.__new__(browser)
        result = {}

        result['total'] = helper.counter()
        result['items'] = helper.list()
        setattr(br, '_Browser__result', result)
        setattr(br, '_Browser__pool', self.__pool)
        setattr(br, '_Browser__pool.size', 0)
        setattr(br, '_Browser__config', self.__browser_configuration(params))

        with self.assertRaises(BrowserError) as context:
            br.done()
        self.assertTrue('raisesexc' in str(context.exception))
        self.assertTrue(BrowserError == context.expected)


if __name__ == "__main__":
    unittest.main()