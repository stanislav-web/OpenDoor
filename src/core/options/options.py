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

from .config import Config
from .exceptions import ArgumentParserError, ThrowingArgumentParser, OptionsError, FilterError
from .filter import Filter


class Options:
    """Options class"""

    def __init__(self):
        """
        Constructor
        :raise OptionsError
        """

        groups = {}

        try:
            parser = ThrowingArgumentParser(formatter_class=RawDescriptionHelpFormatter)
            required_named = parser.add_argument_group('required named options')
            required_named.add_argument('--host', help="Target host; -host http://example.com")
            config_arguments = Config.arguments
            config_arguments_len = len(config_arguments)

            for group, description in sorted(Config.groups.iteritems()):
                groups[group] = parser.add_argument_group(description)

            for i in range(config_arguments_len):
                arg = config_arguments[i]

                if arg['args'] is None:
                    if bool == arg['type']:
                        groups[arg['group']].add_argument(arg['argl'], default=arg['default'], action=arg['action'],
                                                          help=arg['help'])
                    else:
                        groups[arg['group']].add_argument(arg['argl'], default=arg['default'], action=arg['action'],
                                                          help=arg['help'], type=arg['type'])
                else:
                    if bool == arg['type']:
                        groups[arg['group']].add_argument(arg['args'], arg['argl'], default=arg['default'],
                                                          action=arg['action'], help=arg['help'])
                    else:
                        groups[arg['group']].add_argument(arg['args'], arg['argl'], default=arg['default'],
                                                          action=arg['action'], help=arg['help'], type=arg['type'])

            parser.parse_args()
            self.parser = parser
        except (ArgumentParserError) as e:
            raise OptionsError(e.message)

    def get_arg_values(self):
        """
        Get used input options
        :raise OptionsError
        :return: dict
        """

        args = {}

        try:
            arguments = self.parser.parse_args()

            if not arguments.host and True is not arguments.version and True is not arguments.update and True is not arguments.examples:
                raise OptionsError("argument --host is required")

            if True is arguments.version or True is arguments.update or True is arguments.examples:
                for arg, value in vars(arguments).iteritems():
                    if arg in Config.standalone and True is value:
                        args[arg] = value
                        break
            else:

                for arg, value in vars(arguments).iteritems():

                    if value:
                        args[arg] = value
                args = Filter.filter(args)

            return args

        except (AttributeError, FilterError) as e:
            raise OptionsError(e.message)
