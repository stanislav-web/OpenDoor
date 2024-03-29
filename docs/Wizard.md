Wizard
======
The Wizard allows you to select individual settings for each target.
See example:

Configure
---------------------------
`opendoor.conf`

```ini
[general]

# Use ssl <bool>
ssl    = False

# Target scheme <string>
scheme = http://

# Target host (ip) <string>
host    = example.com

# Custom port (Default 80) <int>
port    = 80

# HTTP method (use HEAD as default) <string>
method = HEAD

# Delay between request's threads <int>
delay = 0

# Request timeout (30 sec default) <int>
timeout = 60

# Max retries to reconnect (default 3) <int>
retries = 10

# Using built-in proxylist <boolean>
tor = False

# Path to custom proxylist <string|None>
torlist = None

# Custom permanent proxy server <string|None>
proxy = None

# Randomize user-agent per request <boolean>
random-agent = False

# Debug level 1 - 3 <int>
debug = 0

# Allowed threads <int>
threads = 1

# Response sniff plugins (indexof,collation,file,skipempty) <string>
sniff = None

# Scan type scan=directories or scan=subdomains <string>
scan = directories

# Path to custom wordlist <string|None>
wordlist = None

# Shuffle scan list <boolean>
random-list = False

# Append path prefix to scan host <string|None>
prefix = None

# Force use selected extensions for scan session -e php,json e.g <string|None>
extensions = None

#  Force ignore extensions for scan session -i aspx,jsp e.g <string|None>
ignore_extensions = None

# Scan reports (json,std,txt,html) <string>
reports = std

# Path to custom reports dir <string|None>
reports-dir = None
```

Usage
-----
```shell
opendoor --wizard # get default config from opendoor.conf
opendoor --wizard /usr/local/projects/mytarget.com.conf
```