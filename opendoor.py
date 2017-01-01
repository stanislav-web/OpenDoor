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
#    Development Team:
#
#    Stanislav Menshov (Stanislav WEB) https://vk.com/stanislav_web

try:
    import urllib3
    import threadpool
    import linereader
    import colorama
    import coloredlogs
    import termcolor
    import logging
    import verboselogs
    import tabulate

except ImportError:
    Log.critical("""\t\t[!] Several dependencies wasn't installed!
                Please run sudo pip install -r requirements.txt """)

from Libraries import Command, Filter as FilterArgs, Controller, Version

version = Version()
command = Command()
filter_args = FilterArgs()
args = []

Version().banner()

if command.get_arg_values():
    args = filter_args.call(command)
    Controller(args)
