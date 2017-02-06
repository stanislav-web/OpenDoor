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
  --reports REPORTS     Scan reports (json,std,plain)
  --random-list         Shuffle scan list
  --prefix PREFIX       Append path prefix to scan host

```
