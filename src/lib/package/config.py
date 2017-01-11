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


class Config:
    """Config class"""

    params = {
        'cvsupdate' : '/usr/bin/git pull origin master',
        'cvslog'    : '/usr/bin/git log --oneline -n 1',
        'cfg'       : 'setup.cfg',
        'required_version': '2.7',
        'examples'  :  """

            Examples:
                python ./opendoor.py  --examples
                python ./opendoor.py  --update
                python ./opendoor.py  --version
                python ./opendoor.py --host "http://joomla-ua.org"
                python ./opendoor.py --host "https://joomla-ua.org" --port 8080
                python ./opendoor.py --host "http://joomla-ua.org" --scan subdomains
                python ./opendoor.py --host "https://joomla-ua.org" --threads 10
                python ./opendoor.py --host "http://joomla-ua.org" --threads 10 --proxy
                python ./opendoor.py --host "https://joomla-ua.org" --threads 10 --delay 10
                python ./opendoor.py --host "http://joomla-ua.org" --threads 10 --delay 10 --rest 10
                python ./opendoor.py --host "http://joomla-ua.org"  --random-list --threads 10 --delay 10 --rest 10
                python ./opendoor.py --host "https://joomla-ua.org" --threads 10 --delay 10 --rest 10 --debug 1
                python ./opendoor.py --host "http://joomla-ua.org" --threads 10 --delay 10 --rest 10 --debug 1 --log
            """,
        'banner'    :   """
    ############################################################
    #                                                          #
    #   _____  ____  ____  _  _    ____   _____  _____  ____   #
    #  (  _  )(  _ \( ___)( \( )  (  _ \ (  _  )(  _  )(  _ \  #
    #   )(_)(  )___/ )__)  )  (    )(_) ) )(_)(  )(_)(  )   /  #
    #  (_____)(__)  (____)(_)\_)  (____/ (_____)(_____)(_)\_)  #
    #                                                          #
    #  {0}\t\t                       #
    #  {1}\t\t                       #
    #  {2}\t\t\t                       #
    #  {3}\t\t\t                       #
    #  {4}                     #
    ############################################################""",
        'version'   :   """

    {0}: {1} -> {2}
    {3}
    {4}
    ============================================================""",
        'update': """

    {status} {reasons}
    ============================================================"""
    }
