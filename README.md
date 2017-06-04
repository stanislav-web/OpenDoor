OWASP WEB Directory Scanner [![Twitter](https://img.shields.io/twitter/url/https/github.com/stanislav-web/OpenDoor.svg?style=social)](https://twitter.com/intent/tweet?text=Wow:&url=https://github.com/stanislav-web/OpenDoor)
===============================================================================================================================================================================================================================

[![Coverage Status](https://coveralls.io/repos/github/stanislav-web/OpenDoor/badge.svg?branch=master)](https://coveralls.io/github/stanislav-web/OpenDoor?branch=master) [![Code Health](https://landscape.io/github/stanislav-web/OpenDoor/master/landscape.svg?style=flat)](https://landscape.io/github/stanislav-web/OpenDoor/master)
 [![Codacy Badge](https://api.codacy.com/project/badge/Grade/edc54f96aa9748979f59d414daa978c6)](https://www.codacy.com/app/stanisov/OpenDoor?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=stanislav-web/OpenDoor&amp;utm_campaign=Badge_Grade)


|  Python | Linux  |  OSX | Windows  |
|:-:|:-:|:-:|:-:|
|3.2|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | [![Build status](https://ci.appveyor.com/api/projects/status/3hmrb64ofdssi4qd?svg=true)](https://ci.appveyor.com/project/stanislav-web/opendoor)|
|3.3|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | [![Build status](https://ci.appveyor.com/api/projects/status/3hmrb64ofdssi4qd?svg=true)](https://ci.appveyor.com/project/stanislav-web/opendoor)|
|3.4|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | [![Build status](https://ci.appveyor.com/api/projects/status/3hmrb64ofdssi4qd?svg=true)](https://ci.appveyor.com/project/stanislav-web/opendoor)|
|3.5|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | [![Build status](https://ci.appveyor.com/api/projects/status/3hmrb64ofdssi4qd?svg=true)](https://ci.appveyor.com/project/stanislav-web/opendoor)|
|3.6|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | [![Build status](https://ci.appveyor.com/api/projects/status/3hmrb64ofdssi4qd?svg=true)](https://ci.appveyor.com/project/stanislav-web/opendoor)|

**OpenDoor OWASP** is console multifunctional web sites scanner.
This application find all possible ways to login, index of/ directories, restricted access points, subdomains, hidden data and large backups.
The scanning is performed by the built-in dictionary and external dictionaries as well. Anonymity and speed are provided by means of using proxy servers.
Software is written for informational purposes and is open source product under the GPL license.
    
* *Current v3.2.36-rc (04.06.2017)*
    - Directories - 35888
    - Subdomains - 101000

***Testing of the software on the live commercial systems and organizations is prohibited!***

![Alt text](http://dl3.joxi.net/drive/2017/01/30/0001/0378/90490/90/e309742b5c.jpg "OpenDoor OWASP")

#### Implements
- [x] multithreading control
- [x] scan's reports
- [x] directories scanner
- [x] subdomains scanner
- [x] HTTP(S) (PORT) support
- [x] Keep-alive long pooling
- [x] HTTP(S)/SOCKS proxies
- [x] dynamic request header
- [x] custom wordlst's prefixes
- [x] custom wordlists, proxies, ignore lists
- [x] debug levels (1-3)
- [x] extensions filter
- [x] custom reports directory
- [x] analyze techniques
    * detect redirects
    * detect index of/ Apache
    * detect large files
    * certif required pages
- [x] randomization techniques
    * random user-agent per request
    * random proxy per request
    * wordlists shuffling


#### Local installation and run
```
 git clone https://github.com/stanislav-web/OpenDoor.git
 cd OpenDoor/
 pip install -r requirements.txt
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

v3.2.36-rc (04.06.2017)
-----------------------
    - Added custom reports directory --reports-dir /home/user/Reports
    - Added user guide --docs
    - Reusable proxy requests pooling in --tor, --torlist
    - Prevent socks5 proxies warnings
    - Optimizing scan execution
    - Request's delays allow to use of milliseconds
    - Python2.7 no longer support

#### Help
```
usage: opendoor.py [-h] [--host HOST] [-p PORT] [-m METHOD] [-t THREADS]
                   [-d DELAY] [--timeout TIMEOUT] [-r RETRIES]
                   [--accept-cookies] [--debug DEBUG] [--tor]
                   [--torlist TORLIST] [--proxy PROXY] [-s SCAN] [-w WORDLIST]
                   [--reports REPORTS] [--reports-dir REPORTS_DIR]
                   [--random-agent] [--random-list] [--prefix PREFIX]
                   [-e EXTENSIONS] [-i] [--update] [--version] [--examples]
                   [--docs]

optional arguments:
  -h, --help            show this help message and exit

required named options:
  --host HOST           Target host (ip); --host http://example.com

Application tools:
  --update              Update from CVS
  --version             Get current version
  --examples            Examples of usage
  --docs                Read documentation

Debug tools:
  --debug DEBUG         Debug level 1 - 3

Reports tools:
  --reports REPORTS     Scan reports (json,std,txt)
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
  -i, --indexof         Detect Apache Index of/

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
                        Extensions filter -e php,json e.g
```

#### Maintainers
- @stanislav-web <https://github.com/stanislav-web> (Developer)

### Tests
```
pip install  -r requirements-dev.txt
coverage run --source=src/ setup.py test
```

### Contributors
If  you like to contribute to the development of the project in that case pull requests are open for you.
Also, you can suggest an ideas and create a task in my track list

[![Issues](https://badge.waffle.io/stanislav-web/OpenDoor.png?label=Ready)](https://waffle.io/stanislav-web/OpenDoor) [![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)  [![Say Thanks!](https://img.shields.io/badge/SayThanks.io-%E2%98%BC-1EAEDB.svg)](https://saythanks.io/to/stanislav-web)

### Documentation
- [Opendoor OWASP CookBook ](https://github.com/stanislav-web/OpenDoor/wiki)
- [Issues](https://github.com/stanislav-web/OpenDoor/issues)

