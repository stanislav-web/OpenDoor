# -*- coding: utf-8 -*-

"""Config class"""


class Config:
    """Config class"""

    params = {
        'cvsupdate' : '/usr/bin/git pull origin master',
        'cvslog'    : '/usr/bin/git log --oneline -n 1',
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
            """
    }
