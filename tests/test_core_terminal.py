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
from src.core.system.terminal import Terminal
from src.core.system.output import Output

@unittest.skipIf(False is Output().is_windows, "Test can run on Windows")
class TestTerminal(unittest.TestCase):
    """TestTerminal class"""
    
    def test_get_ts_windows(self):
        """ Terminal.__get_ts_windows() test """
        
        term = getattr(Terminal, '_Terminal__get_ts_windows')()
        self.assertIsNotNone(term)

        
if __name__ == "__main__":
    unittest.main()
