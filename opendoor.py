#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" OWASP OpenDoor launcher

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

for _ in ['urllib3', 'json2html', 'tabulate', 'importlib']:
    try:
        __import__(_)
    except ImportError:
        sys.exit("""\t\t[!] Several dependencies wasn't installed!
            Please run sudo pip install -r requirements.txt """)

if __name__ == "__main__":

    from src import Controller, SrcError

    try:
        bootstrap = Controller()
        bootstrap.run()
    except SrcError:
        sys.exit()
