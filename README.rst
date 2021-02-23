OWASP WEB Directory Scanner |Twitter|
=====================================

+----------+------------------+------------------+
| Python   | Linux            | OSX              |
+==========+==================+==================+
| 3.9      | |Build Status|   | |Build Status|   |
+----------+------------------+------------------+
| 3.10     | |Build Status|   | |Build Status|   |
+----------+------------------+------------------+

**OpenDoor OWASP** is console multifunctional web sites scanner. This
application find all possible ways to login, index of/ directories, web
shells, restricted access points, subdomains, hidden data and large
backups. The scanning is performed by the built-in dictionary and
external dictionaries as well. Anonymity and speed are provided by means
of using proxy servers. Software is written for informational purposes
and is open source product under the GPL license.

***(Due to the incorrect operation of "SSL" the support for "Python 2.7"
is terminated)*** \* *Current 3.4.481-stable (02.10.2017)* - Directories
- 36994 - Subdomains - 181018

***Testing of the software on the live commercial systems and
organizations is prohibited!***

.. figure:: http://dl3.joxi.net/drive/2017/01/30/0001/0378/90490/90/e309742b5c.jpg
   :alt: OpenDoor OWASP

   Alt text
Implements
^^^^^^^^^^

-  [x] multithreading control
-  [x] scan's reports
-  [x] directories scanner
-  [x] subdomains scanner
-  [x] HTTP(S) (PORT) support
-  [x] Keep-alive long pooling
-  [x] HTTP(S)/SOCKS proxies
-  [x] dynamic request header
-  [x] custom wordlst's prefixes
-  [x] custom wordlists, proxies, ignore lists
-  [x] debug levels (1-3)
-  [x] extensions filter
-  [x] custom reports directory
-  [x] custom config wizard (use random techniques)
-  [x] analyze techniques

   -  detect redirects
   -  detect index of/ Apache
   -  detect large files
   -  heuristic detect invalid web pages
   -  blank success page filter
   -  certif required pages

-  [x] randomization techniques

   -  random user-agent per request
   -  random proxy per request
   -  wordlists shuffling
   -  wordlists filters

Install PIP
^^^^^^^^^^^

::

    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

Local installation and run
^^^^^^^^^^^^^^^^^^^^^^^^^^

::

     git clone https://github.com/stanislav-web/OpenDoor.git
     cd OpenDoor/
     pip3 install -r requirements.txt
     chmod +x opendoor.py

     python3 opendoor.py --host http://www.example.com

Global installation (Preferably for OS distributions)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

     git clone https://github.com/stanislav-web/OpenDoor.git
     cd OpenDoor/
     python3 setup.py build && python3 setup.py install

     opendoor --host http://www.example.com

Updates
^^^^^^^

::

     python3 opendoor.py --update
     opendoor --update

`Changelog <CHANGELOG.md>`__ (last changes)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

v3.4.481-stable (02.10.2017)
----------------------------

::

    -   Fixed bugs with externals wordlists
    -   Added 80018 subdomains

v3.4.47-rc Gained more Power! (05.07.2017)
------------------------------------------

::

    - Added IPs lookup for subdomains scan
    - Added missing HTTP statuses
    - Bugfix: encoding errors (supported cp1251,utf8,utf16) for body analyze
    - Bugfix: allow to use both --random-list & --extension params
    - Directory closing slash has been removed
    - Support Internationalized Domain Names IDNA
    - Removed --indexof (-i) params
    - Add --ignore-extensions -i param to ignore selected extension
    - Added --sniff param to process responses
        - indexof   (detect Apache Index Of/ directories)
        - file      (detect large files)
        - collation (heurisic detect invalid web pages)
        - skipempty (skip empty valid pages)
    - Internal dictionaries has been filtered out. Delete all duplicates
    - Added +990 unique directories (36931)

Help
^^^^

::

    usage: opendoor.py [-h] [--host HOST] [-p PORT] [-m METHOD] [-t THREADS]
                       [-d DELAY] [--timeout TIMEOUT] [-r RETRIES]
                       [--accept-cookies] [--debug DEBUG] [--tor]
                       [--torlist TORLIST] [--proxy PROXY] [-s SCAN] [-w WORDLIST]
                       [--reports REPORTS] [--reports-dir REPORTS_DIR]
                       [--random-agent] [--random-list] [--prefix PREFIX]
                       [-e EXTENSIONS] [-i IGNORE_EXTENSIONS] [--sniff SNIFF]
                       [--update] [--version] [--examples] [--docs]
                       [--wizard [WIZARD]]

    optional arguments:
      -h, --help            show this help message and exit

    required named options:
      --host HOST           Target host (ip); --host http://example.com

    Application tools:
      --update              Update from CVS
      --version             Get current version
      --examples            Examples of usage
      --docs                Read documentation
      --wizard [WIZARD]     Run wizard scanner from your config

    Debug tools:
      --debug DEBUG         Debug level 1 - 3

    Reports tools:
      --reports REPORTS     Scan reports (json,std,txt,html)
      --reports-dir REPORTS_DIR
                            Path to custom reports dir

    Request tools:
      -p PORT, --port PORT  Custom port (Default 80)
      -m METHOD, --method METHOD
                            Request method (use HEAD as default)
      -d DELAY, --delay DELAY
                            Delay between requests threading
      --timeout TIMEOUT     Request timeout (30 sec default)
      -r RETRIES, --retries RETRIES
                            Max retries to reconnect (default 3)
      --accept-cookies      Accept and route cookies from responses
      --tor                 Using built-in proxylist
      --torlist TORLIST     Path to custom proxylist
      --proxy PROXY         Custom permanent proxy server
      --random-agent        Randomize user-agent per request

    Sniff tools:
      --sniff SNIFF         Response sniff plugins
                            (indexof,collation,file,skipempty)

    Stream tools:
      -t THREADS, --threads THREADS
                            Allowed threads

    Wordlist tools:
      -s SCAN, --scan SCAN  Scan type scan=directories or scan=subdomains
      -w WORDLIST, --wordlist WORDLIST
                            Path to custom wordlist
      --random-list         Shuffle scan list
      --prefix PREFIX       Append path prefix to scan host
      -e EXTENSIONS, --extensions EXTENSIONS
                            Force use selected extensions for scan session -e
                            php,json e.g
      -i IGNORE_EXTENSIONS, --ignore-extensions IGNORE_EXTENSIONS
                            Ignore extensions for scan session -i aspx,jsp e.g

Maintainers
^^^^^^^^^^^

-  @stanislav-web https://github.com/stanislav-web (Developer)

Tests
~~~~~

::

    pip install  -r requirements-dev.txt
    coverage run --source=src/ setup.py test

Contributors
~~~~~~~~~~~~

If you like to contribute to the development of the project in that case
pull requests are open for you. Also, you can suggest an ideas and
create a task in my track list

|Issues| |License: GPL v3| |Say Thanks!|

Documentation
~~~~~~~~~~~~~

-  `Opendoor OWASP
   CookBook <https://github.com/stanislav-web/OpenDoor/wiki>`__
-  `Issues <https://github.com/stanislav-web/OpenDoor/issues>`__

.. |Twitter| image:: https://img.shields.io/twitter/url/https/github.com/stanislav-web/OpenDoor.svg?style=social
   :target: https://twitter.com/intent/tweet?text=Wow:&url=https://github.com/stanislav-web/OpenDoor
.. |Build Status| image:: https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master
   :target: https://travis-ci.org/stanislav-web/OpenDoor
.. |Issues| image:: https://badge.waffle.io/stanislav-web/OpenDoor.png?label=Ready
   :target: https://waffle.io/stanislav-web/OpenDoor
.. |License: GPL v3| image:: https://img.shields.io/badge/License-GPL%20v3-blue.svg
   :target: http://www.gnu.org/licenses/gpl-3.0
.. |Say Thanks!| image:: https://img.shields.io/badge/SayThanks.io-%E2%98%BC-1EAEDB.svg
   :target: https://saythanks.io/to/stanislav-web
