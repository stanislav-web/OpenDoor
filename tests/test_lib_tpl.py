# # -*- coding: utf-8 -*-
#
# """
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Development Team: Stanislav WEB
# """
#
# import unittest2 as unittest
# from io import StringIO
# from mock import patch
# from src.lib.tpl import Tpl
#
#
# class TestTpl(unittest.TestCase):
#     """TestTpl class"""
#
#     def test_cancel(self):
#         """ Tpl.line() test """
#
#         expected_string = 'test'
#         actual_string = Tpl.line(expected_string)
#         print actual_string
#         exit()
#         self.assertTrue(expected_string in actual_string)
#
#
#     # def test_cancel(self):
#     #     """ Tpl.cancel() test """
#     #
#     #     expected_string = 'test'
#     #
#     #     with patch('sys.stdout', new=StringIO()) as fake_out:
#     #         Tpl.cancel(expected_string)
#     #         self.assertTrue(fake_out.getvalue() in expected_string)
#
#
# if __name__ == "__main__":
#     unittest.main()