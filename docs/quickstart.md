# 🚀 Quickstart

This page shows the fastest way to install OpenDoor and run common scans.

---

## 📦 Install

Recommended installation for most CLI users:

```shell
pipx install opendoor
```

Alternative installation with pip:

```shell
python3 -m pip install --upgrade opendoor
```

On macOS, OpenDoor can also be installed with Homebrew:

```shell
brew install opendoor
```

Verify the installation:

```shell
opendoor --version
opendoor --help
```

Show update instructions for your installation method:

```shell
opendoor --update
```

`--update` is instruction-only. It does not execute package-manager commands and should be used with the same package manager that installed OpenDoor.

---

## 🔎 Run a basic directory scan

```shell
opendoor --host https://example.com
```

By default, OpenDoor runs a directory discovery scan using the built-in directory dictionary.

---

## 🌍 Scan subdomains

```shell
opendoor --host example.com --scan subdomains
```

Use a domain name for subdomain discovery.

---

## 📚 Use a custom wordlist

```shell
opendoor --host https://example.com --wordlist ./wordlist.txt
```

---

## 🎯 Scan multiple targets from a file

Create `targets.txt`:

```text
https://example.com
https://app.example.com
example.org
```

Run:

```shell
opendoor --hostlist targets.txt
```

---

## 🔗 Read targets from stdin

```shell
cat targets.txt | opendoor --stdin
```

This is useful for pipelines and automation.

---

## 📊 Save reports

```shell
opendoor --host https://example.com --reports std,json,html --reports-dir ./reports
```

Common report formats:

| Format | Usage |
|---|---|
| `std` | Terminal output |
| `txt` | Plain text output |
| `json` | Automation and processing |
| `csv` | Spreadsheet-friendly output |
| `html` | Human-readable report |
| `sqlite` | Structured local analysis |

---

## 🧹 Reduce false positives

Use response filters:

```shell
opendoor --host https://example.com --exclude-status 404,429,500-599
opendoor --host https://example.com --exclude-size-range 0-256
```

Use auto-calibration:

```shell
opendoor --host https://example.com --auto-calibrate
```

Auto-calibration helps classify soft-404, wildcard, and catch-all responses.

---

## 🧬 Detect technologies

```shell
opendoor --host https://example.com --fingerprint
```

Fingerprinting attempts to identify probable CMS, frameworks, application stacks, and infrastructure providers.

---

## 🛡️ Detect WAF behavior

```shell
opendoor --host https://example.com --waf-detect
```

Use safe mode for a cautious scan profile:

```shell
opendoor --host https://example.com --waf-safe-mode
```

Safe mode is designed to reduce aggressive behavior after WAF or anti-bot signals are detected.

---

## 🧩 Probe Header Injection Bypass

Header Injection Bypass is an opt-in check for authorized testing of blocked `401` and `403` paths.

It sends controlled, temporary per-request headers and records exact evidence when a blocked response changes to a meaningful result.

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --waf-detect \
  --header-bypass \
  --header-bypass-limit 32 \
  --reports std,json,csv,sqlite
```

Customize trigger statuses, trusted IP values, and tested headers:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass \
  --header-bypass-status 401,403 \
  --header-bypass-ips 127.0.0.1,10.0.0.1 \
  --header-bypass-headers X-Original-URL,X-Rewrite-URL,X-Forwarded-For,X-Real-IP \
  --reports json,html,sqlite
```

Use this only on systems you own or have explicit permission to test.

---

## 🔁 Resume interrupted scans

Save progress:

```shell
opendoor --host https://example.com --session-save scan.session
```

Resume later:

```shell
opendoor --session-load scan.session
```

---

## 🌐 Use a proxy

```shell
opendoor --host https://example.com --proxy socks5://127.0.0.1:9050
```

Or explicitly select proxy transport:

```shell
opendoor --host https://example.com --transport proxy --proxy socks5://127.0.0.1:9050
```

---

## 🔐 Use OpenVPN transport

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn
```

For username/password based OpenVPN profiles:

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn \
  --openvpn-auth ./auth.txt
```

---

## 🧵 Use WireGuard transport

```shell
opendoor \
  --host https://example.com \
  --transport wireguard \
  --transport-profile ./profile.conf
```

Never commit real VPN private keys or credentials to the repository.

---

## 🧪 CI/CD example

```shell
opendoor \
  --host https://example.com \
  --header-bypass \
  --fail-on-bucket success,auth,forbidden,bypass \
  --reports json,sqlite
```

OpenDoor will complete the scan and return exit code `1` only if selected result buckets are found.

The `bypass` bucket can be used as a CI/CD signal when Header Injection Bypass candidates should fail the pipeline.

---

## ➡️ Next steps

Read the full [Usage](Usage.md) page for all CLI options.
