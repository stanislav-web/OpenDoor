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
from mock import patch
from src.lib.tpl import Tpl


class TestArguments(unittest.TestCase):
    """TestArguments class"""

    def prompt_answer(self):
        ans = Tpl.prompt(msg='fake')
        return ans

    def test_prompt(self):
        """ Tpl.prompt() test """

        with patch('__builtin__.raw_input', return_value='fake') as _raw_input:
            self.assertEqual(self.prompt_answer(), 'fake')
            _raw_input.assert_called_once_with('fake')

if __name__ == "__main__":
    unittest.main()