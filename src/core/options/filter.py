# -*- coding: utf-8 -*-

"""Filter class"""

import re
from .exceptions import FilterError
from urlparse import urlparse

class Filter:
    """Filter class"""

    URL_REGEX = "^(?:[-A-Za-z0-9]+\.)+([A-Za-z]|(?u)\w){2,6}$"

    @staticmethod
    def filter(args):
        """ Filter options """

        filtered = {}

        for key, value in args.iteritems():
            if 'scan' == key:
                filtered['scan'] = Filter.scan(value)
            elif 'host' == key:
                filtered['host'] = Filter.host(value)
                filtered['scheme'] = Filter.scheme(value)
            else:
                filtered[key] = value

        return filtered

    @staticmethod
    def scheme(host):
        """ Get `host` scheme """

        scheme = urlparse(host).scheme
        if not scheme:
            scheme = 'http'
        return scheme + "://"

    @staticmethod
    def host(host):
        """ Input `host` param filter """

        if not re.search('http', host, re.IGNORECASE):
            if re.search('https', host, re.IGNORECASE):
                host = "https://" + host
            else:
                host = "http://" + host

        host = urlparse(host).netloc
        regex = re.compile(r"" + Filter.URL_REGEX + "")
        if not regex.match(host):
            raise FilterError("\"{0}\" is invalid host. ".format(host))
        return host

    @staticmethod
    def scan(type):
        """ Input `scan` param filter """

        if type not in ['directories', 'subdomains']:
            type = 'directories'
        return type
