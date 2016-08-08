import re
from urlparse import urlparse
from Logger import Logger as log

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
                filtered[key] = getattr(self, '%s' % key)(value)
            except AttributeError:
                log.critical(key + """ function does not exist in Filter class""")

        return filtered

    def url(self, url):

        if not re.search('http', url, re.IGNORECASE):
            url = "http://" + url

        url = urlparse(url).netloc

        regex = re.compile(r"" + self.URL_REGEX + "")
        if not regex.match(url):
            log.critical("\"" + url + "\""" is invalid url. """)

        return url

    @staticmethod
    def threads(threads):

        if 0 == threads:
            threads = 1
        return threads

    @staticmethod
    def check(type):
        if type not in ['directories', 'subdomains']:
            type = 'directories'
        return type

    @staticmethod
    def debug(debug):
        return debug

    @staticmethod
    def delay(delay):
        return delay

    @staticmethod
    def rest(rest):
        return rest

    @staticmethod
    def log(log):
        return log

    @staticmethod
    def proxy( proxy):
        return proxy

    @staticmethod
    def update(noarg):
        pass

    @staticmethod
    def version( noarg):
        pass

    @staticmethod
    def examples(noarg):
        pass