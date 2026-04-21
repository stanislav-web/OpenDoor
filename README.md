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
[![PyPI - Version](https://img.shields.io/pypi/v/opendoor)](https://pypi.org/project/opendoor/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%2B-green.svg)](https://www.python.org/) [![codecov](https://codecov.io/github/stanislav-web/OpenDoor/graph/badge.svg?token=dyBxutYBso)](https://codecov.io/github/stanislav-web/OpenDoor)

[![Documentation Status](https://app.readthedocs.org/projects/opendoor/badge/?version=latest)](https://opendoor.readthedocs.io/en/latest/)
[![Codacy Security Scan](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml)
[![Dependency Review](https://github.com/stanislav-web/OpenDoor/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/dependency-review.yml)
[![CodeQL](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql)

[Read The Docs](https://opendoor.readthedocs.io/)

* *Current 5.7.0 (22.04.2026)*
    - Directories: 110880
    - Subdomains: 255359

#### [Changelog](CHANGELOG.md) (last changes)
v5.7.0 (22.04.2026)
---------------------------
- (feature) Added `--fingerprint` to run heuristic technology fingerprinting before the main scan.
- (feature) Added probable application stack detection for popular CMS, ecommerce platforms, frameworks, site builders, and static-site tooling.
- (feature) Added infrastructure fingerprinting for AWS (CloudFront, S3, ELB/ALB, API Gateway, Amplify), Cloudflare, Vercel, Netlify, GitHub Pages, GitLab Pages, Heroku, Azure, Google Cloud, Fastly, Akamai, and OpenResty.
- (feature) Added fingerprint summary fields to the standard report output, including application category/name/confidence and infrastructure provider/confidence.
- (ux) Fingerprinting now runs after connectivity checks and before the main scan without breaking the existing scan pipeline.
- (tests) Added regression coverage for fingerprint detection rules, runtime browser integration, controller orchestration, and report rendering.
- (tests) Full unittest suite passes after integration (`679` tests).

#### Main features

- ✅ directories scanner
- ✅ recursive directory scanner
- ✅ subdomains scanner
- ✅ target input sources
    * single target via `--host`
    * multi-target file via `--hostlist`
    * standard input via `--stdin`
- ✅ technology fingerprinting
    * heuristic application stack detection via `--fingerprint`
    * identify probable CMS, ecommerce platforms, frameworks, site builders, and static-site tooling
    * detect infrastructure providers such as AWS, Cloudflare, Vercel, Netlify, GitHub Pages, GitLab Pages, Heroku, Azure, Google Cloud, Fastly, Akamai, and OpenResty
    * print application and infrastructure confidence in the standard report
- ✅ session control
    * runtime pause / resume session
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
    * silent mode
    * info
    * raw mode
- ✅ extensions filters
- ✅ custom config wizard (use random techniques)
- ✅ scans reporting
    * console reports
    * JSON reports
    * TXT reports
    * HTML reports
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
- ✅ response filters
    * include/exclude HTTP status codes
    * HTTP status ranges, e.g. `200-299,301,302,403`
    * exclude exact response sizes
    * exclude inclusive response size ranges
    * match or exclude body text fragments
    * match or exclude body regex patterns
    * min/max response length filters
    * automatic `HEAD` -> `GET` override for body-required filters
- ✅ raw-request templates
    * load raw HTTP requests via `--raw-request request.txt`
    * resolve relative request lines with `--scheme http|https`
    * parse method, host, port, headers, cookies, and request body
    * derive prefix automatically from raw request path
    * allow CLI host/header/cookie/method/prefix overrides on top of the template

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

This flow is preferable for Linux distributions and package maintainers because:
- source package and wheel are generated through the standard Python build backend
- installation can be managed by the distribution package manager
- updates can be delivered together with OS package updates
- no legacy `setup.py install` flow is required

The package is already present in BlackArch Linux, and this build layout is intended to make packaging for other Linux distributions easier as well.

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
usage: opendoor.py [-h] [--host HOST | --hostlist HOSTLIST | --stdin]
                   [-p PORT] [-m METHOD] [--scheme SCHEME]
                   [--raw-request RAW_REQUEST] [-t THREADS] [-d DELAY]
                   [--timeout TIMEOUT] [-r RETRIES] [--keep-alive]
                   [--header HEADER] [--cookie COOKIE] [--accept-cookies]
                   [--debug DEBUG] [--tor] [--torlist TORLIST] [--proxy PROXY]
                   [-s SCAN] [-w WORDLIST] [--reports REPORTS]
                   [--reports-dir REPORTS_DIR] [--random-agent]
                   [--random-list] [--prefix PREFIX] [-e EXTENSIONS]
                   [-i IGNORE_EXTENSIONS] [--recursive]
                   [--recursive-depth RECURSIVE_DEPTH]
                   [--recursive-status RECURSIVE_STATUS]
                   [--recursive-exclude RECURSIVE_EXCLUDE] [--sniff SNIFF]
                   [--include-status INCLUDE_STATUS]
                   [--exclude-status EXCLUDE_STATUS]
                   [--exclude-size EXCLUDE_SIZE]
                   [--exclude-size-range EXCLUDE_SIZE_RANGE]
                   [--match-text MATCH_TEXT] [--exclude-text EXCLUDE_TEXT]
                   [--match-regex MATCH_REGEX] [--exclude-regex EXCLUDE_REGEX]
                   [--min-response-length MIN_RESPONSE_LENGTH]
                   [--max-response-length MAX_RESPONSE_LENGTH] [--update]
                   [--version] [--examples] [--docs] [--wizard [WIZARD]]

options:
  -h, --help            show this help message and exit

required named options:
  --host HOST           Target host; example: --host http://example.com
  --hostlist HOSTLIST   Path to file with targets, one per line
  --stdin               Read targets from STDIN, one per line

Application tools:
  --update              Show package update instructions
  --version             Show current version
  --examples            Show usage examples
  --docs                Open documentation
  --wizard [WIZARD]     Run scanner wizard from your config

Debug tools:
  --debug DEBUG         Debug level -1 (silent), 1 - 3

Response filters:
  --include-status INCLUDE_STATUS
                        Include only response codes, e.g. 200-299,301,302,403
  --exclude-status EXCLUDE_STATUS
                        Exclude response codes, e.g. 404,429,500-599
  --exclude-size EXCLUDE_SIZE
                        Exclude exact response sizes in bytes, e.g. 0,1234
  --exclude-size-range EXCLUDE_SIZE_RANGE
                        Exclude response size ranges in bytes, e.g.
                        0-256,1024-2048
  --match-text MATCH_TEXT
                        Keep only responses whose body contains the given
                        text. Repeatable
  --exclude-text EXCLUDE_TEXT
                        Exclude responses whose body contains the given text.
                        Repeatable
  --match-regex MATCH_REGEX
                        Keep only responses whose body matches the given
                        regex. Repeatable
  --exclude-regex EXCLUDE_REGEX
                        Exclude responses whose body matches the given regex.
                        Repeatable
  --min-response-length MIN_RESPONSE_LENGTH
                        Keep only responses whose size is at least N bytes
  --max-response-length MAX_RESPONSE_LENGTH
                        Keep only responses whose size is at most N bytes

Reports tools:
  --reports REPORTS     Scan reports (json,std,txt,html)
  --reports-dir REPORTS_DIR
                        Path to custom reports directory

Request tools:
  -p, --port PORT       Custom port (default 80)
  -m, --method METHOD   Request method (HEAD by default)
  -d, --delay DELAY     Delay between threaded requests
  --timeout TIMEOUT     Request timeout (30 sec default)
  -r, --retries RETRIES
                        Maximum reconnect retries (default 3)
  --keep-alive          Use keep-alive connection
  --header HEADER       Add custom request header, e.g. --header 'X-Test: 1'
  --cookie COOKIE       Add custom cookie, e.g. --cookie 'sid=abc123'
  --accept-cookies      Accept and route cookies from responses
  --fingerprint         Detect probable CMS, framework, or custom stack before the scan
  --tor                 Use built-in proxy list
  --torlist TORLIST     Path to custom proxy list
  --proxy PROXY         Custom permanent proxy server
  --random-agent        Randomize user-agent per request

Sniff tools:
  --sniff SNIFF         Response sniff plugins (indexof,collation,file,skipemp
                        ty,skipsizes=NUM:NUM...)

Stream tools:
  -t, --threads THREADS
                        Allowed threads

Wordlist tools:
  -s, --scan SCAN       Scan type: directories or subdomains
  -w, --wordlist WORDLIST
                        Path to custom wordlist
  --random-list         Shuffle scan list
  --prefix PREFIX       Append path prefix to scan host
  -e, --extensions EXTENSIONS
                        Force selected extensions for the scan session, e.g.
                        php,json
  -i, --ignore-extensions IGNORE_EXTENSIONS
                        Ignore selected extensions for the scan session, e.g.
                        aspx,jsp
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
