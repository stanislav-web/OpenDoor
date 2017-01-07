# -*- coding: utf-8 -*-

"""Config class"""


class Config:
    """Config class"""

    params = {
        'cvsupdate' : '/usr/bin/git pull origin master',
        'cvslog'    : '/usr/bin/git log --oneline -n 1',
        'cfg'       : 'setup.cfg',
        'examples'  :  """

            Examples:
                python ./opendoor.py  --examples
                python ./opendoor.py  --update
                python ./opendoor.py  --version
                python ./opendoor.py --url "http://joomla-ua.org"
                python ./opendoor.py --url "https://joomla-ua.org" --port 8080
                python ./opendoor.py --url "http://joomla-ua.org" --scan subdomains
                python ./opendoor.py --url "https://joomla-ua.org" --threads 10
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --proxy
                python ./opendoor.py --url "https://joomla-ua.org" --threads 10 --delay 10
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --delay 10 --rest 10
                python ./opendoor.py --url "https://joomla-ua.org" --threads 10 --delay 10 --rest 10 --debug 1
                python ./opendoor.py --url "http://joomla-ua.org" --threads 10 --delay 10 --rest 10 --debug 1 --log
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
