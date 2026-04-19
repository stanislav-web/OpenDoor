OWASP WEB Directory Scanner [![Twitter](https://img.shields.io/twitter/url/https/github.com/stanislav-web/OpenDoor.svg?style=social)](https://twitter.com/intent/tweet?text=Wow:&url=https://github.com/stanislav-web/OpenDoor)
===============================================================================================================================================================================================================================

| Python   | Linux                                                                                                                               | OSX                                                                                                                                 |
|----------|-------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| 3.12     | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) |
| 3.13     | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) |
| 3.14     | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) | ![CircleCI](https://circleci.com/gh/stanislav-web/OpenDoor.svg?style=shield&circle-token=6858e3bc123caac9e31ab8f18f5e9e22a03fdb0f ) |

**OpenDoor OWASP** is console multifunctional website's scanner.
This application finds all possible ways to login, index of/ directories, web shells, restricted access points, subdomains, hidden data and large backups.
The scanning is performed by the built-in dictionary and external dictionaries as well. Anonymity and speed are provided by means of using proxy servers.
Software is written for informational purposes and is open source product under the GPL license.

![Maintainer](https://img.shields.io/badge/maintainer-stanislav_web-blue)
[![Contributors](https://img.shields.io/github/contributors/stanislav-web/Opendoor)](https://github.com/stanislav-web/OpenDoor/graphs/contributors)
[![PyPI version](https://badge.fury.io/py/opendoor.svg)](https://badge.fury.io/py/opendoor)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%2B-green.svg)](https://www.python.org/)

[![Documentation Status](https://readthedocs.org/projects/opendoor/badge/?version=latest)](https://opendoor.readthedocs.io/?badge=latest)
[![Codacy Security Scan](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml)
[![Codespaces Prebuilds](https://github.com/stanislav-web/OpenDoor/actions/workflows/codespaces/create_codespaces_prebuilds/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/codespaces/create_codespaces_prebuilds)
[![Dependency Review](https://github.com/stanislav-web/OpenDoor/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/dependency-review.yml)
[![CodeQL](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql)

[Read The Docs](https://opendoor.readthedocs.io/)

* *Current 5.0.0 (2026)*
    - Directories: 83012
    - Subdomains: 255359

#### [Changelog](CHANGELOG.md) (last changes)
v5.0.0 (2026)
---------------------------
- Added: `pyproject.toml` for modern Python packaging workflow
- Added: source and wheel build support through `python -m build`
- Added: refreshed `MANIFEST.in` for correct source distribution contents
- Changed: Python support baseline updated to `3.12`, `3.13`, `3.14`
- Changed: package build/install flow modernized for current Python ecosystem
- Changed: CLI update/version behavior refreshed for modern environments
- Changed: test suite refreshed for modern Python runtime and standard library mocks
- Changed: development dependencies refreshed to current maintained versions
- Fixed: build issues for source and wheel distribution generation
- Fixed: packaging metadata and install paths for modern setuptools/pip workflows
- Fixed: tests depending on external shell and network behavior
- Planned next: deeper refactoring, additional tests, warnings cleanup and internal code improvements

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
    * skip 200 OK redirects
    * skip empty pages
    * heuristic detect invalid pages
    * blank success page filter
    * certificate required pages
- ✅ randomization techniques:
    * random user-agent per request
    * random proxy per request
    * wordlists shuffling
    * wordlists filters

#### Install PIP
```bash
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip
```

#### Local installation and run
```bash
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor/
python3 -m pip install -r requirements.txt
chmod +x opendoor.py

python3 opendoor.py --host http://www.example.com
```

#### Local development installation
```bash
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor/
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
python -m pip install -e .

opendoor --host http://www.example.com
```

#### Global installation from PyPI
```bash
python3 -m pip install --upgrade opendoor
opendoor --host http://www.example.com
```

#### Global installation with pipx (recommended for end users)
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install opendoor

opendoor --host http://www.example.com
```

#### Installation from source for OS distributions / maintainers
```bash
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor/
python3 -m pip install --upgrade build
python3 -m build
```

Generated artifacts:
```bash
dist/opendoor-5.0.0.tar.gz
dist/opendoor-5.0.0-py3-none-any.whl
```

This flow is preferable for Linux distributions and package maintainers because:
- source package and wheel are generated through the standard Python build backend
- installation can be managed by the distribution package manager
- updates can be delivered together with OS package updates
- no legacy `setup.py install` flow is required

The package is already present in BlackArch Linux, and this build layout is intended to make packaging for other Linux distributions easier as well.

#### Manual installation from built wheel
```bash
python3 -m pip install dist/opendoor-5.0.0-py3-none-any.whl
opendoor --host http://www.example.com
```

#### Updates
```bash
python3 -m pip install --upgrade opendoor
pipx upgrade opendoor
```

If you use a source checkout:
```bash
git pull
python3 -m pip install -e .
```

#### Help
```bash
usage: opendoor.py [-h] [--host HOST] [-p PORT] [-m METHOD] [-t THREADS]
                   [-d DELAY] [--timeout TIMEOUT] [-r RETRIES]
                   [--keep-alive] [--accept-cookies] [--debug DEBUG] [--tor]
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
  --update              Update package information
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
  --keep-alive          Use keep-alive connection
  --accept-cookies      Accept and route cookies from responses
  --tor                 Using built-in proxylist
  --torlist TORLIST     Path to custom proxylist
  --proxy PROXY         Custom permanent proxy server
  --random-agent        Randomize user-agent per request

Sniff tools:
  --sniff SNIFF         Response sniff plugins
                        (indexof,collation,file,skipempty,skipsizes=NUM:NUM...)

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
```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest
```

### Build
```bash
python3 -m pip install -r requirements-dev.txt
python3 -m build
```

### Contributors
If you like to contribute to the development of the project, in that case, pull requests are open for you.
Also, you can suggest an ideas and create a task in my track list.

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0) [![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/stanislav-web)

### Documentation
- [Read The Docs](https://opendoor.readthedocs.io/)
- [Opendoor OWASP CookBook](https://github.com/stanislav-web/OpenDoor/wiki)
- [Issues](https://github.com/stanislav-web/OpenDoor/issues)
- [PyPI package](https://pypi.org/project/opendoor/)
