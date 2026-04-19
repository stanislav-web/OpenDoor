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
import sys as py_sys

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

        The configured version boundaries are interpreted as inclusive
        major.minor versions. For example:
        - minimum `3.12` allows `3.12.x` and higher
        - maximum `3.14` allows `3.14.x`

        :return: True when the interpreter is supported, otherwise a dict with
                 mismatch details.
        """

        versions = CoreConfig.get("info").get("required_versions")
        min_version = Package.__parse_version_boundary(versions.get("minor"))
        max_version = Package.__parse_version_boundary(versions.get("major"))
        actual_version = (py_sys.version_info.major, py_sys.version_info.minor)

        if actual_version < min_version or actual_version > max_version:
            return {
                "status": False,
                "actual": f"{py_sys.version_info.major}.{py_sys.version_info.minor}",
                "expected": f"{versions.get('minor')} -> {versions.get('major')}",
            }

        return True

    @staticmethod
    def examples():
        """
        Get examples from core config.

        :return: str
        """

        return CoreConfig.get("examples")

    @staticmethod
    def banner():
        """
        Build the application banner with fixed-width lines.

        :raise PackageError:
        :return: str
        """

        try:
            info_lines = [
                "Directories: {0}".format(Package.__directories_count()),
                "Subdomains: {0}".format(Package.__subdomains_count()),
                "Browsers: {0}".format(Package.__browsers_count()),
                "Proxies: {0}".format(Package.__proxies_count()),
                Package.__license(),
            ]

            return Package.__render_banner(info_lines)

        except (FileSystemError, CoreSystemError, PackageError) as error:
            raise PackageError(error)

    @staticmethod
    def version():
        """
        Get package version info.

        :raise PackageError:
        :return: str
        """

        try:
            version = CoreConfig.get("version").format(
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
        Wizard runner.

        :param str config:
        :raise PackageError:
        :return: dict
        """

        try:
            config = filesystem.readcfg(config)
            # noinspection PyProtectedMember
            params = dict(config._sections["general"])

            for key, val in params.items():
                params[key] = None if val == "None" else val

                if params[key] is not None:
                    if params[key].isdigit():
                        params[key] = int(float(params[key]))
                    elif params[key] in ["True", "False"]:
                        params[key] = params[key] == "True"
                    else:
                        params[key] = params[key].strip()

            return params

        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def docs():
        """
        Open browser with docs.

        :return: bool
        """

        docurl = CoreConfig.get("info").get("documentation")
        return helper.openbrowser(docurl)

    @staticmethod
    def update():
        """
        Return update instructions.

        :raise PackageError:
        :return: str
        """

        try:
            if False is sys().is_windows:
                command = CoreConfig.get("command").get("cvsupdate")
                status = (
                    "Automatic in-place update is disabled. "
                    "Update the installed package with: {0} "
                    "or pull the latest source manually from the repository."
                ).format(command)
                upd_status = tpl.line(status, color="green")
                msg = CoreConfig.get("update").format(status=upd_status)
            else:
                msg = CoreConfig.get("update").format(status=tpl.line(key="upd_win_stat"))

            return msg

        except (AttributeError, CoreSystemError) as error:
            raise PackageError(error)

    @staticmethod
    def local_version():
        """
        Get local version.

        :raise PackageError:
        :return: str
        """

        try:
            return CoreConfig.get("info").get("version")
        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __app_name():
        """
        Get app name.

        :raise PackageError:
        :return: str
        """

        try:
            return CoreConfig.get("info").get("name")
        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __remote_version():
        """
        Get remote version from repository.

        :raise PackageError:
        :return: str
        """

        if Package.remote_version is not None:
            return Package.remote_version

        try:
            request_uri = CoreConfig.get("info").get("remote_version")

            with urlopen(request_uri, timeout=5) as response:
                body = response.read().decode("utf-8", errors="replace").strip()

            Package.remote_version = body.splitlines()[0] if body else "unavailable"
            return Package.remote_version

        except (URLError, ValueError, OSError, FileSystemError, CoreSystemError):
            Package.remote_version = "unavailable"
            return Package.remote_version

    @staticmethod
    def __current_version():
        """
        Get current version with colorized state.

        :raise PackageError:
        :return: str
        """

        try:
            local = Package.local_version()
            remote = Package.__remote_version()

            if remote == "unavailable":
                return tpl.line(local, color="green")

            if True is helper.is_less(local, remote):
                return tpl.line(local, color="red")

            return tpl.line(local, color="green")

        except (FileSystemError, CoreSystemError, PackageError) as error:
            raise PackageError(error)

    @staticmethod
    def __repo():
        """
        Get repository url.

        :raise PackageError:
        :return: str
        """

        try:
            return CoreConfig.get("info").get("repository")
        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __license():
        """
        Get package license.

        :raise PackageError:
        :return: str
        """

        try:
            return CoreConfig.get("info").get("license")
        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __directories_count():
        """
        Directories count.

        :raise PackageError:
        :return: int
        """

        try:
            filename = CoreConfig.get("data").get("directories")
            return filesystem.count_lines(filename)

        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __subdomains_count():
        """
        Subdomains count.

        :raise PackageError:
        :return: int
        """

        try:
            filename = CoreConfig.get("data").get("subdomains")
            return filesystem.count_lines(filename)

        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __browsers_count():
        """
        Browsers count.

        :raise PackageError:
        :return: int
        """

        try:
            filename = CoreConfig.get("data").get("useragents")
            return filesystem.count_lines(filename)

        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __proxies_count():
        """
        Proxies count.

        :raise PackageError:
        :return: int
        """

        try:
            filename = CoreConfig.get("data").get("proxies")
            return filesystem.count_lines(filename)

        except FileSystemError as error:
            raise PackageError(str(error))

    @staticmethod
    def __render_banner(info_lines):
        """
        Render fixed-width banner.

        :param list[str] info_lines:
        :return: str
        """

        width = 58
        border = "#" * (width + 2)

        art_lines = [
            "#   _____  ____  ____  _  _    ____   _____  _____  ____   #",
            "#  (  _  )(  _ \\( ___)( \\( )  (  _ \\ (  _  )(  _  )(  _ \\  #",
            "#   )(_)(  )___/ )__)  )  (    )(_) ) )(_)(  )(_)(  )   /  #",
            "#  (_____)(__)  (____)(_ )_)  (____/ (_____)(_____)(_ )_)  #",
        ]

        def normalize_line(line):
            """
            Normalize banner art line to the expected width.

            :param str line:
            :return: str
            """

            content = line[1:-1] if line.startswith("#") and line.endswith("#") else line
            return "#" + content.ljust(width)[:width] + "#"

        def framed_text(text):
            """
            Render text line inside banner frame.

            :param str text:
            :return: str
            """

            return "#  " + text.ljust(width - 2)[: width - 2] + "#"

        result = [
            border,
            "#" + (" " * width) + "#",
        ]

        for line in art_lines:
            result.append(normalize_line(line))

        result.append("#" + (" " * width) + "#")

        for line in info_lines:
            result.append(framed_text(line))

        result.append(border)

        return "\n".join(result)

    @staticmethod
    def __parse_version_boundary(raw_version):
        """
        Parse configured major.minor boundary into a comparable tuple.

        Only the first two numeric parts are used because the application
        currently declares support by major.minor ranges.

        :param str raw_version:
        :return: tuple[int, int]
        """

        parts = str(raw_version).strip().split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return major, minor