from argparse import RawDescriptionHelpFormatter
from Logger import Logger as log
from Exceptions import ArgumentParserError , ThrowingArgumentParser

class Command:
    """Console helper class"""

    def __init__(self):

        try:
            parser = ThrowingArgumentParser(description=__doc__,
                                    formatter_class=RawDescriptionHelpFormatter)
            requiredNamed = parser.add_argument_group('required named arguments')
            requiredNamed.add_argument('-u', '--url', help="URL or page to scan; -u http://example.com")
            parser.add_argument('--update', default=False, action='store_true', help="Update from version control")
            parser.add_argument('-v', '--version', default=False, action='store_true', help="Get current version")
            parser.add_argument('-c', '--check', help="Directory scan eg --check=dir or subdomains --check=sub")
            parser.add_argument('-t', '--threads', help="Allowed threads", type=int)
            parser.add_argument('-d', '--delay', help="Delay between requests", type=int)
            parser.add_argument('-r', '--rest', help="Max request timeout ", type=int)
            parser.add_argument('-p', '--proxy', default=False, action='store_true', help="Use proxy list")
            parser.add_argument('-l', '--logs', default=False, action='store_true', help="Use proxy list")
            parser.parse_args()
            self.parser = parser;
        except (ArgumentParserError) as e:
            log.critical(e.message)


    def get_arg_values(self):

        command_list = {}

        arguments = self.parser.parse_args()

        if not arguments.url and not arguments.version and not arguments.update:
            log.critical("argument -u/--url is required")

        for arg, value in vars(arguments).iteritems():

            if value:
                command_list[arg] = value

        if not command_list:
            #print get_examples()
            self.parser.print_help()
        else:
            return command_list