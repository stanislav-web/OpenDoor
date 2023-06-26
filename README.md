OWASP WEB Directory Scanner [![Twitter](https://img.shields.io/twitter/url/https/github.com/stanislav-web/OpenDoor.svg?style=social)](https://twitter.com/intent/tweet?text=Wow:&url=https://github.com/stanislav-web/OpenDoor)
===============================================================================================================================================================================================================================

| Python   | Linux                                                                                                                               | OSX                                                                                                                                 |
|----------|-------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| 3.7   	  | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) |
| 3.8   	  | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) |
| 3.9   	  | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) |
| 3.10   	 | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) |
| 3.11   	 | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) |

**OpenDoor OWASP** is console multifunctional website's scanner.
This application finds all possible ways to login, index of/ directories, web shells, restricted access points, subdomains, hidden data and large backups.
The scanning is performed by the built-in dictionary and external dictionaries as well. Anonymity and speed are provided by means of using proxy servers.
Software is written for informational purposes and is open source product under the GPL license.

[Read The Docs](https://opendoor.readthedocs.io/)

* *Current 4.0.6 (25.06.2023)*
    - Directories: 82239
    - Subdomains: 181018

***Testing of the software on the live commercial systems and organizations is prohibited!***

![Alt text](http://dl3.joxi.net/drive/2017/01/30/0001/0378/90490/90/e309742b5c.jpg "OpenDoor OWASP")

- ✅ directories scanner
- ✅ subdomains scanner
- ✅ multithreading control
- ✅ scan's reports
- ✅ HTTP(S) (PORT) support
- ✅ Keep-alive long pooling
- ✅ Invalid certificates scan
- ✅ HTTP(S)/SOCKS proxies
- ✅ dynamic request header
- ✅ custom wordlists prefixes
- ✅ custom wordlists, proxies, ignore lists
- ✅ debug levels (1-3)
- ✅ extensions filter
- ✅ custom reports directory
- ✅ custom config wizard (use random techniques)
- ✅ analyze techniques:
    * detect redirects
    * detect index of/ Apache
    * detect large files
    * heuristic detect invalid pages
    * blank success page filter
    * certificate required pages
- ✅ randomization techniques:
    * random user-agent per request
    * random proxy per request
    * wordlists shuffling
    * wordlists filters


#### Install PIP
```
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
```

#### Local installation and run
```
 git clone https://github.com/stanislav-web/OpenDoor.git
 cd OpenDoor/
 pip3 install -r requirements.txt
 chmod +x opendoor.py

 python3 opendoor.py --host http://www.example.com
```

#### Global installation (Preferably for OS distributions)
```
 git clone https://github.com/stanislav-web/OpenDoor.git
 cd OpenDoor/
 python3 setup.py build && python3 setup.py install

 opendoor --host http://www.example.com
```


#### Updates
```
 python3 opendoor.py --update
 opendoor --update
```

#### [Changelog](CHANGELOG.md) (last changes)

v4.0.6 (26.06.2023)
---------------------------
    -   Re-create documentation portal. Keep docs up to date. Publish on Pypi

v4.0.5 (25.06.2023)
---------------------------
    -   Update dictionary: + 45442 new directories

v4.0.4-stable (24.06.2023)
---------------------------
    -   Fix unit tests and resolve dev requirements

v4.0.3 (24.06.2023)
---------------------------
    -   Fix [#ISSUE-44](https://github.com/stanislav-web/OpenDoor/issues/44) ignore invalid SSL by defaul  

v4.0.2 (23.06.2023)
---------------------------
    -   Python 3.11 launch fix [#ISSUE-58](https://github.com/stanislav-web/OpenDoor/issues/58) added encoding to setup.py 

v4.0.1-beta (23.02.2021)
---------------------------
    -   Python 2.6,2.7 is unsupported
    -   Update directories.dat  36994 -> 37019
    -   [enhancement] [#PR-40](https://github.com/stanislav-web/OpenDoor/issues/40) added encoding to setup.py 
    -   [bugfix] [#PR-48](https://github.com/stanislav-web/OpenDoor/issues/48) Python 3.9 / 3.10 compatibility
    -   [bugfix] [#PR-20](https://github.com/stanislav-web/OpenDoor/issues/20) No timeout setup in request
    -   [enhancement] [#PR-36](https://github.com/stanislav-web/OpenDoor/issues/36) Feature Request: Show only found items

v3.4.481-stable (02.10.2017)
---------------------------
    -   Fixed bugs with externals wordlists
    -   Added 80018 subdomains

v3.4.47-rc Gained more Power! (05.07.2017)
---------------------------
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

#### Help
```
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
  --debug DEBUG         Debug level -1 (silent), 1 - 3

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
```

#### Maintainers
- @stanislav-web <https://github.com/stanislav-web> (Developer)

### Tests
```
pip3 install  -r requirements-dev.txt
python setup.py test
```

### Contributors
If  you like to contribute to the development of the project, in that case, pull requests are open for you.
Also, you can suggest an ideas and create a task in my track list

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0) [![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/stanislav-web)  

### Documentation
- [Read The Docs](https://opendoor.readthedocs.io/)
- [Opendoor OWASP CookBook](https://github.com/stanislav-web/OpenDoor/wiki)
- [Issues](https://github.com/stanislav-web/OpenDoor/issues)

