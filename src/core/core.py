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

CoreConfig = {
    'info': {
        'name': 'Opendoor scanner',
        'repository': 'git@github.com:stanislav-web/OpenDoor.git',
        'remote_version': 'https://raw.githubusercontent.com/stanislav-web/OpenDoor/master/VERSION',
        'license': 'License: GNU General Public License',
        'version': '4.0.6',
        'documentation': 'https://opendoor.readthedocs.org',
        'required_versions': {
            'minor': '3.9',
            'major': '3.10'
        },
    },
    'data': {
        'directories': 'data/directories.dat',
        'ignored': 'data/ignored.dat',
        'proxies': 'data/proxies.dat',
        'subdomains': 'data/subdomains.dat',
        'useragents': 'data/useragents.dat',
        'tmplist': 'tmp/list.tmp',
        'extensionlist': 'tmp/extensionlist.tmp',
        'ignore_extensionlist': 'tmp/ignore_extensionlist.tmp',
        'reports': 'reports/',
        'exceptions_log': 'syslog/exceptions.log',
    },
    'command': {
        'cvsupdate': '/usr/bin/git pull origin master',
        'cvslog': '/usr/bin/git log --oneline -n 1',
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
                python3 ./opendoor.py --host "http://example.com" --threads 10 --tor
                python3 ./opendoor.py --host "http://example.com" --threads 10 --delay 10
                python3 ./opendoor.py --host "http://example.com" --threads 10 --prefix en/
                python3 ./opendoor.py --host "http://example.com" --threads 10 --delay 10 --timeout 10
                python3 ./opendoor.py --host "http://example.com"  --random-list --threads 10 --delay 10 --timeout 10
                python3 ./opendoor.py --host "http://example.com" --threads 10 --delay 10 --timeout 10 --debug 1
                python3 ./opendoor.py --host "http://example.com" --threads 10 --debug 1 --reports std,txt
                python3 ./opendoor.py --host "http://example.com" --debug 1 --reports std,txt --reports-dir /reports
                python3 ./opendoor.py --host "http://example.com" --threads 10 --debug 1 --extensions php,html
            """, 'banner': """
############################################################
#                                                          #
#   _____  ____  ____  _  _    ____   _____  _____  ____   #
#  (  _  )(  _ \( ___)( \( )  (  _ \ (  _  )(  _  )(  _ \  #
#   )(_)(  )___/ )__)  )  (    )(_) ) )(_)(  )(_)(  )   /  #
#  (_____)(__)  (____)(_)\_)  (____/ (_____)(_____)(_)\_)  #
#                                                          #
#  {0}\t\t                           #
#  {1}\t\t                           #
#  {2}\t\t\t                   #
#  {3}\t\t\t                           #
#  {4}                     #
############################################################""", 'version': """

{0}: {1} -> {2}
{3}
{4}
============================================================""", 'update': """

{status}
============================================================"""
}
