OWASP WEB Directory Scanner [![Twitter](https://img.shields.io/twitter/url/https/github.com/stanislav-web/OpenDoor.svg?style=social)](https://twitter.com/intent/tweet?text=Wow:&url=https://github.com/stanislav-web/OpenDoor)
===============================================================================================================================================================================================================================

| Python | Linux | macOS | Windows |
|---|---|---|---|
| 3.12 | [![CI Linux Python 3.12](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py312.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py312.yml) | [![CI macOS Python 3.12](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py312.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py312.yml) | [![CI Windows Python 3.12](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py312.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py312.yml) |
| 3.13 | [![CI Linux Python 3.13](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py313.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py313.yml) | [![CI macOS Python 3.13](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py313.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py313.yml) | [![CI Windows Python 3.13](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py313.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py313.yml) |
| 3.14 | [![CI Linux Python 3.14](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py314.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py314.yml) | [![CI macOS Python 3.14](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py314.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py314.yml) | [![CI Windows Python 3.14](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py314.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py314.yml) |

**OpenDoor OWASP** is console multifunctional website's scanner.  
This application finds all possible ways to login, index of/ directories, web shells, restricted access points, subdomains, hidden data and large backups.  
The scanning is performed by the built-in dictionary and external dictionaries as well. Anonymity and speed are provided by means of using proxy servers.  
Software is written for informational purposes and is open source product under the GPL license.

![Maintainer](https://img.shields.io/badge/maintainer-stanislav_web-blue)
[![Contributors](https://img.shields.io/github/contributors/stanislav-web/Opendoor)](https://github.com/stanislav-web/OpenDoor/graphs/contributors)
[![PyPI version](https://badge.fury.io/py/opendoor.svg)](https://badge.fury.io/py/opendoor)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%2B-green.svg)](https://www.python.org/)

[![Documentation Status](https://app.readthedocs.org/projects/opendoor/badge/?version=latest)](https://opendoor.readthedocs.io/en/latest/)
[![Codacy Security Scan](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml)
[![Dependency Review](https://github.com/stanislav-web/OpenDoor/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/dependency-review.yml)
[![CodeQL](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql)

[Read The Docs](https://opendoor.readthedocs.io/)

* *Current 5.0.1 (19.04.2026)*
    - Directories: 83012
    - Subdomains: 255359

#### [Changelog](CHANGELOG.md) (last changes)
v5.0.1 (19.04.2026)
---------------------------
- Fixed: Read the Docs badge updated to the current badge endpoint
- Removed: stale Codespaces Prebuilds badge that no longer resolves
- Changed: documentation stack refreshed for current Read the Docs / MkDocs workflow
- Changed: `docs/requirements.txt` reduced to the active MkDocs-based documentation stack
- Changed: `.readthedocs.yaml` updated for current RTD configuration
- Changed: documentation pages refreshed for the modern packaging and installation flow
- Fixed: docs build now aligns with the current project packaging and supported Python baseline

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
Use this mode if you want to run OpenDoor directly from the repository without installing it globally.

```bash
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor/
python3 -m pip install -r requirements.txt
chmod +x opendoor.py

python3 opendoor.py --host http://www.example.com
```

#### Local development installation
Use this mode if you are developing, testing, or changing the project locally.

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
Use this if you want the package available as a normal Python CLI tool.

```bash
python3 -m pip install --upgrade opendoor
opendoor --host http://www.example.com
```

#### Global installation with pipx (recommended for end users)

##### macOS / Homebrew
```bash
brew install pipx
pipx ensurepath
pipx install opendoor

opendoor --host http://www.example.com
```

##### Linux / generic environments
Install `pipx` with your system package manager or preferred Python tooling, then:

```bash
pipx ensurepath
pipx install opendoor

opendoor --host http://www.example.com
```

`pipx` is the preferred option when you want an isolated CLI installation without managing a project virtual environment manually.

#### Installation from source for OS distributions / maintainers
This flow is intended for Linux distributions, package maintainers, and release pipelines.

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

##### PyPI installation
```bash
python3 -m pip install --upgrade opendoor
```

##### pipx installation
```bash
pipx upgrade opendoor
```

##### Source checkout
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
  --host HOST           Target host; example: --host http://example.com

Application tools:
  --update              Show package update instructions
  --version             Show current version
  --examples            Show usage examples
  --docs                Open documentation
  --wizard [WIZARD]     Run scanner wizard from your config

Debug tools:
  --debug DEBUG         Debug level -1 (silent), 1 - 3

Reports tools:
  --reports REPORTS     Scan reports (json,std,txt,html)
  --reports-dir REPORTS_DIR
                        Path to custom reports directory

Request tools:
  -p PORT, --port PORT  Custom port (default 80)
  -m METHOD, --method METHOD
                        Request method (HEAD by default)
  -d DELAY, --delay DELAY
                        Delay between threaded requests
  --timeout TIMEOUT     Request timeout (30 sec default)
  -r RETRIES, --retries RETRIES
                        Maximum reconnect retries (default 3)
  --keep-alive          Use keep-alive connection
  --accept-cookies      Accept and route cookies from responses
  --tor                 Use built-in proxy list
  --torlist TORLIST     Path to custom proxy list
  --proxy PROXY         Custom permanent proxy server
  --random-agent        Randomize user-agent per request

Sniff tools:
  --sniff SNIFF         Response sniff plugins
                        (indexof,collation,file,skipempty,skipsizes=NUM:NUM...)

Stream tools:
  -t THREADS, --threads THREADS
                        Allowed threads

Wordlist tools:
  -s SCAN, --scan SCAN  Scan type: directories or subdomains
  -w WORDLIST, --wordlist WORDLIST
                        Path to custom wordlist
  --random-list         Shuffle scan list
  --prefix PREFIX       Append path prefix to scan host
  -e EXTENSIONS, --extensions EXTENSIONS
                        Force selected extensions for scan session, e.g. php,json
  -i IGNORE_EXTENSIONS, --ignore-extensions IGNORE_EXTENSIONS
                        Ignore selected extensions for scan session, e.g. aspx,jsp
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

### Lint
```bash
python3 -m pip install -r requirements-dev.txt
ruff check .
```

### Contributors
If you like to contribute to the development of the project, in that case, pull requests are open for you.  
Also, you can suggest ideas and create a task in my track list.

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0) [![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/stanislav-web)

### Documentation
- [Read The Docs](https://opendoor.readthedocs.io/)
- [Opendoor OWASP CookBook](https://github.com/stanislav-web/OpenDoor/wiki)
- [Issues](https://github.com/stanislav-web/OpenDoor/issues)
- [PyPI package](https://pypi.org/project/opendoor/)
