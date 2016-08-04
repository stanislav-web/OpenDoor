from Version import update, get_full_version;
from Libraries import Http;
from Logger import Logger as log
from Progress import Progress

class Controller:

    DEFAULT_LOGGING = False

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
        if result :
            Progress.view(result)
            isLogging =  params.get('log', self.DEFAULT_LOGGING)

            if True == isLogging:
                log.syslog(url, result)
        exit()

    def examples_action(self):
        examples = """
            Examples:
                python ./opendoor.py  --examples
                python ./opendoor.py  --update
                python ./opendoor.py  --version
                python ./opendoor.py --url "http://joomla-ua.org"
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --proxy
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --delay 10
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --delay 10 --rest 10
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --delay 10 --rest 10 --debug 1
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --delay 10 --rest 10 --debug 1 --log
            """
        exit(examples)
