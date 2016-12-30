# -*- coding: utf-8 -*-

"""Filter class"""

import re
from urlparse import urlparse
from .Logger import Logger as Log


class Filter:
    """Filter args class"""

    URL_REGEX = "^(?:[-A-Za-z0-9]+\.)+([A-Za-z]|(?u)\w){2,6}$"

    def call(self, Command):
        """ Filter commands """

        args = Command.get_arg_values()
        filtered = {}
        for key, value in args.iteritems():
            try:
                # dymanic function call
                filtered[key] = getattr(self, '{}'.format(key))(value)
                if 'url' == key:
                    filtered['scheme'] = self.scheme(value)
            except AttributeError:
                Log.critical(key + """ function does not exist in Filter class""")



        return filtered

    @staticmethod
    def scheme(url):
        """ Get `url` scheme """

        scheme = urlparse(url).scheme
        if not scheme:
            scheme='http'
        return scheme+"://"


    def url(self, url):
        """ Input `url` param filter """

        if not re.search('http', url, re.IGNORECASE):
            if re.search('https', url, re.IGNORECASE):
                url = "https://" + url
            else:
                url = "http://" + url

        url = urlparse(url).netloc
        regex = re.compile(r"" + self.URL_REGEX + "")
        if not regex.match(url):
            Log.critical("\"" + url + "\""" is invalid url. """)

        return url

    @staticmethod
    def threads(threads):
        """ Input `threads` param filter """

        if 0 == threads:
            threads = 1
        return threads

    @staticmethod
    def port(port):
        """ Input `threads` param filter """

        if 0 == port:
            port = 80
        return port

    @staticmethod
    def check(type):
        """ Input `check` param filter """

        if type not in ['directories', 'subdomains']:
            type = 'directories'
        return type

    @staticmethod
    def debug(debug):
        """ Input `debug` param filter """

        return debug

    @staticmethod
    def delay(delay):
        """ Input `delay` param filter """

        return delay

    @staticmethod
    def rest(rest):
        """ Input `rest` param filter """

        return rest

    @staticmethod
    def log(log):
        """ Input `log` param filter """

        return log

    @staticmethod
    def proxy(proxy):
        """ Input `proxy` param filter """

        return proxy

    @staticmethod
    def update(noarg):
        """ Input `update` param filter """

        pass

    @staticmethod
    def version(noarg):
        """ Input `version` param filter """

        pass

    @staticmethod
    def examples(noarg):
        """ Input `examples` param filter """

        pass
