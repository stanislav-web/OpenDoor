import sys,  re
import Command

class Filter:

    URL_REGEX = "^(?:[-A-Za-z0-9]+\.)+([A-Za-z]|(?u)\w){2,6}$"

    """Filter args class"""
    def call(self, Command):
        args = Command.get_arg_values()
        for key, value in args.iteritems():
            try:
                # dymanic function call
                getattr(self, '%s' % key)(value)
            except AttributeError:
                sys.exit(key + """ function does not exist in Filter class""")

    def url(self, url):

        regex = re.compile(r"" + self.URL_REGEX + "")
        if not regex.match(url):
            sys.exit(url + """ is invalid url. """)