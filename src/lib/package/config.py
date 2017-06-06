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


class Config(object):
    """Config class"""

    params = {
        'cvsupdate': '/usr/bin/git pull origin master',
        'cvslog': '/usr/bin/git log --oneline -n 1',
        'cfg': 'setup.cfg',
        'documentations': 'https://github.com/stanislav-web/OpenDoor/wiki',
        'required_versions': {
            'minor': '3.3',
            'major': '3.6'
        },
        'examples': """

            Examples:
                python ./opendoor.py  --examples
                python ./opendoor.py  --update
                python ./opendoor.py  --version
                python ./opendoor.py --host "http://example.com"
                python ./opendoor.py --host "https://example.com" --port 8080
                python ./opendoor.py --host "http://example.com" --scan subdomains
                python ./opendoor.py --host "http://example.com" --threads 10
                python ./opendoor.py --host "http://example.com" --threads 10 --tor
                python ./opendoor.py --host "http://example.com" --threads 10 --delay 10
                python ./opendoor.py --host "http://example.com" --threads 10 --prefix en/
                python ./opendoor.py --host "http://example.com" --threads 10 --delay 10 --timeout 10
                python ./opendoor.py --host "http://example.com"  --random-list --threads 10 --delay 10 --timeout 10
                python ./opendoor.py --host "http://example.com" --threads 10 --delay 10 --timeout 10 --debug 1
                python ./opendoor.py --host "http://example.com" --threads 10 --debug 1 --reports std,txt
                python ./opendoor.py --host "http://example.com" --debug 1 --reports std,txt --reports-dir /reports
                python ./opendoor.py --host "http://example.com" --threads 10 --debug 1 --extensions php,html
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
============================================================"""}
