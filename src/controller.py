# -*- coding: utf-8 -*-

"""Controller class"""

from src.lib import args
from src.lib import package
from src.lib import browser
from src.lib import applog
from src.lib import tpl
from src.lib import LibError

from .exceptions import SrcError

class Controller:
    """Controller class"""

    def __init__(self):
        """init constructor"""

        try :
            self.ioargs = args().get_arguments()
        except LibError as e:
            raise SrcError(tpl.error(e.message))

    def run(self):
        """ run action """

        try:

            package.banner()

            if 'host' in self.ioargs:
                getattr(self, 'host_action')(self.ioargs)
            else:
                for action, args in self.ioargs.iteritems():
                    if hasattr(self, '{0}_action'.format(action)) and callable(
                            getattr(self, '{0}_action'.format(action))):
                        getattr(self, '{func}_action'.format(func=action))()
                        break

        except (LibError, SrcError) as e:
            raise SrcError(tpl.error(e.message))


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


    def host_action(self, params=()):
        """ load by host action """

        brows = browser(params)
        if False is applog.is_logged(params.get('host')):

            if None is params.get('log'):
                tpl.info(key='use_log')

            try:
                brows.ping()
                brows.scan()
            except LibError as e:
                raise SrcError(e)

        else:
            try:
                raw_input(
                    tpl.inline(key='logged', color='yellow',host=params.get('host'))
                )
            except KeyboardInterrupt:
                tpl.cancel(key='abort')
