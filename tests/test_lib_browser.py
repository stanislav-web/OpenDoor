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
from src.lib import browser
import os, ConfigParser
from src.core import filesystem, helper

class TestBrowser(unittest.TestCase):
    """TestBrowser class"""

    @property
    def __configuration(self):
        test_config = filesystem.getabsname(os.path.join('tests', 'data', 'setup.cfg'))
        config = ConfigParser.RawConfigParser()
        config.read(test_config)
        return config

    #
    # def test_done(self):
    #     """ Debug.level test """
    #
    #     br = browser.__new__(browser)
    #     result = {}
    #     result['total'] = helper.counter()
    #     result['items'] = helper.list()
    #     setattr(br, '_Browser__result.DEFAULT_SCAN', 'directories')
    #
    #     br.done()



if __name__ == "__main__":
    unittest.main()