Opendoor OWASP WEB Directory Scanner
====================================

**OpenDoor OWASP** is a console multifunctional website scanner focused on directory and subdomain discovery.

The application helps detect:
- hidden directories and files
- subdomains
- index pages
- restricted access points
- large files and backups
- false-positive success pages with response sniffers

Scanning is performed with built-in dictionaries and external wordlists.  
Anonymity and flexibility are supported through proxy usage, custom headers, and randomized request techniques.

Software is written for informational purposes and distributed as an open source project under the GPL license.

[![Contributors](https://img.shields.io/github/contributors/stanislav-web/Opendoor)](https://github.com/stanislav-web/OpenDoor/graphs/contributors)
[![PyPI version](https://badge.fury.io/py/opendoor.svg)](https://pypi.org/project/opendoor/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%2B-green.svg)](https://www.python.org/)

#### Current release
- **Version:** 5.0.1
- **Directories:** 83012
- **Subdomains:** 255359

#### Implements
- ✅ directories scanner
- ✅ subdomains scanner
- ✅ multithreading control
- ✅ scan reports
- ✅ HTTP(S) custom port support
- ✅ keep-alive requests
- ✅ invalid certificate scanning
- ✅ HTTP(S) / SOCKS proxy support
- ✅ dynamic request headers
- ✅ custom wordlists and prefixes
- ✅ custom proxy lists and ignore lists
- ✅ debug levels (1-3)
- ✅ extension filters
- ✅ custom reports directory
- ✅ configuration wizard
- ✅ response analysis techniques:
    * skip empty pages
    * detect redirects
    * skip 200 OK redirects
    * detect Apache index pages
    * detect large files
    * heuristic detection of invalid pages
    * blank success page filtering
    * certificate-required page detection
- ✅ randomization techniques:
    * random user-agent per request
    * random proxy per request
    * wordlist shuffling
    * wordlist filtering

#### Supported Python
- Python 3.12
- Python 3.13
- Python 3.14

#### Installation highlights
- `pip install opendoor`
- `pipx install opendoor`
- `python -m build` for maintainers and Linux package builders

#### Documentation sections
See the navigation menu for:
- installation and updates
- usage and CLI arguments
- sniffers
- wizard configuration
- testing
- changelog
- contribution

***Testing of the software on live commercial systems and organizations is prohibited!***

![Logo](img/open-door.png)
