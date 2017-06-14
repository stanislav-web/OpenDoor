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

CoreConfig = {
    'info': {
        'name': 'Opendoor scanner',
        'repository': 'git@github.com:stanislav-web/OpenDoor.git',
        'setup': 'https://raw.githubusercontent.com/stanislav-web/OpenDoor/master/setup.cfg',
        'license': 'License: GNU General Public License',
        'version': '3.3.36-rc',
    },
    'opendoor': {
        'directories': 'data/directories.dat',
        'ignored': 'data/ignored.dat',
        'proxies': 'data/proxies.dat',
        'subdomains': 'data/subdomains.dat',
        'useragents': 'data/useragents.dat',
        'tmplist': 'tmp/list.tmp',
        'extensionlist': 'tmp/extensionlist.tmp',
        'reports': 'reports/',
    },
    'system': {
        'exceptions_log': 'syslog/exceptions.log',
    }
}
