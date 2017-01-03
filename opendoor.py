#! /usr/bin/env python

""" OWASP OpenDoor launcher """

#    OpenDoor Web Directory Scanner
#    Copyright (C) 2016  Stanislav Menshov
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Development Team: Stanislav Menshov
#
import sys

try:
    import urllib3
    import threadpool
    import linereader
    import colorama
    import coloredlogs
    import termcolor
    import logging
    import tabulate

except ImportError:
    sys.exit("""\t\t[!] Several dependencies wasn't installed!
                Please run sudo pip install -r requirements.txt """)

if __name__ == "__main__":

    from src.lib.options import Options

    options = Options()
    args = options.get_arg_values()
    if args:
        Controller(args)

    # from src.Controller import Controller
    # from src.Version import Version
    # from src.Filter import Filter as FilterArgs
    #
    # version = Version()
    # options = Options()
    # filter_args = FilterArgs()
    # args = options.get_arg_values()
    #
    # version.banner()
    #
    # if args_values:
    #     args = filter_args.call(command)
    #     Controller(args)
