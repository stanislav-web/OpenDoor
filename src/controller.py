# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development Team: Stanislav WEB
"""

from src.core.decorators import execution_time
from src.lib import ArgumentsError
from src.lib import BrowserError
from src.lib import PackageError
from src.lib import ReporterError
from src.lib import TplError
from src.lib import args
from src.lib import browser
from src.lib import events
from src.lib import package
from src.lib import reporter
from src.lib import tpl
from .exceptions import SrcError


class Controller(object):

    """Controller class"""

    def __init__(self):
        """
        Init constructor
        :raise SrcError
        """

        events.terminate()

        try:

            interpreter = package.check_interpreter()

            if interpreter is not True:
                raise SrcError(tpl.error(key='unsupported', actual=interpreter.get('actual'),
                                         expected=interpreter.get('expected')))
            else:
                self.ioargs = args().get_arguments()
        except ArgumentsError as error:
            raise SrcError(tpl.error(error))

    @execution_time(log=tpl)
    def run(self):
        """
        Bootstrap action
        :raise SrcError
        :return: None
        """

        try:

            tpl.message(package.banner())
            if 'host' in self.ioargs or 'wizard' in self.ioargs:
                getattr(self, 'scan_action')(self.ioargs)
            else:
                for action in self.ioargs.keys():

                    if hasattr(self, '{0}_action'.format(action))\
                            and args().is_arg_callable(getattr(self, '{0}_action'.format(action))):
                        getattr(self, '{func}_action'.format(func=action))()
                        break

        except (SrcError, PackageError, BrowserError, AttributeError) as error:
            raise SrcError(tpl.error(error))

    @staticmethod
    def examples_action():
        """
        Show examples action
        :return: None
        """

        tpl.message(package.examples())

    @staticmethod
    def update_action():
        """
        App update action
        :raise SrcError
        :return: None
        """

        try:
            tpl.message(package.update())
        except (AttributeError, PackageError) as error:
            raise SrcError(error)

    @staticmethod
    def docs_action():
        """
         Show app user guide

         :raise SrcError
         :return: None
         """

        try:
            package.docs()
        except (AttributeError, PackageError) as error:
            raise SrcError(error)

    @staticmethod
    def version_action():
        """
        Show app version action

        :raise SrcError
        :return: None
        """

        try:
            tpl.message(package.version())
        except (AttributeError, PackageError) as error:
            raise SrcError(error)

    @staticmethod
    def local_version():
        """
        Show app local version
        :raise SrcError
        :return: None
        """

        try:
            tpl.message(package.local_version())
        except (AttributeError, PackageError) as error:
            raise SrcError(error)

    @classmethod
    def scan_action(cls, params):
        """
        URL scan action
        :param dict params: console input args
        :raise SrcError
        :return: None
        """

        try:

            if 'wizard' in params:
                tpl.info(key='load_wizard', config=params['wizard'])
                params = package.wizard(params['wizard'])
            brows = browser(params)
            if True is reporter.is_reported(params.get('host')):
                try:
                    tpl.prompt(key='logged')
                except KeyboardInterrupt:
                    tpl.cancel(key='abort')

            if reporter.default is params.get('reports'):
                tpl.info(key='use_reports')

            brows.ping()
            brows.scan()
            brows.done()

        except (AttributeError, BrowserError, ReporterError, TplError) as error:
            raise SrcError(error)
        except (KeyboardInterrupt, SystemExit):
            tpl.cancel(key='abort')
