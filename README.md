OWASP Directory Access Scanner
==================================

[![Coverage Status](https://coveralls.io/repos/github/stanislav-web/OpenDoor/badge.svg?branch=master)](https://coveralls.io/github/stanislav-web/OpenDoor?branch=master) [![Code Health](https://landscape.io/github/stanislav-web/OpenDoor/master/landscape.svg?style=flat)](https://landscape.io/github/stanislav-web/OpenDoor/master)
 [![Codacy Badge](https://api.codacy.com/project/badge/Grade/edc54f96aa9748979f59d414daa978c6)](https://www.codacy.com/app/stanisov/OpenDoor?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=stanislav-web/OpenDoor&amp;utm_campaign=Badge_Grade) [![Say Thanks!](https://img.shields.io/badge/SayThanks.io-%E2%98%BC-1EAEDB.svg)](https://saythanks.io/to/stanislav-web)



|  Python | Linux  |  OSX | Windows  |
|:-:|:-:|:-:|:-:|
|2.6|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | ?  |
|2.7|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | ?  |

This application scans the site directories and find all possible ways to login, index of/ dirs and entry points.
The scanning is performed by the dictionary that came with the software. Possiblly to use own dictionaries.
This software is written for informational purposes and is an open source product under the GPL license.


* *Current v3.0.1-beta (31.01.2017)*
    - Directories - 26322
    - Subdomains - 101000

***Testing of the software on the commercial systems and organizations is prohibited!***

![Alt text](http://dl3.joxi.net/drive/2017/01/30/0001/0378/90490/90/e309742b5c.jpg "OpenDoor OWASP")


#### Requirements
* Unix
* Python 2.6.x
* Python 2.7.x

#### Maintainers
- @stanislav-web <https://github.com/stanislav-web> (Developer)

#### Dependencies [![Requirements Status](https://requires.io/github/stanislav-web/OpenDoor/requirements.svg?branch=master)](https://requires.io/github/stanislav-web/OpenDoor/requirements/?branch=master)
* urllib3
* importlib
* json2html
* tabulate

#### Install Dependencies
```
sudo pip install -r requirements.txt
chmod +x opendoor.py
```
Also, you have to install `socksipy` package if you'll use socks as proxy
```
sudo apt-get install python-socksipy
```

#### Implements
- [x] multithreading control
- [x] scan's reports
- [x] directories scanner
- [x] subdomains scanner
- [x] HTTP(S) (PORT) support
- [x] HTTP(S)/SOCKS proxies
- [x] dynamic request header
- [x] detect redirects
- [x] detect index of/ Apache
- [x] detect large files
- [x] custom wordlst's prefixes
- [x] custom wordlists, proxies, ignore lists
- [x] debug levels (1-3)
- [x] randomization techniques
    * random user-agent per request
    * random proxy per request
    * wordlists shuffling


#### [Changelog](CHANGELOG.md) (last changes)

<sub>v3.0.1-beta (31.01.2017)</sub>
-------------------------
    - relieved of unnecessary dependencies
    - fully optimized code inside
    - user-friendly interface
    - multiple reporters (std,txt,json,html)
    - added external wordlists support
    - added external proxylist support
    - added wordlist shuffling
    - wordlst's prefixes
    - added multithreading control
    - dynamic and smart requests (cookies + accept headers)
    - apache index of/ and files detection

#### Basic usage
```
 python opendoor.py --host http://www.example.com
```
#### Help
```
usage: opendoor.py [-h] [--host HOST] [-p PORT] [-m METHOD] [-t THREADS]
                   [-d DELAY] [--timeout TIMEOUT] [-r RETRIES]
                   [--accept-cookies] [--debug DEBUG] [--tor]
                   [--torlist TORLIST] [--proxy PROXY] [-s SCAN] [-w WORDLIST]
                   [--reports REPORTS] [--random-agent] [--random-list]
                   [--prefix PREFIX] [-i] [--update] [--version] [--examples]

optional arguments:
  -h, --help            show this help message and exit

required named options:
  --host HOST           Target host (ip); --host http://example.com

Application tools:
  --update              Update from CVS
  --version             Get current version
  --examples            Examples of usage

Debug tools:
  --debug DEBUG         Debug level 1 - 3

Request tools:
  -p PORT, --port PORT  Custom port (Default 80)
  -m METHOD, --method METHOD
                        HTTP method (use HEAD as default)
  -d DELAY, --delay DELAY
                        Delay between request's threads
  --timeout TIMEOUT     Request timeout (30 sec default)
  -r RETRIES, --retries RETRIES
                        Max retries to reconnect (default 3)
  --accept-cookies      Accept and route cookies from responses
  --tor                 Using proxylist
  --torlist TORLIST     Path to external proxylist
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
                        Path to external wordlist
  --reports REPORTS     Scan reports (json,std,txt)
  --random-list         Shuffle scan list
  --prefix PREFIX       Append path prefix to scan host

```

### Test
```
pip install unittest2 mock
coverage run --source=opendoor setup.py test
```

### Contributors
If  you like to contribute to the development of the project in that case pull requests are open for you.
Also, you can suggest an ideas and create a task in my track list

[![Issues](https://badge.waffle.io/stanislav-web/OpenDoor.png?label=Ready)](https://waffle.io/stanislav-web/OpenDoor) [![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
### Documentation
- [API for contributors ](https://pythonhosted.org/opendoor/)
- [Opendoor OWASP Wiki Pages ](https://github.com/stanislav-web/OpenDoor/wiki)
- [Opendoor OWASP CookBook ](https://github.com/stanislav-web/OpenDoor/wiki)
- [Issues](https://github.com/stanislav-web/OpenDoor/issues)

