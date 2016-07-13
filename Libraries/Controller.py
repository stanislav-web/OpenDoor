import sys
from Vendors import update, get_full_version;
from Libraries import Http;

class Controller:
    """Controller class"""
    def __init__(self, InputArguments):
        for action, args in InputArguments.iteritems():
            try:
                # dymanic function call
                if not args:
                    getattr(self, '%s_action' % action)()
                else:
                    getattr(self, '%s_action' % action)(args)

            except AttributeError:
                sys.exit(action + """ action does not exist in Controllers""")

    def update_action(self):
        update()

    def version_action(self):
        print get_full_version()

    def url_action(self, url):
        print Http().connect(url)
