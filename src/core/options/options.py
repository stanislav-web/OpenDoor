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

from argparse import RawDescriptionHelpFormatter

from .exceptions import ArgumentParserError, ThrowingArgumentParser, OptionsError, FilterError
from .filter import Filter


class Options(object):
    """Options class"""

    def __init__(self):
        """
        Constructor
        :raise OptionsError
        """

        self.__standalone = ["version", "update", "examples"]

        __groups = {
            'request': "Request tools",
            'stream': "Stream tools",
            'debug': "Debug tools",
            'wordlist': "Wordlist tools",
            'sniff': "Sniff tools",
            'app': "Application tools"
        }

        __arguments = [
            {
                "group": "request",
                "args": "-p",
                "argl": "--port",
                "default": 80,
                "action": "store",
                "help": "Custom port (Default 80)",
                "type": int
            },
            {
                "group": "request",
                "args": "-m",
                "argl": "--method",
                "default": "HEAD",
                "action": "store",
                "help": "HTTP method (use HEAD as default)",
                "type": str
            },
            {
                "group": "stream",
                "args": "-t",
                "argl": "--threads",
                "default": 1,
                "action": "store",
                "help": "Allowed threads",
                "type": int
            },
            {
                "group": "request",
                "args": "-d",
                "argl": "--delay",
                "default": 0,
                "action": "store",
                "help": "Delay between request's threads",
                "type": int
            },
            {
                "group": "request",
                "args": None,
                "argl": "--timeout",
                "default": 30,
                "action": "store",
                "help": "Request timeout (30 sec default)",
                "type": int
            },
            {
                "group": "request",
                "args": "-r",
                "argl": "--retries",
                "default": 3,
                "action": "store",
                "help": "Max retries to reconnect (default 3)",
                "type": int
            },
            {
                "group": "request",
                "args": None,
                "argl": "--accept-cookies",
                "default": False,
                "action": "store_true",
                "help": "Accept and route cookies from responses",
                "type": bool
            },
            {
                "group": "debug",
                "args": None,
                "argl": "--debug",
                "default": 0,
                "action": "store",
                "help": "Debug level 1 - 3",
                "type": int
            },
            {
                "group": "request",
                "args": None,
                "argl": "--tor",
                "default": False,
                "action": "store_true",
                "help": "Using proxylist",
                "type": bool
            },
            {
                "group": "request",
                "args": None,
                "argl": "--torlist",
                "default": None,
                "action": "store",
                "help": "Path to external proxylist",
                "type": str
            },
            {
                "group": "request",
                "args": None,
                "argl": "--proxy",
                "default": None,
                "action": "store",
                "help": "Custom permanent proxy server",
                "type": str
            },
            {
                "group": "wordlist",
                "args": "-s",
                "argl": "--scan",
                "default": "directories",
                "action": "store",
                "help": "Scan type scan=directories or scan=subdomains",
                "type": str
            },
            {
                "group": "wordlist",
                "args": "-w",
                "argl": "--wordlist",
                "default": None,
                "action": "store",
                "help": "Path to external wordlist",
                "type": str
            },
            {
                "group": "wordlist",
                "args": None,
                "argl": "--reports",
                "default": "std",
                "action": "store",
                "help": "Scan reports (json,std,txt)",
                "type": str
            },
            {
                "group": "request",
                "args": None,
                "argl": "--random-agent",
                "default": False,
                "action": "store_true",
                "help": "Randomize user-agent per request",
                "type": bool
            },
            {
                "group": "wordlist",
                "args": None,
                "argl": "--random-list",
                "default": False,
                "action": "store_true",
                "help": "Shuffle scan list",
                "type": bool
            },
            {
                "group": "wordlist",
                "args": None,
                "argl": "--prefix",
                "default": None,
                "action": "store",
                "help": "Append path prefix to scan host",
                "type": str
            },
            {
                "group": "sniff",
                "args": "-i",
                "argl": "--indexof",
                "default": False,
                "action": "store_true",
                "help": "Detect Apache Index of/",
                "type": bool
            },
            {
                "group": "app",
                "args": None,
                "argl": "--update",
                "default": False,
                "action": "store_true",
                "help": "Update from CVS",
                "type": bool
            },
            {
                "group": "app",
                "args": None,
                "argl": "--version",
                "default": False,
                "action": "store_true",
                "help": "Get current version",
                "type": bool
            },
            {
                "group": "app",
                "args": None,
                "argl": "--examples",
                "default": False,
                "action": "store_true",
                "help": "Examples of usage",
                "type": bool
            }
        ]

        groupped = {}
        try:
    
            self.parser = ThrowingArgumentParser(formatter_class=RawDescriptionHelpFormatter)
            
            required_named = self.parser.add_argument_group('required named options')
            required_named.add_argument('--host', help="Target host (ip); --host http://example.com")
            arguments_len = len(__arguments)

            for group, description in sorted(__groups.items()):
                groupped[group] = self.parser.add_argument_group(description)

            for i in range(arguments_len):
                arg = __arguments[i]

                if arg['args'] is None:
                    if bool == arg['type']:
                        groupped[arg['group']].add_argument(arg['argl'],
                                                            default=arg['default'],
                                                            action=arg['action'],
                                                            help=arg['help'])
                    else:
                        groupped[arg['group']].add_argument(arg['argl'],
                                                            default=arg['default'],
                                                            action=arg['action'],
                                                            help=arg['help'],
                                                            type=arg['type'])
                else:
                    if bool == arg['type']:
                        groupped[arg['group']].add_argument(arg['args'],
                                                            arg['argl'],
                                                            default=arg['default'],
                                                            action=arg['action'],
                                                            help=arg['help'])
                    else:
                        groupped[arg['group']].add_argument(arg['args'],
                                                            arg['argl'],
                                                            default=arg['default'],
                                                            action=arg['action'],
                                                            help=arg['help'],
                                                            type=arg['type'])

            self.args = self.parser.parse_args()
        except ArgumentParserError as e:
            raise OptionsError(e.message)

    def get_arg_values(self):
        """
        Get used input options
        :raise OptionsError
        :return: dict
        """

        args = {}

        try:
            arguments = self.args

            if not self.args.host \
                    and True is not self.args.version \
                    and True is not self.args.update \
                    and True is not self.args.examples:
                raise OptionsError("argument --host is required")

            if True is self.args.version or True is self.args.update or True is self.args.examples:
                for arg, value in vars(arguments).items():
                    if arg in self.__standalone and True is value:
                        args[arg] = value
                        break
            else:

                for arg, value in vars(self.args).items():

                    if value:
                        args[arg] = value
                args = Filter.filter(args)

            return args

        except (AttributeError, FilterError) as e:
            raise OptionsError(e.message)
