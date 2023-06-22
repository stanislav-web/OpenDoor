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

from src.core import helper
from .exceptions import FilterError


class Filter(object):

    """Filter class"""

    URL_REGEX = "^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|(?:[-A-Za-z0-9]+\.)+([-A-Za-z]|\w){2,8}$"

    @staticmethod
    def filter(args):
        """
        Filter options
        :param dict args:
        :return: dict
        """

        filtered = {}

        for key, value in args.items():
            if 'scan' == key:
                filtered['scan'] = Filter.scan(value)
            elif 'host' == key:
                filtered['host'] = Filter.host(value)
                filtered['scheme'] = Filter.scheme(value)
                filtered['ssl'] = Filter.ssl(filtered['scheme'])
            else:
                if 'proxy' == key:
                    filtered[key] = Filter.proxy(value)
                else:
                    filtered[key] = value

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
        regex = re.compile(r"" + Filter.URL_REGEX + "", re.UNICODE)

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
