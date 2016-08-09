from Version import update, get_full_version;
from Libraries import Http;
from Logger import Logger as log
from Progress import Progress

class Controller:
    """Controller class"""

    DEFAULT_LOGGING = False

    def __init__(self, InputArguments):

        for action, args in InputArguments.iteritems():
            try:
                # dymanic function call
                if not args:
                    getattr(self, '{func}_action'.format(func=action))()
                else:
                    getattr(self, '{func}_action'.format(func=action))(args, InputArguments)
                    break

            except AttributeError:
                log.critical(action + """ action does not exist in Controller""")

    @staticmethod
    def update_action():
        """ Update action """
        update()
        exit()

    @staticmethod
    def version_action():
        """ Show version action """
        print get_full_version()
        exit()

    def url_action(self, url, params=()):
        """ Load by url action """

        result = Http().get(url, params);
        if result :
            Progress.view(result)
            is_logging =  params.get('log', self.DEFAULT_LOGGING)

            if True == is_logging:
                log.syslog(url, result)
        exit()

    @staticmethod
    def examples_action():
        """ Show examples action """

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