OWASP WEB Directory Scanner [![Twitter](https://img.shields.io/twitter/url/https/github.com/stanislav-web/OpenDoor.svg?style=social)](https://twitter.com/intent/tweet?text=Wow:&url=https://github.com/stanislav-web/OpenDoor)
===============================================================================================================================================================================================================================

![OpenDoor OWASP](https://raw.githubusercontent.com/stanislav-web/OpenDoor/master/logo.png)

| Python | Linux | macOS | Windows |
|---|---|---|---|
| 3.12 | [![CI Linux Python 3.12](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py312.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py312.yml) | [![CI macOS Python 3.12](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py312.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py312.yml) | [![CI Windows Python 3.12](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py312.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py312.yml) |
| 3.13 | [![CI Linux Python 3.13](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py313.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py313.yml) | [![CI macOS Python 3.13](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py313.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py313.yml) | [![CI Windows Python 3.13](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py313.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py313.yml) |
| 3.14 | [![CI Linux Python 3.14](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py314.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py314.yml) | [![CI macOS Python 3.14](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py314.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py314.yml) | [![CI Windows Python 3.14](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py314.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py314.yml) |

**OpenDoor OWASP** is a multifunctional console website scanner.  
This application finds possible login entry points, `Index of/` directories, web shells, restricted access points, subdomains, hidden data, and large backup files.  
Scanning is performed using both the built-in dictionary and external dictionaries.  
Anonymity and speed are provided through the use of proxy servers.  
The software is written for informational purposes and is released as an open-source product under the GPL license.  
The project is part of [BlackArch Linux](https://blackarch.org/webapp.html) and is maintained and supported by the community.

![Maintainer](https://img.shields.io/badge/maintainer-stanislav_web-blue)
[![Contributors](https://img.shields.io/github/contributors/stanislav-web/Opendoor)](https://github.com/stanislav-web/OpenDoor/graphs/contributors)
[![PyPI version](https://badge.fury.io/py/opendoor.svg)](https://badge.fury.io/py/opendoor)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%2B-green.svg)](https://www.python.org/) [![codecov](https://codecov.io/github/stanislav-web/OpenDoor/graph/badge.svg?token=dyBxutYBso)](https://codecov.io/github/stanislav-web/OpenDoor)

[![Documentation Status](https://app.readthedocs.org/projects/opendoor/badge/?version=latest)](https://opendoor.readthedocs.io/en/latest/)
[![Codacy Security Scan](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml)
[![Dependency Review](https://github.com/stanislav-web/OpenDoor/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/dependency-review.yml)
[![CodeQL](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql)

[Read The Docs](https://opendoor.readthedocs.io/)

* *Current 5.3.0 (21.04.2026)*
    - Directories: 110977
    - Subdomains: 255359

#### [Changelog](CHANGELOG.md) (last changes)
v5.3.0 (21.04.2026)
---------------------------
- (feature) Added custom request headers via `--header`.
- (feature) Added custom request cookies via `--cookie`.
- (feature) Request providers now apply multiple custom headers and cookies from CLI/config.
- (docs) Updated `README.md` and `docs/Usage.md` with `--header` and `--cookie` examples and refreshed CLI help output.
- (tests) Test suite expanded to 553 tests with request provider coverage for custom headers and cookies.

#### Main features

- ✅ directories scanner
- ✅ recursive directory scanner
- ✅ subdomains scanner
- ✅ multithreading control
- ✅ HTTP(S) (PORT) support
- ✅ Keep-alive long pooling
- ✅ Invalid certificates scan
- ✅ HTTP(S)/SOCKS proxies
- ✅ dynamic request headers
    * custom request headers support
    * custom request cookies support
    * cookie routing from responses
    * custom or randomized user-agent support
- ✅ custom wordlists prefixes
- ✅ custom wordlists, proxies, ignore lists
- ✅ debug levels (1-3)
- ✅ extensions filters
- ✅ custom config wizard (use random techniques)
- ✅ scans reporting
    * console reports
    * json reports
    * txt reports
    * html reports
- ✅ analyze techniques:
    * detect redirects
    * detect index of/ Apache
    * detect large files
    * skip 200 OK redirects
    * skip empty pages
    * cookie routing (reusing cookies)
    * heuristic detect invalid pages (false 404)
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

#### Global installation from PyPI
Use this if you want the package available as a normal Python CLI tool.

##### Linux / macOS
```bash
python3 -m pip install --upgrade opendoor
opendoor --host http://www.example.com
```

##### Windows (PowerShell)
```powershell
winget install Python.Python.3.14
py -m pip install --upgrade pip
py -m pip install --upgrade opendoor

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

##### Windows (PowerShell)
```powershell
winget install Python.Python.3.14
py -m pip install --user pipx
py -m pipx ensurepath

# Reopen PowerShell after ensurepath
pipx install opendoor

opendoor --host http://www.example.com
```

`pipx` is the preferred option when you want an isolated CLI installation without managing a project virtual environment manually.

#### Local installation and run
Use this mode if you want to run OpenDoor directly from the repository without installing it globally.

##### Linux / macOS
```bash
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor/
python3 -m pip install -r requirements.txt
chmod +x opendoor.py

python3 opendoor.py --host http://www.example.com
```

##### Windows (PowerShell)
```powershell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor
py -m pip install -r requirements.txt

py opendoor.py --host http://www.example.com
```

#### Local development installation
Use this mode if you are developing, testing, or changing the project locally.

##### Linux / macOS
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

##### Windows (PowerShell)
```powershell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
python -m pip install -e .

opendoor --host http://www.example.com
```

#### Installation from source for OS distributions / maintainers
This flow is intended for Linux distributions, package maintainers, and release pipelines.

##### Linux / macOS
```bash
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor/
python3 -m pip install --upgrade build
python3 -m build
```

##### Windows (PowerShell)
```powershell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor
py -m pip install --upgrade build
py -m build
```

Generated artifacts:
```bash
dist/opendoor-5.3.0.tar.gz
dist/opendoor-5.3.0-py3-none-any.whl
```

This flow is preferable for Linux distributions and package maintainers because:
- source package and wheel are generated through the standard Python build backend
- installation can be managed by the distribution package manager
- updates can be delivered together with OS package updates
- no legacy `setup.py install` flow is required

The package is already present in BlackArch Linux, and this build layout is intended to make packaging for other Linux distributions easier as well.

#### Manual installation from built wheel

##### Linux / macOS
```bash
python3 -m pip install dist/opendoor-5.3.0-py3-none-any.whl
opendoor --host http://www.example.com
```

##### Windows (PowerShell)
```powershell
py -m pip install dist/opendoor-5.3.0-py3-none-any.whl
opendoor --host http://www.example.com
```

#### Updates

##### PyPI installation

Linux / macOS:
```bash
python3 -m pip install --upgrade opendoor
```

Windows:
```powershell
py -m pip install --upgrade opendoor
```

##### pipx installation
```bash
pipx upgrade opendoor
```

##### Source checkout

Linux / macOS:
```bash
git pull
python3 -m pip install -e .
```

Windows:
```powershell
git pull
py -m pip install -e .
```

#### Help
```bash
usage: opendoor [-h] [--host HOST] [-p PORT] [-m METHOD] [-t THREADS]
                [-d DELAY] [--timeout TIMEOUT] [-r RETRIES]
                [--keep-alive] [--accept-cookies] [--header HEADER]
                [--cookie COOKIE] [--debug DEBUG] [--tor]
                [--torlist TORLIST] [--proxy PROXY] [-s SCAN] [-w WORDLIST]
                [--reports REPORTS] [--reports-dir REPORTS_DIR]
                [--random-agent] [--random-list] [--prefix PREFIX]
                [-e EXTENSIONS] [-i IGNORE_EXTENSIONS] [--recursive]
                [--recursive-depth RECURSIVE_DEPTH]
                [--recursive-status RECURSIVE_STATUS]
                [--recursive-exclude RECURSIVE_EXCLUDE] [--sniff SNIFF]
                [--update] [--version] [--examples] [--docs]
                [--wizard [WIZARD]]

options:
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
  --header HEADER       Add custom request header, e.g. --header 'X-Test: 1'
  --cookie COOKIE       Add custom cookie, e.g. --cookie 'sid=abc123'
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
                        Ignore selected extensions for the scan session, e.g. aspx,jsp
  --recursive           Enable recursive directory scan
  --recursive-depth RECURSIVE_DEPTH
                        Maximum recursive scan depth
  --recursive-status RECURSIVE_STATUS
                        HTTP status codes allowed for recursive expansion
  --recursive-exclude RECURSIVE_EXCLUDE
                        File extensions excluded from recursive expansion
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

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/stanislav-web/OpenDoor) [![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)

### Documentation
- [Read The Docs](https://opendoor.readthedocs.io/)
- [Opendoor OWASP CookBook](https://github.com/stanislav-web/OpenDoor/wiki)
- [Issues](https://github.com/stanislav-web/OpenDoor/issues)
- [PyPI package](https://pypi.org/project/opendoor/)
