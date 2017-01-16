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

    Development Team: Stanislav Menshov
"""

from src.core import process
from src.core import filesystem
from src.core import helper
from src.core import sys
from src.core import SystemError, FileSystemError

from src.lib import tpl

from .config import Config
from ...lib.exceptions import LibError


class Package:
    """Package class"""

    remote_version = None

    @staticmethod
    def check_interpreter():
        """
        Get interpreter version

        :return: dict or bool
        """

        expected_version = Config.params.get('required_version')
        actual_version = sys.version()

        if True is helper.is_less(expected_version, actual_version)\
            or True is helper.is_more(expected_version, actual_version):

            return {
                'status' : False,
                'actual' : actual_version,
                'expected' : expected_version
            }
        else:
            return True

    @staticmethod
    def examples():
        """
        Load examples of usage

        :return: None
        """

        tpl.message(Config.params.get('examples'))

    @staticmethod
    def banner():
        """
        Load application banner

        :raise LibError
        :return: None
        """

        try:

            banner = Config.params.get('banner').format(
                tpl.line('Directories: {0}'.format(Package.__directories_count()), color='blue'),
                tpl.line('Subdomains: {0}'.format(Package.__subdomains_count()), color='blue'),
                tpl.line('Browsers: {0}'.format(Package.__browsers_count()), color='blue'),
                tpl.line('Proxies: {0}'.format(Package.__proxies_count()), color='blue'),
                tpl.line(Package.__license(), color='blue'))
            tpl.message(banner)

        except (FileSystemError, SystemError, LibError) as e:
            raise LibError(e)

    @staticmethod
    def version():
        """
        Load application version

        :raise LibError
        :return: None
        """

        try:

            version = Config.params.get('version').format(
                Package.__app_name(),
                Package.__current_version(),
                Package.__remote_version(),
                Package.__repo(),
                Package.__license())

            tpl.message(version)

        except (FileSystemError, SystemError, LibError) as e:
            raise LibError(e)

    @staticmethod
    def cursor(state):

        """
        Set cursor state

        :raise LibError
        :return: None
        """

        try:

            process.system(Config.params.get('cursor').format(state=state))

        except SystemError as e:
            raise LibError(e)

    @staticmethod
    def update():
        """
        Check for update

        :raise LibError
        :return: None
        """

        try:
            status = process.execute(Config.params.get('cvsupdate'))
            upd_status = tpl.line(status, color='green')

            banner = Config.params.get('update').format(
                status=upd_status)

            tpl.message(banner)

        except SystemError as e:
            raise LibError(e)

    @staticmethod
    def local_version():
        """
        Get application local version

        :raise LibError
        :return: str
        """

        try :
            config = filesystem.readcfg(Config.params.get('cfg'))
            return config.get('info', 'version')
        except FileSystemError as e:
            raise LibError(e)

    @staticmethod
    def __app_name():
        """
        Get application name

        :raise LibError
        :return: str
        """

        try :
            config = filesystem.readcfg(Config.params.get('cfg'))
            return config.get('info', 'name')
        except FileSystemError as e:
            raise LibError(e)

    @staticmethod
    def __remote_version():
        """
        Get application remote version

        :raise LibError
        :return: str
        """
        if None is Package.remote_version:

            try:
                config = filesystem.readcfg(Config.params.get('cfg'))
                request_uri = config.get('info', 'setup')
                result = process.execute('curl -sb GET {uri}'.format(uri=request_uri))
                raw = filesystem.readraw(result)
                Package.remote_version = raw.get('info', 'version')
                return Package.remote_version
            except (FileSystemError, SystemError) as e:
                raise LibError(e)
        else:
            return Package.remote_version

    @staticmethod
    def __current_version():
        """
        Get application current version

        :raise LibError
        :return: str
        """

        try :
            local = Package.local_version()
            remote = Package.__remote_version()

            if True is helper.is_less(local, remote):
                version = tpl.line(local, color='red')
            else:
                version = tpl.line(local, color='green')
            return version

        except (FileSystemError, SystemError, LibError) as e:
            raise LibError(e)

    @staticmethod
    def __repo():
        """
        Get application repository url

        :raise LibError
        :return: str
        """

        try :
            config = filesystem.readcfg(Config.params.get('cfg'))
            return config.get('info', 'repository')
        except FileSystemError as e:
            raise LibError(e)

    @staticmethod
    def __license():
        """
        Get application license

        :raise LibError
        :return: str
        """

        try :
            config = filesystem.readcfg(Config.params.get('cfg'))
            return config.get('info', 'license')
        except FileSystemError as e:
            raise LibError(e)

    @staticmethod
    def __directories_count():
        """
        Get number of directories in basic wordlist

        :raise LibError
        :return: int
        """

        try :
            config = filesystem.readcfg(Config.params.get('cfg'))
            filename = config.get('opendoor', 'directories')
            count = filesystem.read(filename).__len__()
            return count

        except FileSystemError as e:
            raise LibError(e)

    @staticmethod
    def __subdomains_count():
        """
        Get number of subdomains in basic wordlist

        :raise LibError
        :return: int
        """

        try :
            config = filesystem.readcfg(Config.params.get('cfg'))
            filename = config.get('opendoor', 'subdomains')
            count = filesystem.read(filename).__len__()

            return count

        except FileSystemError as e:
            raise LibError(e)

    @staticmethod
    def __browsers_count():
        """
        Get number of browsers in basic wordlist

        :raise LibError
        :return: int
        """

        try :
            config = filesystem.readcfg(Config.params.get('cfg'))
            filename = config.get('opendoor', 'useragents')
            count = filesystem.read(filename).__len__()

            return count

        except FileSystemError as e:
            raise LibError(e)

    @staticmethod
    def __proxies_count():
        """
        Get number of proxies in basic wordlist

        :raise LibError
        :return: int
        """

        try :
            config = filesystem.readcfg(Config.params.get('cfg'))
            filename = config.get('opendoor', 'proxies')
            count = filesystem.read(filename).__len__()

            return count

        except FileSystemError as e:
            raise LibError(e)
