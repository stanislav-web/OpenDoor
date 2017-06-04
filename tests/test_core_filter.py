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
from ddt import ddt, data
from src.core.options.filter import Filter

@ddt
class TestFilter(unittest.TestCase):
    """TestFilter class"""
    
    @data(
            {'host': 'example.com', 'port': 80, 'debug': 1},
            {'host': 'https://example.com', 'port': 223, 'debug': 1},
            {'host': 'example.com','debug': 1, 'scan': 'directories'},
            {'host': 'example.com','debug': 1, 'scan': 'subdomains'}
    )
    def test_filter(self, args):
        """ Filter.filter() test """
        
        flt = Filter.filter(args)
        self.assertIs(type(flt), dict)

      
        
if __name__ == "__main__":
    unittest.main()
