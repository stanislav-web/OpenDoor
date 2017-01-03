# -*- coding: utf-8 -*-

"""Command helper class"""

from argparse import RawDescriptionHelpFormatter

import sys

from src.Exceptions import ArgumentParserError, ThrowingArgumentParser
from src.Logger import Logger as Log
from src.Configs import ArgumentsConfig as config

class Command:
    """Command helper class"""

    def __init__(self):

        try:
            parser = ThrowingArgumentParser(description=__doc__,
                                            formatter_class=RawDescriptionHelpFormatter)
            required_named = parser.add_argument_group('required named arguments')
            required_named.add_argument('-u', '--url', help="URL or page to scan; -u http://example.com")

            for i in range(len(config.arguments)):
                arg = config.arguments[i]
                if arg['args'] is None:
                    if bool == arg['type']:
                        parser.add_argument(arg['argl'], default=arg['default'], action=arg['action'], help=arg['help'])
                    else:
                        parser.add_argument(arg['argl'], default=arg['default'], action=arg['action'], help=arg['help'], type=arg['type'])
                else:
                    if bool == arg['type']:
                        parser.add_argument(arg['args'], arg['argl'], default=arg['default'], action=arg['action'], help=arg['help'])
                    else:
                        parser.add_argument(arg['args'], arg['argl'], default=arg['default'], action=arg['action'], help=arg['help'], type=arg['type'])
            parser.parse_args()
            self.parser = parser
        except ArgumentParserError as e:
            sys.exit(Log.error(e.message))

    def get_arg_values(self):
        """Get used input arguments"""

        command_list = {}

        try:
            arguments = self.parser.parse_args()

            if not arguments.url and not arguments.version and not arguments.update and not arguments.examples:
                sys.exit(Log.error("argument -u/--url is required"))

            for arg, value in vars(arguments).iteritems():

                if value:
                    command_list[arg] = value

            if not command_list:
                self.parser.print_help()
            else:
                return command_list

        except AttributeError as e:
            sys.exit(Log.error(e.message))
