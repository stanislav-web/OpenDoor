OWASP Directory Access scanner
==================================
![Alt text](http://dl2.joxi.net/drive/2016/08/04/0001/0378/90490/90/4b4470c268.jpg "Hackware")

This application scans the site directories and find all possible ways to login, empty directories and entry points.
Scans conducted in the dictionary that is included in this application.
This software is written for informational purposes and is an open source product under the GPL license.

***Testing of the software on the commercial systems and organizations is prohibited!***

![Alt text](http://dl2.joxi.net/drive/2016/08/04/0001/0378/90490/90/a33fce8024.jpg "Hackware")

##### Requirements
* Python 2.7.x

##### Dependencies
```
sudo pip install linereader urllib3 threadpool coloredlogs termcolor logging verboselogs tabulate
```

##### Implements
* multithreading
* filesystem log
* detect redirects
* random user agent
* verbose mode

##### Changelog
*v1.0.0 This is beta version*
    - all the basic functionality is available

*v1.0.1 This is beta version*
    - add debug level as param --debug

*v1.2.1*
    - add filesystem logger (param --log )

*v1.2.2*
    - add example of usage (param --examples )

##### Basic usage
```
python ./opendoor.py --url "http://joomla-ua.org"
```
##### Help
```
usage: opendoor.py [-h] [-u URL] [--update] [-v] [-c CHECK] [-t THREADS]
                   [-d DELAY] [-r REST] [--debug DEBUG] [-p] [-l]

optional arguments:
  -h, --help            show this help message and exit
  --update              Update from version control
  -v, --version         Get current version
  -c CHECK, --check CHECK
                        Directory scan eg --check=dir or subdomains
                        --check=sub (Not implement yet, dir by default)
  -t THREADS, --threads THREADS
                        Allowed threads
  -d DELAY, --delay DELAY
                        Delay between requests
  -r REST, --rest REST  Request timeout
  --debug DEBUG         Debug level (0 by default)
  -p, --proxy           Use proxy list (Not implement yet)
  -l, --log             Use log

required named arguments:
  -u URL, --url URL     URL or page to scan; -u http://example.com
```