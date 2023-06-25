Opendoor OWASP WEB Directory Scanner
=====================================

**OpenDoor OWASP** is console multifunctional website's scanner.
This application finds all possible ways to login, index of/ directories, 
The scanning is performed by the built-in dictionary and external dictionaries as well. Anonymity and speed are provided by means of using proxy servers.
Software is written for informational purposes and is open source product under the GPL license.
Dictionaries are constantly updated, also expanding application functionality.


#### Implements
- [x] multithreading control
- [x] scan's reports
- [x] directories scanner
- [x] subdomains scanner
- [x] HTTP(S) (PORT) support
- [x] Keep-alive long pooling
- [x] HTTP(S)/SOCKS proxies
- [x] dynamic request header
- [x] custom wordlists prefixes
- [x] custom wordlists, proxies, ignore lists
- [x] debug levels (1-3)
- [x] extensions filter
- [x] custom reports directory
- [x] custom config wizard (use random techniques)
- [x] analyze techniques
    * detect redirects
    * detect index of/ Apache
    * detect large files
    * heuristic detect invalid pages
    * blank success page filter
    * certificate required pages
- [x] randomization techniques
    * random user-agent per request
    * random proxy per request
    * wordlists shuffling
    * wordlists filters


***Testing of the software on the commercial systems and organizations is prohibited!***

![Logo](images/open-door.png)