# -*- coding: utf-8 -*-

"""Controller class"""

from src.lib import args
from src.lib import package

class Controller:
    """Controller class"""

    def __init__(self):
        """init constructor"""

        self.ioargs = args().get()

    def run(self):
        """ run action """

        for action, args in self.ioargs.iteritems():

            if 'url' is not action:
                getattr(self, '{func}_action'.format(func=action))()
            else:
                getattr(self, '{func}_action'.format(func=action))(self.ioargs)
            break

    @staticmethod
    def examples_action():
        """ show examples action """

        package.load_examples()

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


