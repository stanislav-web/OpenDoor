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

    Development: Stanislav WEB
"""

from urllib.error import URLError
from urllib.request import urlopen
import os
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
    __ANSI_RESET = "\033[0m"
    __ANSI_BOLD = "\033[1m"
    __ANSI_DIM = "\033[2m"
    __ANSI_CYAN = "\033[36m"
    __ANSI_BRIGHT_CYAN = "\033[96m"
    __ANSI_WHITE = "\033[97m"
    __ANSI_GRAY = "\033[90m"

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
        Return safe cross-platform update instructions.

        The scanner must not execute package-manager commands by itself.
        Different installation methods own different upgrade flows, so this
        command prints an explicit matrix and lets the user choose the command
        matching the way OpenDoor was installed.

        :raise PackageError:
        :return: str
        """

        try:
            status = Package.__update_instructions()
            upd_status = tpl.line(status, color="green")
            return CoreConfig.get("update").format(status=upd_status)

        except (AttributeError, CoreSystemError, TypeError) as error:
            raise PackageError(error)

    @classmethod
    def __update_instructions(cls):
        """
        Build update instructions for supported installation methods.

        :return: cross-platform update instructions
        :rtype: str
        """

        current_python = cls.__quote_command_arg(py_sys.executable or "python")
        current_platform = "Windows" if sys().is_windows else "Unix-like"

        return "\n".join([
            "OpenDoor does not self-update from inside the scanner.",
            "Use the same package manager that installed it.",
            "Current platform: {0}.".format(current_platform),
            "",
            "pipx:",
            "  pipx upgrade opendoor",
            "",
            "pip / current Python environment:",
            "  {0} -m pip install --upgrade opendoor".format(current_python),
            "",
            "Windows Python launcher:",
            "  py -m pip install --upgrade opendoor",
            "",
            "Homebrew:",
            "  brew update && brew upgrade opendoor",
            "",
            "Docker:",
            "  docker pull ghcr.io/stanislav-web/opendoor:latest",
            "",
            "Arch / BlackArch:",
            "  sudo pacman -Syu opendoor",
            "",
            "Debian / Kali:",
            "  sudo apt update",
            "  sudo apt install --only-upgrade opendoor",
            "",
            "Source checkout:",
            "  git pull --ff-only",
            "  {0} -m pip install -e .".format(current_python),
            "",
            "Do not mix package managers for the same installation.",
        ])

    @staticmethod
    def __quote_command_arg(value):
        """
        Quote a command argument for readable shell examples.

        :param str value: command argument
        :return: safely quoted argument
        :rtype: str
        """

        return '"{0}"'.format(str(value).replace('\\', '\\\\').replace('\"', '\\"'))

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

        The remote version is shown only when the local package is older.
        If the local version is current, newer, or the remote version is
        unavailable, only the local version is displayed.

        :raise PackageError:
        :return: str
        """

        try:
            local = Package.local_version()
            remote = Package.__remote_version()

            if remote == "unavailable":
                return tpl.line(local, color="green")

            if True is helper.is_less(local, remote):
                return "{0} -> {1}".format(
                    tpl.line(local, color="red"),
                    tpl.line(remote, color="green"),
                )

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
    def __stdout_is_tty():
        """
        Check whether stdout is an interactive terminal.

        :return: bool
        """

        stdout = getattr(py_sys, "stdout", None)

        if stdout is None or not hasattr(stdout, "isatty"):
            return False

        return bool(stdout.isatty())

    @staticmethod
    def __supports_banner_unicode():
        """
        Check whether Unicode block-art can be safely emitted.

        :return: bool
        """

        if os.environ.get("OPENDOOR_ASCII_BANNER"):
            return False

        if not Package.__stdout_is_tty():
            return False

        stdout = getattr(py_sys, "stdout", None)
        encoding = getattr(stdout, "encoding", None) or "utf-8"

        try:
            "█╔═║╚╝".encode(encoding)
            return True
        except UnicodeEncodeError:
            return False
        except LookupError:
            return False

    @staticmethod
    def __supports_banner_color():
        """
        Check whether ANSI banner colors can be safely emitted.

        The banner keeps plain ASCII output for pipes, redirected logs,
        CI-style non-TTY output, dumb terminals, and explicit NO_COLOR mode.

        :return: bool
        """

        if os.environ.get("NO_COLOR") or os.environ.get("OPENDOOR_NO_COLOR"):
            return False

        if os.environ.get("OPENDOOR_FORCE_COLOR"):
            return True

        if os.environ.get("TERM") == "dumb":
            return False

        if not Package.__stdout_is_tty():
            return False

        if os.name != "nt":
            return True

        return bool(
            os.environ.get("WT_SESSION")
            or os.environ.get("ANSICON")
            or os.environ.get("ConEmuANSI") == "ON"
            or os.environ.get("TERM")
            or os.environ.get("TERM_PROGRAM")
            or os.environ.get("PYCHARM_HOSTED")
        )

    @staticmethod
    def __paint(value, color, enabled):
        """
        Apply ANSI color to a value when banner colors are enabled.

        :param str value:
        :param str color:
        :param bool enabled:
        :return: str
        """

        if not enabled:
            return value

        return "{0}{1}{2}".format(color, value, Package.__ANSI_RESET)

    @staticmethod
    def __render_colored_block_art(colors_enabled):
        """
        Render colored OpenDoor block-art without fixed-width slicing.

        OPEN and DOOR are stored as separate parts so color boundaries cannot
        bleed into the second word.

        :param bool colors_enabled:
        :return: list[str]
        """

        open_lines = [
            "",
            "██████╗ ██████╗ ███████╗███╗   ██╗",
            "██╔═══██╗██╔══██╗██╔════╝████╗  ██║",
            "██║   ██║██████╔╝█████╗  ██╔██╗ ██║",
            "██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║",
            "╚██████╔╝██║     ███████╗██║ ╚████║",
            " ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝",
        ]

        door_lines = [
            "",
            "██████╗  ██████╗  ██████╗ ██████╗ ",
            "██╔══██╗██╔═══██╗██╔═══██╗██╔══██╗",
            "██║  ██║██║   ██║██║   ██║██████╔╝",
            "██║  ██║██║   ██║██║   ██║██╔══██╗",
            "██████╔╝╚██████╔╝╚██████╔╝██║  ██║",
            "╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝",
        ]

        result = [""]

        for open_line, door_line in zip(open_lines, door_lines):
            result.append(
                "    "
                + Package.__paint(open_line, Package.__ANSI_BRIGHT_CYAN + Package.__ANSI_BOLD, colors_enabled)
                + "    "
                + Package.__paint(door_line, Package.__ANSI_WHITE + Package.__ANSI_BOLD, colors_enabled)
            )

        result.extend([
            "",
            Package.__paint(
                "      fingerprints | waf-awareness | auto-calibration | smart scans",
                Package.__ANSI_GRAY,
                colors_enabled,
            ),
            "   ",
        ])

        return result

    @staticmethod
    def __render_plain_ascii_art():
        """
        Render portable plain ASCII banner art.

        :return: list[str]
        """

        return [
            "   ",
            "      ____  ____  _____ _   _      ____   ___   ___  ____",
            "     / __ \\|  _ \\| ____| \\ | |    |  _ \\ / _ \\ / _ \\|  _ \\",
            "    | |  | | |_) |  _| |  \\| |    | | | | | | | | | | |_) |",
            "    | |__| |  __/| |___| |\\  |    | |_| | |_| | |_| |  _ <",
            "     \\____/|_|   |_____|_| \\_|    |____/ \\___/ \\___/|_| \\_\\",
            "",
            "     fingerprints | waf-awareness | auto-calibration | smart scans",
            "   ",
        ]

    @staticmethod
    def __render_banner(info_lines):
        """
        Render the console startup banner without an outer frame.

        The Unicode block-art banner is used only for interactive terminals
        that can encode it. Other outputs keep the portable ASCII banner.

        :param list[str] info_lines:
        :return: str
        """

        colors_enabled = Package.__supports_banner_color()

        if Package.__supports_banner_unicode():
            art_lines = Package.__render_colored_block_art(colors_enabled)
        else:
            art_lines = Package.__render_plain_ascii_art()

        result = [*art_lines, ""]

        result.extend(
            Package.__paint(str(line), Package.__ANSI_CYAN, colors_enabled)
            for line in info_lines
        )

        separator = Package.__paint("=" * 70, Package.__ANSI_DIM + Package.__ANSI_GRAY, colors_enabled)

        return "\n".join(result) + "\n{0}\n".format(separator)

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
