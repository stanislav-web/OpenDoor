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

import re
import sys

from src.core import helper
from .exceptions import FilterError


class Filter(object):

    """Filter class"""

    URL_REGEX = r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|(?:[-A-Za-z0-9]+\.)+([-A-Za-z]|\w){2,8})$"

    @staticmethod
    def filter(args):
        """
        Filter options
        :param dict args:
        :return: dict
        """

        filtered = {}
        targets = Filter.targets(args)

        for key, value in args.items():
            if 'scan' == key:
                filtered['scan'] = Filter.scan(value)
            elif key in ['host', 'hostlist', 'stdin']:
                continue
            else:
                if 'proxy' == key:
                    filtered[key] = Filter.proxy(value)
                else:
                    filtered[key] = value

        if len(targets) == 1:
            filtered['host'] = targets[0]['host']
            filtered['scheme'] = targets[0]['scheme']
            filtered['ssl'] = targets[0]['ssl']

        if len(targets) > 0:
            filtered['targets'] = targets

        return filtered

    @staticmethod
    def scheme(hostname):
        """
        Get the scheme of the input hostname.

        :param hostname: A string representing the input hostname.
        :type hostname: str
        :return: A string representing the scheme of the input hostname.
        :rtype: str
        """

        scheme = helper.parse_url(hostname).scheme
        if not scheme:
            scheme = 'http'
        return scheme + "://"

    @staticmethod
    def ssl(scheme):
        """
        If `ssl` in action
        :param str scheme: scheme protocol
        :return: bool
        """

        return 'https://' == scheme


    @staticmethod
    def targets(args):
        """
        Build normalized targets from a single host, host file or STDIN.

        :param dict args:
        :raise FilterError:
        :return: list[dict]
        """

        raw_targets = []

        if args.get('host'):
            raw_targets = [args.get('host')]
        elif args.get('hostlist'):
            raw_targets = Filter._read_target_lines(args.get('hostlist'))
        elif args.get('stdin') is True:
            raw_targets = Filter._read_target_stream(sys.stdin)

        targets = []
        seen = set()

        for raw_target in raw_targets:
            cleaned = Filter._clean_target(raw_target)
            if not cleaned:
                continue
            if cleaned in seen:
                continue

            host = Filter.host(cleaned)
            scheme = Filter.scheme(cleaned)
            targets.append({
                'host': host,
                'scheme': scheme,
                'ssl': Filter.ssl(scheme),
                'source': cleaned,
            })
            seen.add(cleaned)

        return targets

    @staticmethod
    def _read_target_lines(filepath):
        """
        Read targets from a file.

        :param str filepath:
        :raise FilterError:
        :return: list[str]
        """

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return Filter._read_target_stream(file)
        except OSError as error:
            raise FilterError("Unable to read targets from --hostlist `{0}`. {1}".format(filepath, error))

    @staticmethod
    def _read_target_stream(stream):
        """
        Read targets from a stream-like object.

        :param stream:
        :return: list[str]
        """

        return [line for line in stream.readlines()]

    @staticmethod
    def _clean_target(value):
        """
        Normalize a raw target line.

        :param str value:
        :return: str
        """

        if value is None:
            return ''
        value = str(value).strip()
        if not value or value.startswith('#'):
            return ''
        return value

    @staticmethod
    def host(hostname):
        """
        Input `host` param filter
        :param str hostname: input hostname
        :raise FilterError
        :return: str
        """

        if not re.search('http', hostname, re.IGNORECASE):
            if re.search('https', hostname, re.IGNORECASE):
                hostname = "https://" + hostname
            else:
                hostname = "http://" + hostname

        hostname = helper.parse_url(hostname).netloc
        regex = re.compile(Filter.URL_REGEX, re.UNICODE)

        if not regex.match(hostname):
            try:
                hostname = helper.decode_hostname(hostname)
            except UnicodeError as error:
                raise FilterError("\"{0}\" is invalid host. {1}".format(hostname, str(error)))
            if not regex.match(hostname):
                raise FilterError("\"{0}\" is invalid host. Use ip, http(s) or just hostname".format(hostname))
        return hostname

    @staticmethod
    def proxy(proxyaddress):
        """
        Input `proxy` param filter
        :param str proxyaddress: input proxy server address
        :raise FilterError
        :return: str
        """

        proxy = helper.parse_url(proxyaddress)

        if proxy.scheme not in ['http', 'https', 'socks4', 'socks5'] or None is proxy.port:
            raise FilterError("\"{0}\" is invalid proxy in --proxy. Use scheme:ip:port format".format(proxyaddress))
        return proxyaddress

    @staticmethod
    def scan(choose):
        """
        Input `scan` type filter
        :param str choose: preferred scan type
        :return: str
        """

        if choose not in ['directories', 'subdomains']:
            choose = 'directories'
        return choose