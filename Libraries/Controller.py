from Version import update, get_full_version;
from Libraries import Http;
from Logger import Logger as log
from Progress import Progress

class Controller:
    """Controller class"""
    def __init__(self, InputArguments):

        for action, args in InputArguments.iteritems():
            try:
                # dymanic function call
                if not args:
                    getattr(self, '%s_action' % action)()
                else:
                    getattr(self, '%s_action' % action)(args, InputArguments)
                    break

            except AttributeError:
                log.critical(action + """ action does not exist in Controller""")

    def update_action(self):
        update()
        exit()

    def version_action(self):
        print get_full_version()
        exit()

    def url_action(self, url, params=()):
        result = Http().get(url, params);

        Progress.view(result)
        exit()