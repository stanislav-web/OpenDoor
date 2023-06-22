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

    Development Team: Brain Storm Team
"""

import sys
from .controller import Controller
from .exceptions import SrcError

for _ in ['urllib3', 'json2html', 'tabulate', 'importlib', 'packaging']:
    try:
        __import__(_)
    except ImportError as error:
        sys.exit("""\t\t[!] Several dependencies wasn't installed! Please run pip install -r requirements.txt. 
        Details : %s.""" % error)


def main():
    """
    This function loads the package and runs the Controller class.

    :except SrcError: Raises an exception if there is an error in the source code.
    :return: None
    """
    try:
        bootstrap = Controller()
        bootstrap.run()
    except SrcError:
        sys.exit()


if __name__ == "__main__":
    main()
