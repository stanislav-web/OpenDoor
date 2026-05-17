# OpenDoor

**OpenDoor** is an open-source CLI scanner for authorized web reconnaissance, directory discovery, and exposure assessment.

It helps security researchers, penetration testers, bug bounty hunters, DevSecOps engineers, and developers identify exposed paths, login panels, directory listings, restricted resources, backup files, web shells, subdomains, and other potentially sensitive web assets.

OpenDoor supports single-target and batch scanning, custom wordlists, response filtering, recursive discovery, fingerprint detection, passive WAF detection, controlled Header Injection Bypass probes, smart auto-calibration, resumable sessions, CI/CD fail-on rules, multiple report formats, and optional network transport profiles for proxy, OpenVPN, and WireGuard workflows.

> Use OpenDoor only on systems you own or have explicit permission to test.

![OpenDoor](https://github.com/stanislav-web/OpenDoor/raw/master/logo.png)

---

## 🚀 Start here

| Page | Purpose |
|---|---|
| [Quickstart](quickstart.md) | Install OpenDoor and run common scans quickly. |
| [Installation and update](Installation-and-update.md) | Install and update with Homebrew, pipx, pip, Docker, Linux packages, or source checkouts. |
| [Usage](Usage.md) | Full CLI usage and option reference. |
| [Sniffers](Sniffers.md) | Built-in response analysis and false-positive reduction. |
| [Wizard](Wizard.md) | Interactive configuration workflow. |

---

## 🎯 Target input

OpenDoor can scan a single target, a target file, or targets from standard input.

```shell
opendoor --host https://example.com
opendoor --hostlist targets.txt
cat targets.txt | opendoor --stdin
```

This makes OpenDoor usable both as an interactive scanner and as a batch-oriented CLI tool for larger target sets.

---

## 🔎 Discovery

OpenDoor supports directory discovery and subdomain discovery.

```shell
opendoor --host https://example.com --scan directories
opendoor --host example.com --scan subdomains
```

You can use the built-in dictionaries or provide your own wordlists.

```shell
opendoor --host https://example.com --wordlist ./paths.txt
opendoor --host https://example.com --extensions php,json,txt  # keep only matching wordlist extensions
opendoor --host https://example.com --ignore-extensions aspx,jsp
```

---

## 🧹 Filtering and false-positive reduction

Modern web applications often return noisy responses: soft-404 pages, wildcard routes, CDN error pages, login redirects, and synthetic success pages.

OpenDoor provides several ways to reduce noise:

```shell
opendoor --host https://example.com --include-status 200-299,301,302,403
opendoor --host https://example.com --exclude-status 404,429,500-599
opendoor --host https://example.com --exclude-size-range 0-256,1024-2048
opendoor --host https://example.com --match-regex "admin|login|dashboard"
```

---

## 🧠 Auto-calibration

Auto-calibration helps classify soft-404, wildcard, and catch-all responses before the main scan produces noisy results.

```shell
opendoor --host https://example.com --auto-calibrate
opendoor --host https://example.com --auto-calibrate --calibration-samples 8 --calibration-threshold 0.85
```

Use it when the target returns similar pages for valid and invalid paths.

---

## 🧬 Fingerprint detection

OpenDoor can identify probable application stacks, CMS platforms, frameworks, static-site tooling, and infrastructure providers.

```shell
opendoor --host https://example.com --fingerprint
```

Fingerprinting is useful for understanding what kind of system you are scanning before deeper testing.

---

## 🛡️ WAF detection and safe mode

OpenDoor can passively detect probable WAF or anti-bot behavior.

```shell
opendoor --host https://example.com --waf-detect
opendoor --host https://example.com --waf-safe-mode
```

Safe mode enables a more cautious runtime profile after probable WAF or anti-bot behavior is detected.

Use WAF guard when early classified responses are overwhelmingly WAF-blocked and you want OpenDoor to stop the scan before a long wordlist produces mostly blocked results.

```shell
opendoor --host https://example.com --waf-safe-mode --waf-guard
```

---

## 🧩 Header Injection Bypass

OpenDoor can optionally probe blocked `401` and `403` paths with controlled Header Injection Bypass variants.

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --waf-detect \
  --header-bypass \
  --header-bypass-limit 32
```

The scanner records exact bypass evidence in detailed reports:

- bypass type;
- header name;
- header value;
- original status code;
- resulting status code.

Header-bypass probes are temporary per-request headers and do not mutate the global scan headers.

---

## 🔁 Resumable sessions

Long-running scans can be saved and resumed later.

```shell
opendoor --host https://example.com --session-save scan.session
opendoor --session-load scan.session
```

Sessions are useful for large wordlists, unstable networks and transport-based workflows.

---

## 🌐 Network transports

OpenDoor supports direct, proxy, OpenVPN, and WireGuard transport modes.

```shell
opendoor --host https://example.com --transport direct
opendoor --host https://example.com --transport proxy --proxy socks5://127.0.0.1:9050
opendoor --host https://example.com --transport openvpn --transport-profile ./profile.ovpn
opendoor --host https://example.com --transport wireguard --transport-profile ./profile.conf
```

Transport profiles are local runtime files. Never commit real VPN private keys, OpenVPN credentials, or production profiles to a public repository.

---

## 📊 Reports

OpenDoor can write results in multiple formats.

```shell
opendoor --host https://example.com --reports std,json,html,sarif
opendoor --host https://example.com --reports json,sqlite --reports-dir ./reports
```

| Format   | Purpose |
|----------|---|
| `std`    | Terminal output |
| `txt`    | Plain text output |
| `json`   | Machine-readable output |
| `csv`    | Spreadsheet-friendly output |
| `html`   | Human-readable report |
| `sqlite` | Structured local database for post-processing |
| `sarif`  | SARIF 2.1.0 output for CI/CD code scanning |

Header-bypass evidence is preserved in detailed report formats. CSV and SQLite reports expose dedicated bypass fields, while JSON and HTML keep the full `report_items` metadata.

---

## 🧪 CI/CD fail-on rules

OpenDoor can be used as a pipeline gate.

```shell
opendoor --host https://example.com --fail-on-bucket success,auth,forbidden,blocked,bypass
```

This allows OpenDoor to complete the scan and return exit code `1` only when selected result buckets are found.

Use the `bypass` bucket when Header Injection Bypass candidates should fail the pipeline.

---

## ⚖️ Responsible use

OpenDoor is a security testing tool. Use it only against systems where you have authorization.

Features such as WAF detection, WAF-safe scanning, raw request replay, transport profiles, and Header Injection Bypass probes are intended for authorized security testing, defensive validation, and exposure regression checks.

Do not use OpenDoor to scan third-party infrastructure, public services, organizations, or commercial systems without explicit permission.
