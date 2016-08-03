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

    def threads(self, threads):

        if 0 == threads:
            threads = 1
        return threads

    def check(self, type):
        if type not in ['dir', 'sub']:
            type = 'dir'
        return type

    def debug(self, debug):
        return debug

    def delay(self, delay):
        return delay

    def rest(self, rest):
        return rest

    def proxy(self):
        return True

    def update(self, noarg):
        pass

    def version(self, noarg):
        pass
