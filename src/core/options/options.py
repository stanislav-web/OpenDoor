# -*- coding: utf-8 -*-

"""Options class"""

from argparse import RawDescriptionHelpFormatter
from .exceptions import ArgumentParserError, ThrowingArgumentParser, OptionsError, FilterError
from .config import Config
from .filter import Filter

class Options:
    """Options class"""

    def __init__(self):

        try:
            parser = ThrowingArgumentParser(formatter_class=RawDescriptionHelpFormatter)
            required_named = parser.add_argument_group('required named options')
            required_named.add_argument('-u', '--url', help="URL or page to scan; -u http://example.com")

            config_arguments = Config.arguments
            config_arguments_len = len(config_arguments)

            for i in range(config_arguments_len):
                arg = config_arguments[i]
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
        except (ArgumentParserError) as e:
           raise OptionsError(e.message)

    def get_arg_values(self):
        """Get used input options"""

        args = {}

        try:
            arguments = self.parser.parse_args()

            if not arguments.url \
                    and True is not arguments.version \
                    and True is not arguments.update \
                    and True is not arguments.examples:
                raise OptionsError("argument -u/--url is required")

            if True is arguments.version \
                    or True is arguments.update \
                    or True is arguments.examples:
                for arg, value in vars(arguments).iteritems():
                    if arg in Config.standalone and True is value:
                        args[arg] = value
                        break
            else:

                for arg, value in vars(arguments).iteritems():

                    if value:
                        args[arg] = value

                if not args:
                    self.parser.print_help()
                    return Filter.filter(args)
            return args

        except (AttributeError, FilterError) as e:
            raise OptionsError(e.message)
