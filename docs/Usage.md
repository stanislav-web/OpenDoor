[Basic usage](https://github.com/stanislav-web/OpenDoor/wiki/Usage#basic-usage)
===============
```
python3 opendoor.py --host http://www.example.com
```
![Usage](images/usage.jpg)

[Help](https://github.com/stanislav-web/OpenDoor/wiki/Usage#help)
===============
```
usage: opendoor.py [-h] [--host HOST] [-p PORT] [-m METHOD] [-t THREADS]
                   [-d DELAY] [--timeout TIMEOUT] [-r RETRIES]
                   [--accept-cookies] [--debug DEBUG] [--tor]
                   [--torlist TORLIST] [--proxy PROXY] [-s SCAN] [-w WORDLIST]
                   [--reports REPORTS] [--reports-dir REPORTS_DIR]
                   [--random-agent] [-a] [--random-list] [--prefix PREFIX]
                   [-e EXTENSIONS] [--sniff SNIFF] [--update] [--version]
                   [--examples] [--docs] [--wizard [WIZARD]]

optional arguments:
  -h, --help            show this help message and exit

required named options:
  --host HOST           Target host (ip); --host http://example.com

Application tools:
  --update              Update from CVS
  --version             Get current version
  --examples            Examples of usage
  --docs                Read documentation
  --wizard [WIZARD]     Run wizard scanner from your config

Debug tools:
  --debug DEBUG         Debug level 1 - 3

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
  --accept-cookies      Accept and route cookies from responses
  --tor                 Using built-in proxylist
  --torlist TORLIST     Path to custom proxylist
  --proxy PROXY         Custom permanent proxy server
  --random-agent        Randomize user-agent per request

Sniff tools:
  --sniff SNIFF         Response sniff plugins (indexof,collation,file,skipempty)

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

[Arguments description](https://github.com/stanislav-web/OpenDoor/wiki/Usage#arguments-description-usage)
===============

Application tools
---------------------------

**--update** - update sources from CVS to latest

```python
opendoor --update
```

**--version** - see current package version and compare with server's latest

```python
opendoor --version
```

**--examples** - get some examples of usage

```python
opendoor --examples
```

**--docs** - open this documentation

```python
opendoor --docs
```

**--wizard** - allows you configure own project config. `opendoor.conf` use by default

```python
opendoor --wizard # use opendoor.conf
opendoor --wizard /usr/local/path_to_own_project_conf.conf
```

Required arguments
---------------------------

**--host** - target host (ip). Also might be required protocol. See examples

```python
opendoor --host www.example.com
opendoor --host https://www.example.com
opendoor --host 127.0.0.1
```

Request tools
---------------------------

**--port -p** - custom port. Default 80 for HTTP and 443 for HTTPS

```python
opendoor --host www.example.com # use default 80 port
opendoor --host https://www.example.com # use default 443 port
opendoor --host https://www.example.com --port 444 # use custom port
opendoor --host http://www.example.com --p 8080 # use custom port
```

**--method -m** - scan request method. Use HEAD as default for more faster requests but also you can apply any of the possible methods

```python
opendoor --host https://www.example.com # use default HEAD request method
opendoor --host https://www.example.com -m GET
opendoor --host https://www.example.com --method TRACE
```

**--delay -d** - delay between requests threading. Use to bypass the restrictions of requests per second for the target server

```python
opendoor --host https://www.example.com --delay 3 # 3 sec between requests
opendoor --host https://www.example.com -d 0.3 # 300 ms between requests
```

**--timeout** - request timeout (30 sec default). Maximum sec time for a response

```python
opendoor --host https://www.example.com --timeout 10
```

**--retries -r** - max retries to reconnect (default 3)

```python
opendoor --host https://www.example.com --retries 10
opendoor --host https://www.example.com --r 1
```

**--accept-cookies** - accept and route cookies from responses. To be as natural as possible and bring the scanner closer to the user's browser use cookies receipt. After the first request, your session will accept and  send cookies inside current pool requests

```python
opendoor --host https://www.example.com --accept-cookies

```
**--tor** - using built-in proxy list. You can use proxy lists built into the package to ensure your scanning anonymity

```python
opendoor --host https://www.example.com --tor

```
**--torlist** - path to custom proxylist. Choise your own checked proxy list. The list must have format: ***scheme:ip:port***

```python
opendoor --host https://www.example.com --torlist /home/user/scan/proxy.txt
```

**---proxy** - custom permanent proxy server. Use your own froxy for all requests: ***scheme:ip:port***

```python
opendoor --host https://www.example.com --proxy socks5://127.0.0.1:8888
```

**--random-agent** - randomize your user-agent per request. With each new request, your browser will change. This is both good and bad, because, frequent requests from several browsers can reveal the suspicion of the attack, and at the same time fall in confuse the DevOps, if you would use different proxy servers

```python
opendoor --host https://www.example.com --random-agent
```

Debug tools
---------------------------

**--debug** - debug levels (1-3). Provides the ability to view detailed scanning progress
     - 1 step by step scan proccess
     - 2 + request data view
     - 3 + response data view

```python
opendoor --host www.example.com --debug 1
```

Sniff tools
---------------------------

**--sniff** - Uses for server responses. More detail ([More detail](Sniffers.md))

```python
opendoor --host www.example.com --sniff indexof,collation,file,skipempty
```

Stream tools
---------------------------

**--threads -t** - allowed threads. In order not to harm your computer there is a limit of 25 threads

```python
opendoor --host www.example.com --threads 10
opendoor --host www.example.com --t 15
```

**CTRL+C** - pause scan
**ENTER** - resume scan

Wordlist tools
---------------------------

**--scan -s** - the application allows you to scan in two directions. Not only for directories but also allows you to find subdomains

```python
opendoor --host example.com -scan directories # use as default
opendoor --host example.com -s subdomains
```

**--wordlist -w** - if you don't  satisfied with the built-in list of directories or subdomains, you can assign your own

```python
opendoor --host example.com --wordlist /home/user/scan/mydirlist.dat
opendoor --host example.com --w /home/user/scan/mydirlist.dat
opendoor --host example.com --scan subdomains --wordlist /home/user/scan/mysubdomainslist.txt
```

**--random-list** - shuffle scan list. This technique will allow you to use a mixed list of built-in or external dictionaries instead of the AB list order

```python
opendoor --host example.com --random-list
opendoor --host example.com --wordlist /home/user/scan/mydirlist.dat --random-list

```

**--prefix** - append path prefix to scan host. Works for directories scan type

```python
opendoor --host example.com --prefix en/
opendoor --host example.com --scan directories --prefix en/
```

**--extensions -e** - extensions filter -e php,json e.g. If you know something more about the target host, you can apply a filter to the dictionary with extensions

```python
opendoor --host example.com --extensions php,html
opendoor --host example.com --e htm,py
```

Reports tools
---------------------------

**--reports** - scan reporting format. At the moment there has several providers for reports. Also you can help develop by expanding this functionality

```python
opendoor --host www.example.com # use default "std" report
opendoor --host www.example.com --reports json,html,txt
```

**--reports-dir** - path to custom reports dir. By default, scan reports are located in the "reports/" directory within the package. But you can set the path as you wish

```python
opendoor --host www.example.com --reports json,html,txt --reports-dir /home/usr/User/scans/reports
```