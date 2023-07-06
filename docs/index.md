Opendoor OWASP WEB Directory Scanner
=====================================

**OpenDoor OWASP** is console multifunctional website's scanner.
This application finds all possible ways to login, index of/ directories, 
The scanning is performed by the built-in dictionary and external dictionaries as well. Anonymity and speed are provided by means of using proxy servers.
Software is written for informational purposes and is open source product under the GPL license.
Dictionaries are constantly updated, also expanding application functionality.

[![PyPI version](https://badge.fury.io/py/opendoor.svg)](https://badge.fury.io/py/opendoor)

v4.1.0 (06.07.2023) **LATEST UPDATE**

-   Added `--sniff skipsizes=25:60:101:...`: allow skipping redirect to 200O pages which not found
-   Fix `--sniff skipempty`: increase condition value to detect empty content <= 1000 bytes detect as empty page instead of 100 bytes
-   Fix `ResponseError: Unknown response status : 525`: added to define incorrect SSL handshakes
-   Fix `Object of type HTTPHeaderDictItemView is not JSON serializable`: if `--debug` set `3`
-   Fix response encode failed`('Received response with content-encoding: gzip, but failed to decode it.', error('Error -3 while decompressing data: incorrect header check'))`
-   Optimize directories.txt list (sort, removed trash lines)
-   Added `+13` new directories to internal wordlist
-   Optimize internal wordlist directories.txt list (sort, removed trash lines)

#### Implements
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
    * skip pages of the same size
    * skip empty pages
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


***Testing of the software on the commercial systems and organizations is prohibited!***

![Logo](img/open-door.png)