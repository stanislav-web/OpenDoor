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
import sys
import signal
from src.lib.events import EventHandler

@unittest.skipUnless(hasattr(os, 'kill'), "Test requires os.kill")
@unittest.skipIf(sys.platform =="win32", "Test cannot run on Windows")
@unittest.skipIf(sys.platform == 'freebsd6', "Test kills regrtest on freebsd6 "
    "if threads have been used")
class TestEvents(unittest.TestCase):
    """TestEvents class"""

    def test_termination_handler(self):
        """ Events.terminate() exception test """

        EventHandler.terminate()

        self.assertIs('kill_process', signal.getsignal(signal.SIGTSTP).__name__)
        self.assertTrue(None is not signal.getsignal(signal.SIGTERM))

if __name__ == "__main__":
    unittest.main()
