# -*- coding: utf-8 -*-

"""Controller class"""

import sys

from src.lib.logger.logger import Logger as Log
from .Http import Http
from .Message import Message
from .Progress import Progress
from .Version import Version


class Controller:
    """Controller class"""

    DEFAULT_LOGGING = False

    def __init__(self, InputArguments):

        for action, args in InputArguments.iteritems():

            if not args:
                getattr(self, '{func}_action'.format(func=action))()
            else:
                getattr(self, '{func}_action'.format(func=action))(args, InputArguments)
            break

    @staticmethod
    def update_action():
        """ Update action """

        Version.update()
        sys.exit()

    @staticmethod
    def version_action():
        """ Show version action """

        sys.exit(Version().get_full_version())

    def url_action(self, url, params=()):
        """ Load by url action """

        scan = True

        if True is Log.is_logged(url):

            message = Message().get('has_scanned').format(url).strip("\t")

            try:
                text = raw_input(message)
                if text == "":
                    scan = True
                else:
                    scan = False
            except KeyboardInterrupt as e:
                sys.exit("\n {0}".format(Log.warning(Message().get('abort'))))

        if True is scan:
            result = Http().get(url, params)
            if result:
                Progress.view(result)
                is_logging = params.get('log', self.DEFAULT_LOGGING)

                if True is is_logging:
                    sys.stdout.write(Log.syslog(url, result))
        sys.exit()

    @staticmethod
    def examples_action():
        """ Show examples action """

        examples = """
            Examples:
                python ./opendoor.py  --examples
                python ./opendoor.py  --update
                python ./opendoor.py  --version
                python ./opendoor.py --url "http://joomla-ua.org"
                python ./opendoor.py --url "https://joomla-ua.org"
                python ./opendoor.py --url "http://joomla-ua.org" --port 8080
                python ./opendoor.py --url "http://joomla-ua.org" --check subdomains
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --proxy
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --delay 10
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --delay 10 --rest 10
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --delay 10 --rest 10 --debug 1
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --delay 10 --rest 10 --debug 1 --log
            """
        sys.exit(examples)
