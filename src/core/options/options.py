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
# noinspection PyCompatibility
from argparse import RawDescriptionHelpFormatter, OPTIONAL
from .exceptions import ArgumentParserError, ThrowingArgumentParser, OptionsError, FilterError
from .filter import Filter


class Options(object):

    """Options class"""

    def __init__(self):
        """
        Constructor
        :raise OptionsError
        """

        self.__standalone = ['version', 'update', 'examples', 'docs']
        self.__wizard_conf = 'opendoor.conf'

        __groups = {
            'request': "Request tools",
            'stream': "Stream tools",
            'debug': "Debug tools",
            'wordlist': "Wordlist tools",
            'sniff': "Sniff tools",
            'session': "Session tools",
            'calibration': "Auto-calibration tools",
            'network': "Network transport tools",
            'ci': "CI/CD tools",
            'report': "Reports tools",
            'filter': "Response filters",
            'app': "Application tools"
        }

        __arguments = [
            {
                "group": "request",
                "args": "-p",
                "argl": "--port",
                "default": 80,
                "action": "store",
                "help": "Custom port (default 80)",
                "type": int
            },
            {
                "group": "request",
                "args": "-m",
                "argl": "--method",
                "default": "HEAD",
                "action": "store",
                "help": "Request method (HEAD by default)",
                "type": str
            },
            {
                "group": "request",
                "args": None,
                "argl": "--scheme",
                "default": None,
                "action": "store",
                "help": "Raw-request scheme when request line uses a relative path (http or https)",
                "type": str
            },
            {
                "group": "request",
                "args": None,
                "argl": "--raw-request",
                "default": None,
                "action": "store",
                "help": "Path to raw HTTP request file exported from a proxy or repeater",
                "type": str
            },
            {
                "group": "session",
                "args": None,
                "argl": "--session-save",
                "default": None,
                "action": "store",
                "help": "Persist scan state to a checkpoint file",
                "type": str
            },
            {
                "group": "session",
                "args": None,
                "argl": "--session-autosave-sec",
                "default": 20,
                "action": "store",
                "help": "Autosave session checkpoint every N seconds (default 20)",
                "type": int
            },
            {
                "group": "session",
                "args": None,
                "argl": "--session-autosave-items",
                "default": 200,
                "action": "store",
                "help": "Autosave session checkpoint after N processed items (default 200)",
                "type": int
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
                "help": "Delay between threaded requests",
                "type": float
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
                "help": "Maximum reconnect retries (default 3)",
                "type": int
            },
            {
                "group": "request",
                "args": None,
                "argl": "--keep-alive",
                "default": False,
                "action": "store_true",
                "help": "Use keep-alive connection",
                "type": bool
            },
            {
                "group": "request",
                "args": None,
                "argl": "--header",
                "default": None,
                "action": "append",
                "help": "Add custom request header, e.g. --header 'X-Test: 1'",
                "type": str
            },
            {
                "group": "request",
                "args": None,
                "argl": "--cookie",
                "default": None,
                "action": "append",
                "help": "Add custom cookie, e.g. --cookie 'sid=abc123'",
                "type": str
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
                "group": "request",
                "args": None,
                "argl": "--fingerprint",
                "default": False,
                "action": "store_true",
                "help": "Detect probable CMS, framework or custom stack before the scan",
                "type": bool
            },
            {
                "group": "request",
                "args": None,
                "argl": "--waf-detect",
                "default": False,
                "action": "store_true",
                "help": "Passively detect probable WAF or anti-bot protections before classifying a response",
                "type": bool
            },
            {
                "group": "request",
                "args": None,
                "argl": "--waf-safe-mode",
                "default": False,
                "action": "store_true",
                "help": "Automatically switch to a cautious scan profile after WAF detection",
                "type": bool
            },
            {
                "group": "request",
                "args": None,
                "argl": "--header-bypass",
                "default": False,
                "action": "store_true",
                "help": "Probe blocked 401/403 paths with controlled header-injection bypass variants",
                "type": bool
            },
            {
                "group": "request",
                "args": None,
                "argl": "--header-bypass-headers",
                "default": None,
                "action": "store",
                "help": "Comma-separated header names for --header-bypass",
                "type": str
            },
            {
                "group": "request",
                "args": None,
                "argl": "--header-bypass-ips",
                "default": None,
                "action": "store",
                "help": "Comma-separated trusted IP values for --header-bypass",
                "type": str
            },
            {
                "group": "request",
                "args": None,
                "argl": "--header-bypass-status",
                "default": None,
                "action": "store",
                "help": "Comma-separated status codes that trigger --header-bypass, default 401,403",
                "type": str
            },
            {
                "group": "request",
                "args": None,
                "argl": "--header-bypass-limit",
                "default": 32,
                "action": "store",
                "help": "Maximum header-bypass variants per blocked URL, default 32, use 0 for unlimited",
                "type": int
            },
            {
                "group": "debug",
                "args": None,
                "argl": "--debug",
                "default": 0,
                "action": "store",
                "help": "Debug level -1 (silent), 1 - 3",
                "type": int
            },
            {
                "group": "request",
                "args": None,
                "argl": "--proxy-pool",
                "default": False,
                "action": "store_true",
                "help": "Use built-in rotating proxy pool",
                "type": bool
            },
            {
                "group": "request",
                "args": None,
                "argl": "--proxy-list",
                "default": None,
                "action": "store",
                "help": "Path to custom rotating proxy list",
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
                "group": "network",
                "args": None,
                "argl": "--transport",
                "default": None,
                "action": "store",
                "help": "Network transport mode: direct, proxy, openvpn, wireguard",
                "type": str
            },
            {
                "group": "network",
                "args": None,
                "argl": "--transport-profile",
                "default": None,
                "action": "store",
                "help": "Single transport profile path. OpenVPN: *.ovpn, WireGuard: *.conf",
                "type": str
            },
            {
                "group": "network",
                "args": None,
                "argl": "--transport-profiles",
                "default": None,
                "action": "store",
                "help": "Text file with transport profile paths, one per line",
                "type": str
            },
            {
                "group": "network",
                "args": None,
                "argl": "--transport-rotate",
                "default": None,
                "action": "store",
                "help": "Transport rotation mode: none, per-target",
                "type": str
            },
            {
                "group": "network",
                "args": None,
                "argl": "--transport-timeout",
                "default": None,
                "action": "store",
                "help": "Seconds to wait for transport commands",
                "type": int
            },
            {
                "group": "network",
                "args": None,
                "argl": "--transport-healthcheck-url",
                "default": None,
                "action": "store",
                "help": "Optional URL used to verify connectivity after transport startup",
                "type": str
            },
            {
                "group": "network",
                "args": None,
                "argl": "--openvpn-auth",
                "default": None,
                "action": "store",
                "help": "Optional auth-user-pass file for OpenVPN transport only",
                "type": str
            },
            {
                "group": "wordlist",
                "args": "-s",
                "argl": "--scan",
                "default": "directories",
                "action": "store",
                "help": "Scan type: directories or subdomains",
                "type": str
            },
            {
                "group": "wordlist",
                "args": "-w",
                "argl": "--wordlist",
                "default": None,
                "action": "store",
                "help": "Path to custom wordlist",
                "type": str
            },
            {
                "group": "ci",
                "args": None,
                "argl": "--fail-on-bucket",
                "default": None,
                "action": "store",
                "help": "Exit with code 1 when selected result buckets are found, e.g. success,auth,forbidden,blocked",
                "type": str
            },
            {
                "group": "calibration",
                "args": None,
                "argl": "--auto-calibrate",
                "default": False,
                "action": "store_true",
                "help": "Enable smart baseline filtering for soft-404, wildcard and catch-all responses",
                "type": bool
            },
            {
                "group": "calibration",
                "args": None,
                "argl": "--calibration-samples",
                "default": None,
                "action": "store",
                "help": "Number of random calibration probes before scan",
                "type": int
            },
            {
                "group": "calibration",
                "args": None,
                "argl": "--calibration-threshold",
                "default": None,
                "action": "store",
                "help": "Auto-calibration match threshold from 0.01 to 1.0",
                "type": float
            },
            {
                "group": "report",
                "args": None,
                "argl": "--reports",
                "default": "std",
                "action": "store",
                "help": "Scan reports (json,std,txt,csv,html,sqlite,sarif)",
                "type": str
            },
            {
                "group": "report",
                "args": None,
                "argl": "--reports-dir",
                "default": None,
                "action": "store",
                "help": "Path to custom reports directory",
                "nargs": 1,
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
                "group": "wordlist",
                "args": "-e",
                "argl": "--extensions",
                "default": None,
                "action": "store",
                "help": "Force selected extensions for the scan session, e.g. php,json",
                "type": str
            },
            {
                "group": "wordlist",
                "args": "-i",
                "argl": "--ignore-extensions",
                "default": None,
                "action": "store",
                "help": "Ignore selected extensions for the scan session, e.g. aspx,jsp",
                "type": str
            },
            {
                "group": "wordlist",
                "args": None,
                "argl": "--recursive",
                "default": False,
                "action": "store_true",
                "help": "Enable recursive directory scan",
                "type": bool
            },
            {
                "group": "wordlist",
                "args": None,
                "argl": "--recursive-depth",
                "default": 1,
                "action": "store",
                "help": "Maximum recursive scan depth",
                "type": int
            },
            {
                "group": "wordlist",
                "args": None,
                "argl": "--recursive-status",
                "default": "200,301,302,307,308,403",
                "action": "store",
                "help": "HTTP status codes allowed for recursive expansion",
                "type": str
            },
            {
                "group": "wordlist",
                "args": None,
                "argl": "--recursive-exclude",
                "default": "jpg,jpeg,png,gif,svg,css,js,ico,woff,woff2,ttf,map,pdf,zip,gz,tar",
                "action": "store",
                "help": "File extensions excluded from recursive expansion",
                "type": str
            },
            {
                "group": "sniff",
                "args": None,
                "argl": "--sniff",
                "default": None,
                "action": "store",
                "help": "Response sniff plugins (indexof,collation,file,skipempty,skipsizes=NUM:NUM...)",
                "type": str
            },
            {
                "group": "filter",
                "args": None,
                "argl": "--include-status",
                "default": None,
                "action": "store",
                "help": "Include only response codes, e.g. 200-299,301,302,403",
                "type": str
            },
            {
                "group": "filter",
                "args": None,
                "argl": "--exclude-status",
                "default": None,
                "action": "store",
                "help": "Exclude response codes, e.g. 404,429,500-599",
                "type": str
            },
            {
                "group": "filter",
                "args": None,
                "argl": "--exclude-size",
                "default": None,
                "action": "store",
                "help": "Exclude exact response sizes in bytes, e.g. 0,1234",
                "type": str
            },
            {
                "group": "filter",
                "args": None,
                "argl": "--exclude-size-range",
                "default": None,
                "action": "store",
                "help": "Exclude response size ranges in bytes, e.g. 0-256,1024-2048",
                "type": str
            },
            {
                "group": "filter",
                "args": None,
                "argl": "--match-text",
                "default": None,
                "action": "append",
                "help": "Keep only responses whose body contains the given text. Repeatable",
                "type": str
            },
            {
                "group": "filter",
                "args": None,
                "argl": "--exclude-text",
                "default": None,
                "action": "append",
                "help": "Exclude responses whose body contains the given text. Repeatable",
                "type": str
            },
            {
                "group": "filter",
                "args": None,
                "argl": "--match-regex",
                "default": None,
                "action": "append",
                "help": "Keep only responses whose body matches the given regex. Repeatable",
                "type": str
            },
            {
                "group": "filter",
                "args": None,
                "argl": "--exclude-regex",
                "default": None,
                "action": "append",
                "help": "Exclude responses whose body matches the given regex. Repeatable",
                "type": str
            },
            {
                "group": "filter",
                "args": None,
                "argl": "--min-response-length",
                "default": None,
                "action": "store",
                "help": "Keep only responses whose size is at least N bytes",
                "type": int
            },
            {
                "group": "filter",
                "args": None,
                "argl": "--max-response-length",
                "default": None,
                "action": "store",
                "help": "Keep only responses whose size is at most N bytes",
                "type": int
            },
            {
                "group": "app",
                "args": None,
                "argl": "--update",
                "default": False,
                "action": "store_true",
                "help": "Show package update instructions",
                "type": bool
            },
            {
                "group": "app",
                "args": None,
                "argl": "--version",
                "default": False,
                "action": "store_true",
                "help": "Show current version",
                "type": bool
            },
            {
                "group": "app",
                "args": None,
                "argl": "--examples",
                "default": False,
                "action": "store_true",
                "help": "Show usage examples",
                "type": bool
            },
            {
                "group": "app",
                "args": None,
                "argl": "--docs",
                "default": False,
                "action": "store_true",
                "help": "Open documentation",
                "type": bool
            },
            {
                "group": "app",
                "args": None,
                "argl": "--wizard",
                "default": None,
                "action": "store",
                "help": "Run scanner wizard from your config",
                "nargs": OPTIONAL,
                "const": self.__wizard_conf,
                "type": str
            }
        ]

        groupped = {}
        try:
            self.parser = ThrowingArgumentParser(formatter_class=RawDescriptionHelpFormatter)
            required_named = self.parser.add_argument_group('required named options')
            target_group = required_named.add_mutually_exclusive_group()
            target_group.add_argument('--host', help="Target host; example: --host http://example.com")
            target_group.add_argument('--hostlist', help="Path to file with targets, one per line")
            target_group.add_argument('--stdin', default=False, action='store_true',
                                      help="Read targets from STDIN, one per line")
            target_group.add_argument('--session-load', help="Resume a scan from a saved session file")
            arguments_len = len(__arguments)

            for group, description in sorted(__groups.items()):
                groupped[group] = self.parser.add_argument_group(description)

            for i in range(arguments_len):
                arg = __arguments[i]

                if 'nargs' in arg and arg['nargs'] == '?':
                    const = arg['const']
                else:
                    const = None

                argument_names = [arg['argl']]
                if arg['args'] is not None:
                    argument_names.insert(0, arg['args'])

                argument_kwargs = {
                    'default': arg['default'],
                    'action': arg['action'],
                    'help': arg['help'],
                }

                if bool != arg['type']:
                    argument_kwargs['type'] = arg['type']

                if const is not None:
                    argument_kwargs['nargs'] = arg['nargs']
                    argument_kwargs['const'] = const

                groupped[arg['group']].add_argument(*argument_names, **argument_kwargs)

            self.args = self.parser.parse_args()
        except (ArgumentParserError, KeyError) as error:
            raise OptionsError(error)

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
                    and not getattr(self.args, 'hostlist', None) \
                    and True is not getattr(self.args, 'stdin', False) \
                    and not getattr(self.args, 'raw_request', None) \
                    and not getattr(self.args, 'session_load', None) \
                    and True is not self.args.version \
                    and True is not self.args.update \
                    and True is not self.args.docs \
                    and True is not self.args.examples \
                    and None is self.args.wizard:
                sys.exit(self.parser.print_help())

            if True is self.args.version or True is self.args.update \
                    or True is self.args.examples or True is self.args.docs:
                for arg, value in vars(arguments).items():
                    if arg in self.__standalone and True is value:
                        args[arg] = value
                        break
            else:
                for arg, value in vars(self.args).items():
                    if value or (arg == 'header_bypass_limit' and value == 0):
                        args[arg] = value
                args = Filter.filter(args)

                if args.get('waf_safe_mode') is True:
                    args['waf_detect'] = True

            return args

        except (AttributeError, FilterError, ArgumentParserError) as error:
            raise OptionsError(error)