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
            elif 'url' == key:
                filtered['url'] = Filter.url(value)
                filtered['scheme'] = Filter.scheme(value)
            else:
                filtered[key] = value

        return filtered

    @staticmethod
    def scheme(url):
        """ Get `url` scheme """

        scheme = urlparse(url).scheme
        if not scheme:
            scheme = 'http'
        return scheme + "://"

    @staticmethod
    def url(url):
        """ Input `url` param filter """

        if not re.search('http', url, re.IGNORECASE):
            if re.search('https', url, re.IGNORECASE):
                url = "https://" + url
            else:
                url = "http://" + url

        url = urlparse(url).netloc
        regex = re.compile(r"" + Filter.URL_REGEX + "")
        if not regex.match(url):
            raise FilterError("\"{0}\" is invalid url. ".format(url))
        return url

    @staticmethod
    def scan(type):
        """ Input `scan` param filter """

        if type not in ['directories', 'subdomains']:
            type = 'directories'
        return type
