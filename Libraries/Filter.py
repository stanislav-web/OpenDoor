import sys, re
from urlparse import urlparse


class Filter:
    URL_REGEX = "^(?:[-A-Za-z0-9]+\.)+([A-Za-z]|(?u)\w){2,6}$"

    """Filter args class"""

    def call(self, Command):

        args = Command.get_arg_values()
        filtered = {}
        for key, value in args.iteritems():
            try:
                # dymanic function call
                filtered[key] = getattr(self, '%s' % key)(value)
            except AttributeError:
                sys.exit(key + """ function does not exist in Filter class""")

        return filtered

    def url(self, url):

        if not re.search('http', url, re.IGNORECASE):
            url = "http://" + url

        url = urlparse(url).netloc

        regex = re.compile(r"" + self.URL_REGEX + "")
        if not regex.match(url):
            sys.exit(url + """ is invalid url. """)

        return url

    def update(self, noarg):
        pass

    def version(self, noarg):
        pass
