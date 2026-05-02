# 🧭 Usage

This page describes the OpenDoor command-line interface and common scan workflows.

Use:

```shell
opendoor --help
```

to see the exact options available in your installed build.

---

## 🎯 Target input

OpenDoor accepts one target, a target list, targets from standard input, or a saved session.

Only one of these modes should be used at a time:

```shell
opendoor --host https://example.com
opendoor --hostlist targets.txt
cat targets.txt | opendoor --stdin
opendoor --session-load scan.session
```

### Single target

```shell
opendoor --host https://example.com
```

Use a full URL for directory scans.

### Target list

```shell
opendoor --hostlist targets.txt
```

Example `targets.txt`:

```text
https://example.com
https://app.example.com
example.org
192.168.1.10
192.168.1.0/24
192.168.1.10-192.168.1.50
```

Target lists support mixed URLs, domains, IPv4 addresses, IPv4 CIDR blocks, and inclusive IPv4 ranges.
Expanded targets are deduplicated before scanning.

### Standard input

```shell
cat targets.txt | opendoor --stdin
```

This is useful when OpenDoor is part of a larger pipeline. STDIN accepts the same mixed target format as `--hostlist`.

### Resume from session

```shell
opendoor --session-load scan.session
```

Use this when a previous scan was saved with `--session-save`.

---

## 🔎 Scan modes

OpenDoor supports directory discovery and subdomain discovery.

```shell
opendoor --host https://example.com --scan directories
opendoor --host example.com --scan subdomains
```

### Directory discovery

Directory discovery is used to find exposed paths, files, backups, login panels, admin areas, and other web resources.

```shell
opendoor --host https://example.com --scan directories
```

### Subdomain discovery

Subdomain discovery is used to enumerate probable subdomains from a dictionary.

```shell
opendoor --host example.com --scan subdomains
```

Use a domain name instead of a full path when scanning subdomains.

---

## 📚 Wordlists and extensions

### Custom wordlist

```shell
opendoor --host https://example.com --wordlist ./wordlist.txt
```

A custom wordlist is useful when testing a specific technology stack, application, CMS, or organization-specific naming pattern.

### Shuffle scan list

```shell
opendoor --host https://example.com --random-list
```

This randomizes scan order.

### Prefix

```shell
opendoor --host https://example.com --prefix admin/
```

The prefix is appended to scanned paths.

### Force extensions

```shell
opendoor --host https://example.com --extensions php,json,txt
```

Short form:

```shell
opendoor --host https://example.com -e php,json,txt
```

### Ignore extensions

```shell
opendoor --host https://example.com --ignore-extensions aspx,jsp
```

Short form:

```shell
opendoor --host https://example.com -i aspx,jsp
```

---

## 🔁 Recursive scan

Recursive scan expands discovered directories and scans deeper paths.

```shell
opendoor --host https://example.com --recursive
```

### Limit recursion depth

```shell
opendoor --host https://example.com --recursive --recursive-depth 2
```

### Control recursive expansion statuses

```shell
opendoor --host https://example.com --recursive --recursive-status 200,301,302,403
```

Only responses with selected statuses are used as recursive expansion points.

### Exclude file extensions from recursion

```shell
opendoor --host https://example.com --recursive --recursive-exclude jpg,png,css,js,pdf
```

This prevents static assets and binary files from becoming recursive scan roots.

---

## 🌐 Request options

### Port

```shell
opendoor --host https://example.com --port 8443
```

Short form:

```shell
opendoor --host https://example.com -p 8443
```

### HTTP method

OpenDoor uses `HEAD` by default.

```shell
opendoor --host https://example.com --method GET
```

Short form:

```shell
opendoor --host https://example.com -m GET
```

Use `GET` when you need body-based filters such as `--match-text`, `--exclude-text`, `--match-regex`, or `--exclude-regex`.

### Delay

```shell
opendoor --host https://example.com --delay 0.5
```

Short form:

```shell
opendoor --host https://example.com -d 0.5
```

### Timeout

```shell
opendoor --host https://example.com --timeout 60
```

### Retries

```shell
opendoor --host https://example.com --retries 5
```

Short form:

```shell
opendoor --host https://example.com -r 5
```

### Threads (1 ~ 50)

```shell
opendoor --host https://example.com --threads 20
```

Short form:

```shell
opendoor --host https://example.com -t 20
```

### Keep-alive

```shell
opendoor --host https://example.com --keep-alive
```

### Headers

```shell
opendoor --host https://example.com --header "X-Test: 1"
opendoor --host https://example.com --header "Authorization: Bearer TOKEN"
```

### Cookies

```shell
opendoor --host https://example.com --cookie "sid=abc123"
```

### Accept cookies from responses

```shell
opendoor --host https://example.com --accept-cookies
```

---

## 🧾 Raw HTTP request

OpenDoor can read a raw HTTP request exported from a proxy, repeater, or similar testing tool.

```shell
opendoor --raw-request request.txt
```

If the request line uses a relative path, provide the scheme:

```shell
opendoor --raw-request request.txt --scheme https
```

Raw requests are useful for authenticated scans, custom headers, application-specific cookies, or copied requests from a browser/proxy workflow.

Example raw request:

```http
GET /admin HTTP/1.1
Host: example.com
User-Agent: OpenDoor
Cookie: sid=abc123
```

---

## 🧹 Response filters

Response filters are deterministic user-defined filters. They help keep only relevant responses and remove known noise.

### Include statuses

```shell
opendoor --host https://example.com --include-status 200-299,301,302,403
```

### Exclude statuses

```shell
opendoor --host https://example.com --exclude-status 404,429,500-599
```

### Exclude exact response sizes

```shell
opendoor --host https://example.com --exclude-size 0,1234
```

### Exclude response size ranges

```shell
opendoor --host https://example.com --exclude-size-range 0-256,1024-2048
```

### Match text

```shell
opendoor --host https://example.com --method GET --match-text "Dashboard"
```

`--match-text` is repeatable.

### Exclude text

```shell
opendoor --host https://example.com --method GET --exclude-text "Not Found"
```

`--exclude-text` is repeatable.

### Match regex

```shell
opendoor --host https://example.com --method GET --match-regex "admin|login|dashboard"
```

`--match-regex` is repeatable.

### Exclude regex

```shell
opendoor --host https://example.com --method GET --exclude-regex "404|not found"
```

`--exclude-regex` is repeatable.

### Minimum response length

```shell
opendoor --host https://example.com --min-response-length 100
```

### Maximum response length

```shell
opendoor --host https://example.com --max-response-length 50000
```

### Practical filter example

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --include-status 200-299,301,302,403 \
  --exclude-size-range 0-256 \
  --exclude-regex "not found|404"
```

---

## 🧠 Auto-calibration

Auto-calibration helps classify soft-404, wildcard, and catch-all responses.
Starting with OpenDoor 5.14.3, it also uses lightweight semantic response-diff signals such as visible text, soft-404 phrases, DOM-token structure, text density, and normalized dynamic fragments.
Starting with OpenDoor 5.14.4, subdomain scans can also use DNS wildcard calibration when `--scan subdomains --auto-calibrate` is enabled.

```shell
opendoor --host https://example.com --auto-calibrate
```

### Calibration samples

```shell
opendoor --host https://example.com --auto-calibrate --calibration-samples 8
```

### Calibration threshold

```shell
opendoor --host https://example.com --auto-calibrate --calibration-threshold 0.85
```

The threshold accepts values from `0.01` to `1.0`.

Use auto-calibration when a target returns similar pages for invalid and valid paths.
It is especially useful when dynamic 404 templates contain changing tokens, timestamps, trace IDs, A/B wrappers, or personalized fragments.


### DNS wildcard calibration for subdomains

```shell
opendoor --host example.com --scan subdomains --auto-calibrate
```

When subdomain auto-calibration is enabled, OpenDoor resolves random impossible subdomains first. If those random names resolve, OpenDoor treats the returned addresses as a wildcard DNS baseline.

During the scan, candidates that resolve only to the wildcard baseline are classified into the `calibrated` bucket before HTTP probing. This reduces catch-all DNS noise while keeping default subdomain scanning unchanged unless `--auto-calibrate` is explicitly enabled.

---

## 🧬 Fingerprint detection

Fingerprinting attempts to identify probable CMS, frameworks, application stacks, custom technologies, and infrastructure providers before the scan.

```shell
opendoor --host https://example.com --fingerprint
```

Fingerprinting is useful for:

- choosing better wordlists;
- understanding the target stack;
- identifying static hosting or CDN providers;
- adjusting filters and scan strategy.


OpenDoor 5.14.5 expands the passive fingerprint catalog with selected regional CMS, site-builder and strong HTTP-visible infrastructure signatures, including InstantCMS, Duda, Hostinger Website Builder, CMS.S3 / Megagroup, Webasyst / Shop-Script, Discuz!, NetCat, Hostinger, DDoS-Guard and Tencent Cloud.


---

## 🛡️ WAF detection and safe mode

### WAF detection

```shell
opendoor --host https://example.com --waf-detect
```

This passively detects probable WAF or anti-bot protections before classifying responses.

### Safe mode

```shell
opendoor --host https://example.com --waf-safe-mode
```

Safe mode automatically switches to a more cautious scan profile after WAF detection.

Use this mode when scanning authorized targets protected by WAF, CDN, or anti-bot infrastructure.

---

## 🧩 Header Injection Bypass

Header Injection Bypass is an opt-in feature for authorized testing of blocked resources.

When enabled, OpenDoor probes configured blocked statuses with controlled, temporary per-request headers. `--header-bypass` flow also tries safe path-manipulation variants after header probes. 
If a probe changes a blocked response into a meaningful result, OpenDoor records it in the `bypass` result bucket with exact evidence.

### Enable header-bypass probes

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass
```

By default, OpenDoor probes `401` and `403` responses.

### Recommended WAF-aware usage

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --waf-detect \
  --waf-safe-mode \
  --header-bypass \
  --header-bypass-limit 32 \
  --reports std,json,csv,sqlite
```

### Customize trigger statuses

```shell
opendoor \
  --host https://example.com \
  --header-bypass \
  --header-bypass-status 401,403
```

The value accepts comma-separated HTTP statuses and status ranges.

Examples:

```shell
opendoor --host https://example.com --header-bypass --header-bypass-status 401,403
opendoor --host https://example.com --header-bypass --header-bypass-status 401-403
```

### Customize trusted IP values

```shell
opendoor \
  --host https://example.com \
  --header-bypass \
  --header-bypass-ips 127.0.0.1,10.0.0.1,192.168.1.1
```

These values are used with trusted-IP style headers such as `X-Forwarded-For`, `X-Real-IP`, `Client-IP`, and similar headers.

### Customize header names

```shell
opendoor \
  --host https://example.com \
  --header-bypass \
  --header-bypass-headers X-Original-URL,X-Rewrite-URL,X-Forwarded-For,X-Real-IP
```

OpenDoor supports path-based, host/origin, trusted-IP, and URL-style bypass header families.

### Limit probe variants

```shell
opendoor \
  --host https://example.com \
  --header-bypass \
  --header-bypass-limit 32
```

Use `0` for unlimited variants:

```shell
opendoor \
  --host https://example.com \
  --header-bypass \
  --header-bypass-limit 0
```

### Path-manipulation probes

Path-manipulation probes are enabled automatically when `--header-bypass` is enabled.

OpenDoor tries header-injection variants first, then safe path variants such as:

| Variant | Example |
|---|---|
| `trailing-slash` | `/admin` → `/admin/` |
| `double-leading-slash` | `/admin` → `//admin` |
| `dot-segment` | `/admin` → `/admin/.` |
| `semicolon-suffix` | `/admin` → `/admin;/` |
| `case-variation` | `/admin` → `/Admin` |
| `url-encoded-segment` | `/admin panel` → `/admin%20panel` |

Path probes are controlled by the same `--header-bypass-limit` option.

### Reported evidence

Successful candidates are stored in the `bypass` bucket.

Detailed report items include:

| Field | Meaning |
|---|---|
| `bypass` | Bypass type: `header` or `path` |
| `bypass_header` | Header that produced the candidate for header-based probes |
| `bypass_variant` | Path-manipulation variant name for path-based probes |
| `bypass_value` | Header value or path value used for the probe |
| `bypass_url` | Full probe URL for path-based probes |
| `bypass_from_code` | Original blocked status code |
| `bypass_to_code` | Resulting status code |

CSV reports include dedicated columns for these fields. SQLite reports persist them in nullable item columns. JSON and HTML reports preserve them in `report_items`.

### Notes

- Header-bypass probes are disabled by default.
- Probe headers are temporary per-request headers.
- Normal scan headers are not mutated.
- Use this only on systems you are authorized to test.
- Combine with `--waf-safe-mode`, `--delay`, lower `--threads`, and higher `--timeout` for cautious WAF-protected scans.

---

## 🔁 Sessions

Sessions allow long-running scans to be saved and resumed.

### Save a session

```shell
opendoor --host https://example.com --session-save scan.session
```

### Autosave by time

```shell
opendoor \
  --host https://example.com \
  --session-save scan.session \
  --session-autosave-sec 20
```

### Autosave by processed items

```shell
opendoor \
  --host https://example.com \
  --session-save scan.session \
  --session-autosave-items 200
```

### Load a session

```shell
opendoor --session-load scan.session
```

Sessions are useful for:

- large wordlists;
- unstable networks;
- batch scans;
- recursive scans;
- transport-based workflows;
- scans interrupted by terminal or system restarts.

---

## 🌐 Proxy and transport options

OpenDoor supports proxy usage and network transport profiles.

### Permanent proxy

```shell
opendoor --host https://example.com --proxy socks5://127.0.0.1:9050
```

### Built-in proxy list

```shell
opendoor --host https://example.com --proxy-pool
```

### Custom proxy list

```shell
opendoor --host https://example.com --proxy-list proxies.txt
```

### Transport mode

```shell
opendoor --host https://example.com --transport direct
opendoor --host https://example.com --transport proxy --proxy socks5://127.0.0.1:9050
opendoor --host https://example.com --transport openvpn --transport-profile ./profile.ovpn
opendoor --host https://example.com --transport wireguard --transport-profile ./profile.conf
```

Available transport modes:

| Mode | Purpose |
|---|---|
| `direct` | Default network path |
| `proxy` | Route traffic through a configured proxy |
| `openvpn` | Bring up an OpenVPN profile for the scan |
| `wireguard` | Bring up a WireGuard profile for the scan |

### Single transport profile

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn
```

```shell
opendoor \
  --host https://example.com \
  --transport wireguard \
  --transport-profile ./profile.conf
```

### Multiple transport profiles

```shell
opendoor \
  --hostlist targets.txt \
  --transport openvpn \
  --transport-profiles vpn-profiles.txt
```

Example `vpn-profiles.txt`:

```text
./vpn/profile-1.ovpn
./vpn/profile-2.ovpn
./vpn/profile-3.ovpn
```

### Transport rotation

```shell
opendoor \
  --hostlist targets.txt \
  --transport openvpn \
  --transport-profiles vpn-profiles.txt \
  --transport-rotate per-target
```

Supported rotation modes:

| Mode | Behavior |
|---|---|
| `none` | Use the selected transport without rotation |
| `per-target` | Rotate transport profiles between targets |

### Transport timeout

```shell
opendoor --host https://example.com --transport-timeout 60
```

### Transport healthcheck

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn \
  --transport-healthcheck-url https://ifconfig.me
```

### OpenVPN auth-user-pass

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn \
  --openvpn-auth ./auth.txt
```

Never commit real OpenVPN profiles, WireGuard private keys, auth files, or production transport credentials to a public repository.

---

## 📊 Reports

OpenDoor can write scan results in multiple formats.

```shell
opendoor --host https://example.com --reports std,json,html
opendoor --host https://example.com --reports json,sqlite,sarif --reports-dir ./reports
```

Available report formats:

| Format   | Purpose                                       |
|----------|-----------------------------------------------|
| `std`    | Terminal output                               |
| `txt`    | Plain text output                             |
| `json`   | Machine-readable output                       |
| `csv`    | Column-separated output                       |
| `html`   | Human-readable report                         |
| `sqlite` | Structured local database for post-processing |
| `sarif`  | SARIF 2.1.0 output for CI/CD code scanning     |

When `--header-bypass` is enabled and a header or path candidate is found, report formats preserve bypass evidence:

| Report | Header-bypass evidence |
|---|---|
| `std` | Shows the `bypass` bucket in summary statistics |
| `txt` | Includes bypass evidence in bypass report lines |
| `json` | Preserves full metadata in `report_items` |
| `csv` | Adds dedicated bypass columns |
| `html` | Preserves detailed `report_items` metadata |
| `sqlite` | Stores bypass metadata in nullable item columns |
| `sarif` | Preserves bypass evidence in SARIF result properties |

### SARIF reports

```shell
opendoor --host https://example.com --reports sarif,json --reports-dir ./reports
```

Use SARIF when OpenDoor findings should be uploaded to GitHub Code Scanning or other SARIF-compatible CI/CD security tooling. OpenDoor emits SARIF 2.1.0 and preserves URL, status code, response size, WAF, bypass and fingerprint evidence in result properties.

```yaml
- name: Upload OpenDoor SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: reports/example.com/example.com.sarif
    category: opendoor
```


### Custom reports directory

```shell
opendoor --host https://example.com --reports json,html --reports-dir ./reports
```

---

## 🧪 CI/CD fail-on rules

OpenDoor can behave as a CI/CD quality gate.

```shell
opendoor --host https://example.com --fail-on-bucket success,auth,forbidden,blocked,bypass
```

When selected buckets are found, OpenDoor exits with code `1`.

The `bypass` bucket can be used as a CI/CD signal when header-bypass candidates should fail the pipeline.

This is useful for:

- GitHub Actions;
- GitLab CI;
- nightly exposure checks;
- release gates;
- security regression tests.

Example:

```shell
opendoor \
  --host https://example.com \
  --reports json,sqlite \
  --fail-on-bucket success,auth,forbidden,bypass
```

---

## 🔍 Sniffers

Sniffers are built-in response analysis plugins.

```shell
opendoor --host https://example.com --sniff indexof
opendoor --host https://example.com --sniff skipempty
opendoor --host https://example.com --sniff skipsizes=24:41:50
```

Multiple sniffers can be combined:

```shell
opendoor --host https://example.com --sniff skipempty,file,collation,indexof,skipsizes=24:41:50
```

For details, see [Sniffers](Sniffers.md).

---

## 🐞 Debugging

### Debug levels

```shell
opendoor --host https://example.com --debug 1
opendoor --host https://example.com --debug 2
opendoor --host https://example.com --debug 3
```

Silent mode:

```shell
opendoor --host https://example.com --debug -1
```

Use debug output when validating filters, transport behavior, request headers, response classification, or report generation.

---

## 🧰 Application tools

### Show current version

```shell
opendoor --version
```

### Show examples

```shell
opendoor --examples
```

### Open documentation

```shell
opendoor --docs
```

### Run wizard

```shell
opendoor --wizard
```

### Show update instructions

```shell
opendoor --update
```

---

## ✅ Practical workflows

### Low-noise directory scan

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --auto-calibrate \
  --include-status 200-299,301,302,403 \
  --exclude-size-range 0-256 \
  --reports std,json,csv
```

### Authenticated scan from raw request

```shell
opendoor \
  --raw-request request.txt \
  --scheme https \
  --method GET \
  --auto-calibrate \
  --reports json,html
```

### WAF-safe scan

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --timeout 60 \
  --retries 5 \
  --delay 0.5
```

### Header-bypass scan

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --waf-detect \
  --waf-safe-mode \
  --header-bypass \
  --header-bypass-limit 32 \
  --reports std,json,csv,sqlite
```

### Batch scan with reports

```shell
opendoor \
  --hostlist targets.txt \
  --reports json,sqlite,csv \
  --reports-dir ./reports
```

### CI/CD exposure gate

```shell
opendoor \
  --host https://example.com \
  --auto-calibrate \
  --reports json,sqlite,csv \
  --fail-on-bucket success,auth,forbidden,bypass
```

### CI/CD gate with header-bypass candidates

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass \
  --reports json,sqlite,csv \
  --fail-on-bucket success,auth,forbidden,bypass
```
