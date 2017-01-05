OWASP Directory Access scanner
====================
.. image:: http://dl2.joxi.net/drive/2016/08/04/0001/0378/90490/90/4b4470c268.jpg
:target: http://dl2.joxi.net/drive/2016/08/04/0001/0378/90490/90/4b4470c268.jpg
    

.. image:: https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master
:target: https://travis-ci.org/stanislav-web/OpenDoor
.. image:: https://badge.fury.io/py/opendoor.svg
:target: https://badge.fury.io/py/opendoor
        
This application scans the site directories and find all possible ways to login, empty directories and entry points.
Scans conducted in the dictionary that is included in this application.
This software is written for informational purposes and is an open source product under the GPL license.

* *Current v2.7.95*

    * Directories - 26590
    * Subdomains - 101000

**Testing of the software on the commercial systems and organizations is prohibited!**

.. image:: http://dl2.joxi.net/drive/2016/12/12/0001/0378/90490/90/29ae6dade2.jpg
:target: http://dl2.joxi.net/drive/2016/12/12/0001/0378/90490/90/29ae6dade2.jpg
    
Requirements
------------
    * Unix, Mac OS
    * Python 2.7.x

Install Dependencies
------------
    sudo pip install -r requirements.txt
    chmod +x opendoor.py

Implements
------------
    * multithreading
    * reporting
    * random user agent
    * random proxy from proxy list
    * subdomains scanner
    * HTTP/HTTPS support
    * detection of redirect and follow
    * exclusion list

Changelog
------------
    * *v1.0.0* - all the basic functionality is available
    * *v1.0.1* - added debug level as param --debug
    * *v1.2.1* - added filesystem logger (param --log)
    * *v1.2.2* - added example of usage (param --examples)
    * *v1.3.2* - added posibility to use random proxy from proxylist (param --proxy)
    * *v1.3.3* - simplify dependency installation
    * *v1.3.4* - added code quality watcher
    * *v1.3.5* - added ReadTimeoutError ProxyError handlers
    * *v1.3.51* - fixed code style, resolve file read errors
    * *v1.3.52* - code docstyle added
    * *v2.3.52* - subdomains scan available! (param --check subdomains). Added databases
    * *v2.3.54* - disabled treads error. Refactored
    * *v2.4.62* - change port is available now! (param --port 8080). Code style fixes
    * *v2.5.62* - added HTTPS support!
    * *v2.6.62* - added 19000 Possible directories!
    * *v2.7.62* - added redirect handler (Beta)
    * *v2.7.72* - added 52 directories , small changes for UI
    * *v2.7.82* - added 683 directories
    * *v2.7.92* - exclusion list added Data/exclusions.dat
    * *v2.7.95* - large files definitions , bad requests detection handler
    * *v2.7.96* - optimize debug levels (0 - 1 - 2 param --debug) , optimize imports

Basic usage
------------
    python ./opendoor.py --url "http://joomla-ua.org"

Help
------------
    usage: opendoor.py [-h] [-u URL] [--port PORT] [--update] [--examples] [-v]
                   [-c CHECK] [-t THREADS] [-d DELAY] [-r REST]
                   [--debug DEBUG] [-p] [-l]

    optional arguments:
      -h, --help            Show this help message and exit
      --port PORT           Custom port (default 80)
      --update              Update from version control
      --examples            Examples of usage
      -v, --version         Get current version
      -c CHECK, --check CHECK
                        Directory scan eg --check=directories or subdomains
                         (directories by default)
      -t THREADS, --threads THREADS
                        Allowed threads
      -d DELAY, --delay DELAY
                        Delay between requests
      -r REST, --rest REST  Request timeout
      --debug DEBUG         Debug level (0 by default)
      -p, --proxy           Use proxy list
      -l, --log             Use filesystem log

    required named arguments:
      -u URL, --url URL     URL or page to scan; -u http://example.com