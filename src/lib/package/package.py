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

    Development Team: Brain Storm Team
"""

from urllib.error import URLError
from urllib.request import urlopen

from src.core import CoreConfig
from src.core import CoreSystemError, FileSystemError
from src.core import filesystem
from src.core import helper
from src.core import sys
# noinspection PyPep8Naming
from src.lib.tpl import Tpl as tpl
from .exceptions import PackageError


class Package(object):
    """Package class."""

    remote_version = None

    @staticmethod
    def check_interpreter():
        """
        Validate the current Python interpreter version.

        The supported version range is defined in CoreConfig and treated as
        inclusive boundaries.

        :return: True if the interpreter is supported, otherwise a dict with
                 mismatch details.
        """

        versions = CoreConfig.get('info').get('required_versions')
        actual_version = sys.version()
        min_version = versions.get('minor')
        max_version = versions.get('major')

        is_too_old = helper.is_less(actual_version, min_version)
        is_too_new = helper.is_more(actual_version, max_version)

        if is_too_old or is_too_new:
            return {
                'status': False,
                'actual': actual_version,
                'expected': f'{min_version} -> {max_version}',
            }

        return True

    @staticmethod
    def examples():
        """
        Load usage examples.

        :return: str
        """

        return CoreConfig.get('examples')

    @staticmethod
    def banner():
        """
        Build the application banner with fixed-width lines.

        This implementation intentionally avoids injecting banner data through
        the old template with tab characters. It renders each line with a
        deterministic width so the right border is always aligned.

        :raise PackageError:
        :return: str
        """

        try:
            info_lines = [
                'Directories: {0}'.format(Package.__directories_count()),
                'Subdomains: {0}'.format(Package.__subdomains_count()),
                'Browsers: {0}'.format(Package.__browsers_count()),
                'Proxies: {0}'.format(Package.__proxies_count()),
                Package.__license(),
            ]

            return Package.__render_banner(info_lines)

        except (FileSystemError, CoreSystemError, PackageError) as error:
            raise PackageError(error)

    @staticmethod
    def version():
        """
        Build application version information.

        :raise PackageError:
        :return: str
        """

        try:
            version = CoreConfig.get('version').format(
                Package.__app_name(),
                Package.__current_version(),
                Package.__remote_version(),
                Package.__repo(),
                Package.__license(),
            )
            return version

        except (FileSystemError, CoreSystemError, PackageError) as error:
            raise PackageError(error)

    @staticmethod
    def wizard(config):
        """
        Read wizard values from a config file.

        :param str config: Configuration filename.
        :raise PackageError:
        :return: dict
        """

        try:
            config = filesystem.readcfg(config)
            # noinspection PyProtectedMember
            params = dict(config._sections['general'])

            for key, val in params.items():
                params[key] = None if val == 'None' else val

                if params[key] is not None:
                    if params[key].isdigit():
                        params[key] = int(float(params[key]))
                    elif params[key] in ['True', 'False']:
                        params[key] = params[key] == 'True'
                    else:
                        params[key] = params[key].strip()

            return params

        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def docs():
        """
        Open documentation in a browser.

        :return: bool
        """

        docurl = CoreConfig.get('info').get('documentation')
        return helper.openbrowser(docurl)

    @staticmethod
    def update():
        """
        Return modern update instructions.

        The application should not mutate a local Git checkout internally.
        Updating should be done through pip for installed packages, or through
        normal Git workflow when the user works from source.

        :raise PackageError:
        :return: str
        """

        try:
            if False is sys().is_windows:
                command = CoreConfig.get('command').get('cvsupdate')
                status = (
                    'Automatic in-place update is disabled. '
                    'Update the installed package with: {0} '
                    'or pull the latest source manually from the repository.'
                ).format(command)
                upd_status = tpl.line(status, color='green')
                msg = CoreConfig.get('update').format(status=upd_status)
            else:
                msg = CoreConfig.get('update').format(status=tpl.line(key='upd_win_stat'))

            return msg

        except (AttributeError, CoreSystemError) as error:
            raise PackageError(error)

    @staticmethod
    def local_version():
        """
        Get the local application version.

        :raise PackageError:
        :return: str
        """

        try:
            return CoreConfig.get('info').get('version')
        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __app_name():
        """
        Get application name.

        :raise PackageError:
        :return: str
        """

        try:
            return CoreConfig.get('info').get('name')
        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __remote_version():
        """
        Fetch the latest known remote version.

        This implementation intentionally avoids shelling out to curl.
        If the remote version cannot be fetched, the command still works and
        reports 'unavailable' instead of failing.

        :raise PackageError:
        :return: str
        """

        if Package.remote_version is not None:
            return Package.remote_version

        try:
            request_uri = CoreConfig.get('info').get('remote_version')

            with urlopen(request_uri, timeout=5) as response:
                body = response.read().decode('utf-8', errors='replace').strip()

            Package.remote_version = body.splitlines()[0] if body else 'unavailable'
            return Package.remote_version

        except (URLError, ValueError, OSError, FileSystemError, CoreSystemError):
            Package.remote_version = 'unavailable'
            return Package.remote_version

    @staticmethod
    def __current_version():
        """
        Get the current application version with colorized status.

        :raise PackageError:
        :return: str
        """

        try:
            local = Package.local_version()
            remote = Package.__remote_version()

            if remote == 'unavailable':
                return tpl.line(local, color='green')

            if True is helper.is_less(local, remote):
                return tpl.line(local, color='red')

            return tpl.line(local, color='green')

        except (FileSystemError, CoreSystemError, PackageError) as error:
            raise PackageError(error)

    @staticmethod
    def __repo():
        """
        Get repository URL.

        :raise PackageError:
        :return: str
        """

        try:
            return CoreConfig.get('info').get('repository')
        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __license():
        """
        Get license information.

        :raise PackageError:
        :return: str
        """

        try:
            return CoreConfig.get('info').get('license')
        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __directories_count():
        """
        Get the number of directories in the main wordlist.

        :raise PackageError:
        :return: int
        """

        try:
            filename = CoreConfig.get('data').get('directories')
            return filesystem.count_lines(filename)

        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __subdomains_count():
        """
        Get the number of subdomains in the main wordlist.

        :raise PackageError:
        :return: int
        """

        try:
            filename = CoreConfig.get('data').get('subdomains')
            return filesystem.count_lines(filename)

        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __browsers_count():
        """
        Get the number of user agents in the bundled list.

        :raise PackageError:
        :return: int
        """

        try:
            filename = CoreConfig.get('data').get('useragents')
            return filesystem.count_lines(filename)

        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __proxies_count():
        """
        Get the number of proxies in the bundled list.

        :raise PackageError:
        :return: int
        """

        try:
            filename = CoreConfig.get('data').get('proxies')
            return filesystem.count_lines(filename)

        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __render_banner(info_lines):
        """
        Render banner with deterministic width.

        :param list[str] info_lines: Informational lines to place below the ASCII logo.
        :return: str
        """

        width = 58
        border = '#' * (width + 2)

        art_lines = [
            '#   _____  ____  ____  _  _    ____   _____  _____  ____   #',
            '#  (  _  )(  _ \\( ___)( \\( )  (  _ \\ (  _  )(  _  )(  _ \\  #',
            '#   )(_)(  )___/ )__)  )  (    )(_) ) )(_)(  )(_)(  )   /  #',
            '#  (_____)(__)  (____)(_ )_)  (____/ (_____)(_____)(_ )_)  #',
        ]

        def normalize_line(line: str) -> str:
            """
            Normalize a pre-framed line to the expected width.

            :param str line: Raw banner line.
            :return: Normalized line.
            """
            content = line[1:-1] if line.startswith('#') and line.endswith('#') else line
            return '#' + content.ljust(width)[:width] + '#'

        def framed_text(text: str) -> str:
            """
            Render one plain informational line inside the banner frame.

            :param str text: Text content.
            :return: Rendered frame line.
            """
            return '#  ' + text.ljust(width - 2)[:width - 2] + '#'

        result = [
            border,
            '#' + (' ' * width) + '#',
        ]

        for line in art_lines:
            result.append(normalize_line(line))

        result.append('#' + (' ' * width) + '#')

        for line in info_lines:
            result.append(framed_text(line))

        result.append(border)

        return '\n'.join(result)