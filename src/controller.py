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

from src.lib import ArgumentsError
from src.lib import BrowserError
from src.lib import PackageError
from src.lib import ReporterError
from src.lib import reporter
from src.lib import args
from src.lib import browser
from src.lib import events
from src.lib import package
from src.lib import tpl
from . import execution_time
from .exceptions import SrcError


class Controller:
    """Controller class"""

    def __init__(self):
        """
        Init constructor
        :raise SrcError
        """

        events.terminate()

        try:

            interpreter = package.check_interpreter()

            if True != interpreter:
                raise SrcError(tpl.error(key='unsupported', actual=interpreter.get('actual'),
                                         expected=interpreter.get('expected')))

            self.ioargs = args().get_arguments()
        except ArgumentsError as e:
            raise SrcError(tpl.error(e.message))

    @execution_time(log=tpl)
    def run(self):
        """
        Bootstrap action
        :raise SrcError
        :return: None
        """

        try:

            package.banner()

            if 'host' in self.ioargs:
                getattr(self, 'scan_action')(self.ioargs)
            else:
                for action, args in self.ioargs.iteritems():
                    if hasattr(self, '{0}_action'.format(action)) and callable(
                            getattr(self, '{0}_action'.format(action))):
                        getattr(self, '{func}_action'.format(func=action))()
                        break

        except (SrcError, PackageError, BrowserError, AttributeError) as e:
            raise SrcError(tpl.error(e.message))

    @staticmethod
    def examples_action():
        """
        Show examples action
        :return: None
        """

        package.examples()

    @staticmethod
    def update_action():
        """
        App update action
        :raise SrcError
        :return: None
        """

        try:
            package.update()
        except (AttributeError, PackageError) as e:
            raise SrcError(e)

    @staticmethod
    def version_action():
        """
        Show app version action

        :raise SrcError
        :return: None
        """

        try:
            package.version()
        except (AttributeError, PackageError) as e:
            raise SrcError(e)

    @staticmethod
    def local_version():
        """
        Show app local version
        :raise SrcError
        :return: None
        """

        try:
            return package.local_version()
        except (AttributeError, PackageError) as e:
            raise SrcError(e)

    def scan_action(self, params=()):
        """
        URL scan action
        :param dict params: console input args
        :raise SrcError
        :return: None
        """

        brows = browser(params)

        if False is reporter.is_reported(params.get('host')):

            if reporter.default is params.get('reports'):
                tpl.info(key='use_reports')

            try:

                brows.ping()
                brows.scan()
                brows.done()

            except (AttributeError, BrowserError, ReporterError) as e:
                raise SrcError(e.message)
            except (KeyboardInterrupt, SystemExit):
                tpl.cancel(key='abort')

        else:
            try:
                raw_input(tpl.line(key='logged', color='yellow', host=params.get('host')))
            except KeyboardInterrupt:
                tpl.cancel(key='abort')
