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

import sys
import unittest2 as unittest


class TestWorker(unittest.TestCase):
    """ TestWorker class"""

    @unittest.skip("unresolved")
    def test_pause(self):
        """ Worker.pause test """

        pass

    @unittest.skip("unresolved")
    def test_resume(self):
        """ Worker.resume test """

        pass

    @unittest.skip("unresolved")
    def test_exception(self):
        """ Worker.exception test """

        pass

    @unittest.skip("unresolved")
    def test_run(self):
        """ Worker.run test """

        pass

    @unittest.skip("unresolved")
    def test_terminate(self):
        """ Worker.terminate test """

        pass

if __name__ == "__main__":
    unittest.main()
