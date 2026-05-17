# ⚙️ Wizard

The OpenDoor wizard runs a scan from a configuration file.

It is useful when you want repeatable scan profiles, shared team presets, CI-friendly configuration, or target-specific settings without passing many CLI flags every time.

---

## 🚀 Run the wizard

Use the default configuration file:

```shell
opendoor --wizard
```

By default, OpenDoor reads:

```text
opendoor.conf
```

Use a custom configuration file:

```shell
opendoor --wizard ./configs/example.com.conf
```

This is useful when you maintain different profiles for different environments, targets, or scan strategies.

---

## 🧭 When to use the wizard

Use `--wizard` when you want to:

- keep scan configuration in a file;
- reuse the same options across multiple runs;
- create low-noise profiles for specific targets;
- keep CI/CD commands shorter;
- separate scan behavior from shell scripts;
- maintain team-approved scan presets.

For one-off scans, direct CLI flags are usually faster:

```shell
opendoor --host https://example.com --auto-calibrate --reports json,html
```

For repeatable scans, prefer a config file:

```shell
opendoor --wizard ./configs/example.com.conf
```

---

## 🧾 Minimal configuration

A minimal directory scan configuration:

```ini
[general]

host = example.com
scheme = https://
port = 443

scan = directories
method = HEAD
threads = 10
reports = std,json
```

Run it:

```shell
opendoor --wizard ./configs/example.com.conf
```

---

## 🎯 Target settings

Target-related options define what OpenDoor scans.

```ini
[general]

host = example.com
scheme = https://
port = 443
scan = directories
```

`scheme` is the source of truth for HTTP vs HTTPS. OpenDoor derives the internal SSL mode from it, so modern configs do not need a separate `ssl` key.

Common scan modes:

```ini
scan = directories
```

```ini
scan = subdomains
```

Use `directories` for web path discovery and `subdomains` for domain enumeration.

---

## 🌐 Request settings

Request settings control how OpenDoor talks to the target.

```ini
[general]

method = HEAD
delay = 0
timeout = 30
retries = 3
threads = 10
keep_alive = None
accept_cookies = None
```

Notes:

- `HEAD` is faster for status/size-oriented discovery.
- `GET` is better when body-based filters or body-oriented sniffers are required.
- `timeout` and `retries` should be increased for slow or unstable targets.
- `delay` can be used to reduce request pressure.
- `threads` controls concurrency (1 ~ 50).

For body-based analysis:

```ini
method = GET
```

---

## 🧬 Fingerprinting

Enable fingerprint detection before scanning:

```ini
fingerprint = True
```

Fingerprinting attempts to identify probable CMS, frameworks, application stacks, static-site tooling, and infrastructure providers.

Use it when you want to adjust scan strategy based on detected technologies.

---

## 🛡️ WAF detection and safe mode

Enable passive WAF detection:

```ini
waf_detect = True
```

Enable cautious WAF-aware behavior:

```ini
waf_safe_mode = True
```

Safe mode automatically enables WAF detection in runtime configuration.

Use it for authorized targets protected by CDN, WAF, or anti-bot infrastructure.

---

## 🛡️ WAF guard

Enable WAF guard when you want the wizard profile to stop a scan early if the first classified primary responses are overwhelmingly WAF-blocked:

```ini
waf_guard = True
waf_guard_after = 50
waf_guard_threshold = 0.95
```

`waf_guard_after` is the minimum number of classified primary scan responses before the guard can trigger.

`waf_guard_threshold` is the WAF-blocked response ratio required to stop the scan. `0.95` means 95%.

Example low-noise WAF profile:

```ini
fingerprint = True
waf_safe_mode = True
waf_guard = True
waf_guard_after = 50
waf_guard_threshold = 0.95
threads = 1
delay = 1
timeout = 10
```

When triggered, OpenDoor stops gracefully and keeps generated reports for responses already processed. Plain origin `403 Forbidden` responses do not trigger WAF guard by themselves; responses must be classified as WAF / anti-bot blocked.

`waf_guard` automatically enables WAF detection in runtime configuration, but it does not enable `waf_safe_mode`. Add both when you want cautious request timing plus early stop behavior.

---

## 🧩 Header Injection Bypass

Enable controlled header-bypass probes:

```ini
header_bypass = True
```

Customize trigger statuses:

```ini
header_bypass_status = 401,403
```

Customize trusted IP values:

```ini
header_bypass_ips = 127.0.0.1,10.0.0.1,192.168.1.1
```

Customize tested headers:

```ini
header_bypass_headers = X-Original-URL,X-Rewrite-URL,X-Forwarded-For,X-Real-IP
```

Limit the number of probe variants per blocked URL:

```ini
header_bypass_limit = 32
```

Use `0` for unlimited variants:

```ini
header_bypass_limit = 0
```

Header-bypass probes are temporary per-request headers. They do not mutate global headers configured with `header`.

Use this feature only on systems you are authorized to test.

---

## 🧠 Auto-calibration

Auto-calibration helps reduce soft-404, wildcard, and catch-all noise.

```ini
auto_calibrate = True
calibration_samples = 5
calibration_threshold = 0.92
```

Use auto-calibration when invalid paths return successful-looking or repetitive responses.

Example:

```ini
method = GET
auto_calibrate = True
calibration_samples = 8
calibration_threshold = 0.85
```

---

## 📚 Wordlists and extensions

Use a custom local wordlist:

```ini
wordlist = ./wordlists/custom.txt
```

Use a remote HTTP(S) wordlist:

```ini
wordlist = https://example.com/wordlists/custom.txt
```

Bundled OpenDoor dictionaries are treated as `internal`. Any value configured through `wordlist` is treated as `external`; remote files are downloaded before scan start and are limited to 500 MB.

Shuffle scan order:

```ini
random_list = True
```

Add a path prefix:

```ini
prefix = admin/
```

Filter by extensions:

```ini
extensions = php,json,txt
```

This keeps only wordlist entries that already have the selected extensions.

Ignore extensions:

```ini
ignore_extensions = aspx,jsp,do
```

---

## 🔁 Recursive scan

Enable recursive directory discovery:

```ini
recursive = True
recursive_depth = 2
recursive_status = 200,301,302,307,308,403
recursive_exclude = jpg,jpeg,png,gif,svg,css,js,ico,woff,woff2,ttf,map,pdf,zip,gz,tar
```

Use recursion when discovered directories should become new scan roots.

Keep recursion depth controlled to avoid overly large scans.

---

## 🔍 Sniffers

Sniffers are built-in response analysis plugins.

```ini
sniff = skipempty,collation,indexof,file,openredirect
```

Known false-positive response sizes:

```ini
sniff = skipempty,skipsizes=24:41:50
```

Common values:

| Sniffer | Purpose |
|---|---|
| `skipempty` | Skip empty responses |
| `skipsizes=NUM:NUM...` | Skip known false-positive body sizes |
| `indexof` | Detect directory listings |
| `file` | Detect downloadable or interesting files |
| `collation` | Detect repeated fallback responses |
| `openredirect` | Verify redirect-like parameters for confirmed open redirect issues |

For details, see [Sniffers](Sniffers.md).

---

## 🧹 Response filters

Response filters keep or remove responses by status, size, text, regex, and body length.

```ini
include_status = 200-299,301,302,403
exclude_status = 404,429,500-599
exclude_size = 0,1234
exclude_size_range = 0-256,1024-2048
min_response_length = 100
max_response_length = 50000
```

Body-based filters:

```ini
match_text = Dashboard
exclude_text = Not Found
match_regex = admin|login|dashboard
exclude_regex = 404|not found
```

Body-based filters are most useful with:

```ini
method = GET
```

---

## 🌐 Proxy and transport settings

### Proxy

Use a permanent proxy:

```ini
proxy = socks5://127.0.0.1:9050
```

Use the built-in proxy list:

```ini
proxy_pool = True
```

Use a custom proxy list:

```ini
proxy_list = ./proxies.txt
```

### Network transport

Direct mode:

```ini
transport = direct
```

Proxy transport:

```ini
transport = proxy
proxy = socks5://127.0.0.1:9050
```

OpenVPN transport:

```ini
transport = openvpn
transport_profile = ./vpn/profile.ovpn
openvpn_auth = ./vpn/auth.txt
```

WireGuard transport:

```ini
transport = wireguard
transport_profile = ./vpn/profile.conf
```

Multiple profiles:

```ini
transport_profiles = ./vpn/profiles.txt
transport_rotate = per-target
```

Transport timeout and healthcheck:

```ini
transport_timeout = 30
transport_healthcheck_url = https://ifconfig.me
```

Never commit real OpenVPN profiles, WireGuard private keys, auth files, or production transport credentials to a public repository.

---

## 📊 Reports

Configure report formats:

```ini
reports = std,json,html,sqlite,csv,sarif
```

Custom reports directory:

```ini
reports_dir = ./reports
```

Common formats:

| Format   | Purpose                                       |
|----------|-----------------------------------------------|
| `std`    | Terminal output                               |
| `txt`    | Plain text output                             |
| `json`   | Machine-readable output                       |
| `html`   | Human-readable report                         |
| `csv`    | Column-separated report                       |
| `sqlite` | Structured local database for post-processing |
| `sarif`  | SARIF 2.1.0 output for CI/CD code scanning |

Header-bypass metadata is preserved in reports when `header_bypass = True` finds a candidate. CSV and SQLite expose dedicated bypass fields, while JSON and HTML preserve full `report_items` metadata.

If your local build supports additional report plugins, use the formats shown by:

```shell
opendoor --help
```

---

## 🔁 Sessions

Save scan state:

```ini
session_save = ./sessions/example.session
session_autosave_sec = 20
session_autosave_items = 200
```

Resume from a checkpoint:

```ini
session_load = ./sessions/example.session
```

Sessions are useful for large scans, unstable networks, recursive discovery, and transport-based workflows.

---

## 🧪 CI/CD fail-on rules

Enable CI/CD fail-on behavior by selected result buckets:

```ini
fail_on_bucket = success,auth,forbidden,blocked,bypass,openredirect
```

When at least one selected bucket is found, OpenDoor exits with code `1`.

Use the `bypass` bucket when header-bypass candidates should fail the pipeline. Use the `openredirect` bucket when confirmed open redirect vulnerabilities should fail the pipeline.

This is useful for:

- security gates;
- nightly exposure checks;
- release pipelines;
- regression tests.

---

## 🐞 Debugging

Debug levels:

```ini
debug = 0
```

Common values:

| Value | Meaning |
|---:|---|
| `-1` | Quiet progress mode |
| `0` | Normal output |
| `1` | Scanner decisions and enabled features |
| `2` | Outgoing HTTP request diagnostics |
| `3` | Incoming HTTP response and classification diagnostics |

Use debug output when validating request behavior, filters, reports, sessions, or transport startup.

---

## ✅ Example: low-noise directory scan

```ini
[general]

host = example.com
scheme = https://
port = 443

scan = directories
method = GET
threads = 10
timeout = 30
retries = 3

auto_calibrate = True
calibration_samples = 8
calibration_threshold = 0.85

include_status = 200-299,301,302,403
exclude_status = 404,429,500-599
exclude_size_range = 0-256

sniff = skipempty,collation,indexof,file

reports = std,json,html
reports_dir = ./reports
```

Run:

```shell
opendoor --wizard ./configs/example.com.conf
```

---

## ✅ Example: WAF-safe scan

```ini
[general]

host = example.com
scheme = https://
port = 443

scan = directories
method = GET
threads = 3
delay = 1
timeout = 60
retries = 5

waf_safe_mode = True
auto_calibrate = True

header_bypass = True
header_bypass_limit = 32
header_bypass_status = 401,403

reports = std,json,csv,sqlite
```

Run:

```shell
opendoor --wizard ./configs/waf-safe-example.conf
```

---

## ✅ Example: Header-bypass profile

```ini
[general]

host = example.com
scheme = https://
port = 443

scan = directories
method = GET
threads = 3
delay = 1
timeout = 60
retries = 5

waf_detect = True
waf_safe_mode = True

header_bypass = True
header_bypass_status = 401,403
header_bypass_ips = 127.0.0.1,10.0.0.1,192.168.1.1
header_bypass_headers = X-Original-URL,X-Rewrite-URL,X-Forwarded-For,X-Real-IP
header_bypass_limit = 32

reports = std,json,csv,sqlite
reports_dir = ./reports
```

Run:

```shell
opendoor --wizard ./configs/header-bypass-example.conf
```

---

## ✅ Example: OpenVPN transport scan

```ini
[general]

host = example.com
scheme = https://
port = 443

scan = directories
method = HEAD
threads = 5

transport = openvpn
transport_profile = ./vpn/profile.ovpn
openvpn_auth = ./vpn/auth.txt
transport_timeout = 60
transport_healthcheck_url = https://ifconfig.me

reports = std,json,sqlite
```

Run:

```shell
opendoor --wizard ./configs/openvpn-example.conf
```

---

## ✅ Example: CI/CD profile

```ini
[general]

host = example.com
scheme = https://
port = 443

scan = directories
method = GET

auto_calibrate = True
include_status = 200-299,301,302,403
exclude_status = 404,429,500-599

reports = json,sqlite
reports_dir = ./reports

fail_on_bucket = success,auth,forbidden,bypass
```

Run:

```shell
opendoor --wizard ./configs/ci-example.conf
```

---

## ⚠️ Configuration notes

Some options use `None` as the disabled value in configuration files.

Recommended disabled value:

```ini
keep_alive = None
accept_cookies = None
random_list = None
header_bypass = None
```

Recommended enabled value:

```ini
keep_alive = True
accept_cookies = True
random_list = True
header_bypass = True
```

Avoid storing secrets in configuration files committed to Git.

Do not commit:

- real VPN private keys;
- OpenVPN auth files;
- production proxy credentials;
- authenticated cookies;
- bearer tokens;
- customer-specific target lists.


Optional executable override:

```ini
transport_bin = /opt/homebrew/sbin/openvpn
```

On Windows, point it to `openvpn.exe` when the OpenVPN installer did not add it to `PATH`. If the VPN is managed by a GUI app or a corporate agent, keep `transport = direct` and start the VPN outside OpenDoor.
