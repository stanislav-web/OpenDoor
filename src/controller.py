# -*- coding: utf-8 -*-

"""Controller class"""

from src.lib import args
from src.lib import package
from src.lib import browser
from src.lib import applogger
from src.lib import LibError
from .exceptions import SrcError

class Controller:
    """Controller class"""

    def __init__(self):
        """init constructor"""

        try :
            self.ioargs = args().get_arguments()
        except LibError as e:
            raise SrcError(e.message)

    def run(self):
        """ run action """

        try:

            package.banner()

            if 'url' in self.ioargs:
                getattr(self, 'url_action')(self.ioargs)
            else:
                for action, args in self.ioargs.iteritems():
                    if hasattr(self, '{0}_action'.format(action)) and callable(
                            getattr(self, '{0}_action'.format(action))):
                        getattr(self, '{func}_action'.format(func=action))()
                        break

        except LibError as e:
            raise SrcError(e)


    @staticmethod
    def examples_action():
        """ show examples action """

        package.examples()

    @staticmethod
    def update_action():
        """ update action """

        try:
            package.update()
        except LibError as e:
            raise SrcError(e)

    @staticmethod
    def version_action():
        """ show version action """

        try:
            package.version()
        except LibError as e:
            raise SrcError(e)

    @staticmethod
    def local_version():
        """ show local version """

        try:
            return package.local_version()
        except LibError as e:
            raise SrcError(e)


    def url_action(self, params=()):
        """ load by url action """

        if False is applogger.is_logged(params.get('url')):

            browser.ping(params.get('url'), params.get('port'))
            pass
        else:
            #@TODO prompt message to log rewrite
            pass

        exit('OK!')

        # scan = True
        #
        # if True is Log.is_logged(url):
        #
        #     message = Message().get('has_scanned').format(url).strip("\t")
        #
        #     try:
        #         text = raw_input(message)
        #         if text == "":
        #             scan = True
        #         else:
        #             scan = False
        #     except KeyboardInterrupt as e:
        #         sys.exit("\n {0}".format(Log.warning(Message().get('abort'))))
        #
        # if True is scan:
        #     result = Http().get(url, params)
        #     if result:
        #         Progress.view(result)
        #         is_logging = params.get('log', self.DEFAULT_LOGGING)
        #
        #         if True is is_logging:
        #             sys.stdout.write(Log.syslog(url, result))
        # sys.exit()


