#!/usr/bin/env python3
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

    Development: Stanislav WEB
"""

import sys
from .controller import Controller
from .exceptions import SrcError

for _ in ['urllib3', 'importlib', 'packaging']:
    try:
        __import__(_)
    except ImportError as error:
        sys.exit("""\t\t[!] Several dependencies wasn't installed! Please run pip install -r requirements.txt.
        Details : %s.""" % error)


def main():
    """
    Load the package and run the controller.

    Console-script entrypoints wrap this function in ``sys.exit(...)``.
    Returning the controller exit code keeps installed ``opendoor`` behavior
    aligned with the direct ``python opendoor.py`` launcher.

    :return: Process exit code.
    :rtype: int
    """
    try:
        bootstrap = Controller()
        return bootstrap.run() or 0
    except SrcError:
        return 1


if __name__ == "__main__":
    sys.exit(main())
