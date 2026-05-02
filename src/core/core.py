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

from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
import sys as py_sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_version() -> str:
    """
    Resolve the application version.

    Priority:
    1. VERSION file from the source checkout.
    2. Installed package metadata.

    :return: Current package version.
    """

    version_file = PROJECT_ROOT / 'VERSION'
    if version_file.exists():
        return version_file.read_text(encoding='utf-8').splitlines()[0].strip()

    try:
        return package_version('opendoor')
    except PackageNotFoundError:
        return '0.0.0'


def resolve_data_root() -> Path:
    """
    Resolve the bundled data directory for both source and installed package use.

    Source checkout usually stores dictionaries in `<repo>/data`.
    Installed wheel with `data_files` places them under `<sys.prefix>/data`.

    :return: Resolved data root path.
    """

    candidates = [
        PROJECT_ROOT / 'data',
        Path(py_sys.prefix) / 'data',
        Path(py_sys.base_prefix) / 'data',
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return PROJECT_ROOT / 'data'


RUNTIME_ROOT = Path.cwd()
DATA_ROOT = resolve_data_root()
fVersion = read_version()

CoreConfig = {
    'info': {
        'name': 'Opendoor scanner',
        'repository': 'https://github.com/stanislav-web/OpenDoor.git',
        'remote_version': 'https://raw.githubusercontent.com/stanislav-web/OpenDoor/master/VERSION',
        'license': 'License: GNU GPL V3 (2016 - 2026)',
        'version': fVersion,
        'documentation': 'https://opendoor.readthedocs.io',
        'required_versions': {
            'minor': '3.12',
            'major': '3.14'
        },
    },
    'data': {
        'directories': str(DATA_ROOT / 'directories.dat'),
        'ignored': str(DATA_ROOT / 'ignored.dat'),
        'proxies': str(DATA_ROOT / 'proxies.dat'),
        'subdomains': str(DATA_ROOT / 'subdomains.dat'),
        'useragents': str(DATA_ROOT / 'useragents.dat'),
        'tmplist': str(RUNTIME_ROOT / 'tmp' / 'list.tmp'),
        'extensionlist': str(RUNTIME_ROOT / 'tmp' / 'extensionlist.tmp'),
        'ignore_extensionlist': str(RUNTIME_ROOT / 'tmp' / 'ignore_extensionlist.tmp'),
        'reports': str(RUNTIME_ROOT / 'reports'),
        'exceptions_log': str(RUNTIME_ROOT / 'syslog' / 'exceptions.log'),
    },
    'command': {
        'cvsupdate': '/usr/bin/env python3 -m pip install --upgrade opendoor',
        'cvslog': '/usr/bin/env python3 -m pip show opendoor',
    },
    'examples': """

            Examples:
                python3 ./opendoor.py  --examples
                python3 ./opendoor.py  --update
                python3 ./opendoor.py  --version
                python3 ./opendoor.py  --docs
                python3 ./opendoor.py  --wizard
                python3 ./opendoor.py  --wizard /usr/local/projects/my.conf
                python3 ./opendoor.py --host "http://example.com"
                python3 ./opendoor.py --host "https://example.com" --port 8080
                python3 ./opendoor.py --host "http://example.com" --scan subdomains
                python3 ./opendoor.py --host "http://example.com" --threads 10
                python3 ./opendoor.py --host "http://example.com" -random-list --extensions php,html
                python3 ./opendoor.py --host "http://example.com" -random-list --ignore-extensions aspx,jsp
                python3 ./opendoor.py --host "http://example.com" --threads 10 --random-list
                python3 ./opendoor.py --host "http://example.com" --threads 10 --random-agent
                python3 ./opendoor.py --host "http://example.com" --threads 10 --proxy-pool
                python3 ./opendoor.py --host "http://example.com" --threads 10 --delay 10
                python3 ./opendoor.py --host "http://example.com" --threads 10 --prefix en/
                python3 ./opendoor.py --host "http://example.com" --threads 10 --delay 10 --timeout 10
                python3 ./opendoor.py --host "http://example.com"  --random-list --threads 10 --delay 10 --timeout 10
                python3 ./opendoor.py --host "http://example.com" --threads 10 --delay 10 --timeout 10 --debug 1
                python3 ./opendoor.py --host "http://example.com" --threads 10 --debug 1 --reports std,txt,json,html,sqlite
                python3 ./opendoor.py --host "http://example.com" --debug 1 --reports std,txt --reports-dir /reports
                python3 ./opendoor.py --host "http://example.com" --threads 10 --debug 1 --extensions php,html
            """,
    'banner': r"""
        .... ---------+-------------------------------+--------- ....
    ____   _____  ______ _   _        .----.        _____    ____    ____   _____
  / ____||  __ \|  ____|| \ | |      / .--. \      |  __ \  / __ \  / __ \ |  __ \
 | |  __ | |__) | |__   |  \| |     | |    | |     | |  | || |  | || |  | || |__) |
 | |  | ||  ___/|  __|  | . ` |     | | () | |     | |  | || |  | || |  | ||  _  /
 | |__| || |    | |____ | |\  |     | |____| |     | |__| || |__| || |__| || | \ \
  \_____||_|    |______||_| \_|      \____/      |_____/  \____/  \____/ |_|  \_\
        .... -----+----- scan through the open door -----+----- ....

{0}
{1}
{2}
{3}
{4}""",
    'version': """

{0}: {1} -> {2}
{3}
{4}
============================================================""",
    'update': """

{status}
============================================================"""
}