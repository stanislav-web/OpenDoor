# OpenDoor — OWASP Web Recon & Directory Discovery Platform

![OpenDoor](https://github.com/stanislav-web/OpenDoor/raw/master/logo.png)

**OpenDoor** is an open-source CLI Recon Platform for authorized web reconnaissance, directory discovery, subdomain enumeration, fingerprints, WAF detection, bypass probing, response filtering, reporting, open-redirect checks, bounded crawl and transport-based scanning workflows.

It helps security researchers, penetration testers, bug bounty hunters, DevSecOps engineers, and developers identify exposed paths, login panels, directory listings, restricted resources, backup files, web shells, subdomains, and other potentially sensitive web assets.

> Use OpenDoor only on systems you own or have explicit permission to test.
---

## ✅ Project status

[![PyPI version](https://img.shields.io/pypi/v/opendoor)](https://pypi.org/project/opendoor/)
[![Homebrew](https://img.shields.io/homebrew/v/opendoor?label=homebrew)](https://formulae.brew.sh/formula/opendoor)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-green.svg)](https://www.python.org/)
[![Docker Image](https://github.com/stanislav-web/OpenDoor/actions/workflows/docker-image.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/docker-image.yml)

[![Coverage](https://codecov.io/github/stanislav-web/OpenDoor/graph/badge.svg?token=dyBxutYBso)](https://codecov.io/github/stanislav-web/OpenDoor)
[![CodeQL](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql)
[![Codacy Security Scan](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml)
[![Documentation Status](https://app.readthedocs.org/projects/opendoor/badge/?version=latest)](https://opendoor.readthedocs.io/)

## 🧪 CI matrix

| Platform | Python 3.12 | Python 3.13 | Python 3.14 |
|---|---|---|---|
| Linux | [![Linux 3.12](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py312.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py312.yml) | [![Linux 3.13](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py313.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py313.yml) | [![Linux 3.14](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py314.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-linux-py314.yml) |
| macOS | [![macOS 3.12](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py312.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py312.yml) | [![macOS 3.13](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py313.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py313.yml) | [![macOS 3.14](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py314.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-macos-py314.yml) |
| Windows | [![Windows 3.12](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py312.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py312.yml) | [![Windows 3.13](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py313.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py313.yml) | [![Windows 3.14](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py314.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/ci-windows-py314.yml) |

---

## 🚀 Quick links

- [Documentation](https://opendoor.readthedocs.io/)
- [Quickstart](https://opendoor.readthedocs.io/quickstart/)
- [Installation and update](https://opendoor.readthedocs.io/Installation-and-update/)
- [Usage guide](https://opendoor.readthedocs.io/Usage/)
- [Practical examples](https://opendoor.readthedocs.io/examples/basic-scans/)
- [Changelog](CHANGELOG.md)
- [PyPI package](https://pypi.org/project/opendoor/)
- [Homebrew formulae](https://formulae.brew.sh/formula/opendoor)
- [Docker image](https://github.com/users/stanislav-web/packages/container/package/opendoor)
- [AUR package](https://aur.archlinux.org/packages/opendoor)
- [BlackArch package](https://blackarch.org/webapp.html)
- [Issues](https://github.com/stanislav-web/OpenDoor/issues)
- [Contributors](https://github.com/stanislav-web/OpenDoor/graphs/contributors)

---

## ✨ Features

- directory discovery;
- recursive directory discovery;
- bounded same-origin crawl;
- redirects following;
- subdomain enumeration;
- multi-threading scans for faster lookups;
- single target, target file, stdin, IPv4 CIDR, and IPv4 range input modes;
- custom wordlists, prefixes, shuffling to break scan patterns and extension filters, remote wordlists supports;
- custom request headers, cookies forwarding, and raw HTTP request templates;
- response filters by status, size, text, regex, and body length;
- response sniffers for detecting directory listings, empty responses, known file exposures, active shadow-copy probes, collation, possible exposed secrets, client-exposed endpoints, errors, exposed debug stack traces, and verified open redirect vulnerabilities;
- smart auto-calibration for soft-404, wildcard, catch-all, semantic response-diff, and DNS wildcard cases;
- technology fingerprint detection for CMS, ecommerce platforms, frameworks, runtime stacks, infrastructure, and HSTS posture;
- passive privacy-risk checks in `--fingerprint`, including possible HSTS, ETag/cache, and supercookie surfaces.
- passive WAF detection and bypass in secure scanning mode;
- WAF guard stop condition for ending low-value scans when initial classified responses are overwhelmingly WAF-blocked;
- controlled header and path bypass probes for blocked `401` and `403` resources;
- fault-tolerant scan runtime with retries, fail-streak protection, transport failure handling, resumable sessions, and runtime pause/resume controls;
- CI/CD fail-on result bucket rules;
- differential report comparison for previous/current JSON or SQLite reports;
- reports in terminal, text, JSON, CSV, HTML, SARIF and SQLite formats;
- proxy, OpenVPN, and WireGuard transport profiles;
- sequential per-target transport rotation for batch workflows;
- configuration wizard for repeatable scan profiles;
- built-in wordlists (upd. 2026-06)

---

## 🧭 Where does OpenDoor make sense?

It is designed for real targets where speed alone is not enough: WAFs, CDNs, soft-404 pages, wildcard routes, restricted resources, authenticated areas, unstable networks, multi-target batches, and transport-controlled scans.
Since it first launch in 2016 to the present day, the OpenDoor has changed dramatically, growing from a primitive brute forcer into a new adaptive discovery framework. Became DevOps and QA friendly.
OpenDoor focuses on **context-aware discovery** instead of blind enumeration.

### What makes OpenDoor different

| Capability | Why it matters |
|---|---|
| **Fingerprint-first scanning** | OpenDoor can identify probable CMS platforms, frameworks, infrastructure providers, and WAF signals before deeper discovery. This helps you scan with context instead of blindly throwing a generic wordlist at the target. |
| **WAF-aware behavior** | OpenDoor can detect probable WAF / anti-bot behavior and switch to a safer runtime profile with `--waf-safe-mode`, reducing noisy blocked scans and making defensive responses easier to understand. |
| **WAF guard stop condition** | OpenDoor can stop a scan early when the initial classified responses are overwhelmingly WAF-blocked. This avoids spending long runs on wordlists that only produce repeated edge/WAF block pages. |
| **Controlled bypass evidence** | OpenDoor can optionally probe blocked `401` and `403` resources with controlled header-injection and path-manipulation variants. It records exact evidence such as bypass type, header or path variant, probe value, original status code, and resulting status code without mutating global scan headers. |
| **Multi-signal auto-calibration** | OpenDoor does not rely only on status code or response size. It compares multiple response signals such as body hashes, visible text, semantic soft-404 phrases, DOM-token structure, titles, redirects, stable headers, word count, line count, text density, normalized dynamic tokens, and DNS wildcard baselines to reduce soft-404 and wildcard false positives. |
| **Bounded same-origin crawl** | `--crawl` can enrich directory scans with one-hop same-origin links found in already scanned HTML responses. It uses the existing scan pipeline, global request deduplication, per-bucket report deduplication, and bounded memory caps instead of becoming a spider or browser renderer. |
| **Heuristic sniffer plugin system** | OpenDoor includes a pluggable response-analysis layer for heuristic sniffers such as secrets, stack traces, directory listings, malware indicators, shadow copies, suspicious files, open redirects, and repeated soft-error templates. This lets scans surface meaningful evidence from response bodies instead of reporting only status codes and sizes. |
| **Transport-level workflows** | OpenDoor supports direct, proxy, OpenVPN, and WireGuard transport modes. It can also rotate transport profiles per target in authorized batch scans, which is not the same as manually starting a VPN before running a scanner. |
| **Proxy pool support** | OpenDoor can use proxy pools through `--proxy-list`, validate available proxies before scanning, rotate requests across the live pool. This helps long authorized scans survive unreliable routes without hardcoding a single proxy endpoint. |
| **Fault-tolerant scan runtime** | OpenDoor is designed to keep scans useful on unstable targets and unreliable networks. It combines request retries, consecutive failure protection, recoverable transport-error handling, proxy rotation, WAF-aware stop conditions, checkpoint sessions, and interactive pause/resume controls so long scans can fail safely instead of silently losing coverage. |
| **Resumable long scans** | OpenDoor can save scan checkpoints and resume later. This matters when scans are interrupted by crashes, unstable networks, blocked routes, terminal disconnects, or long multi-target jobs. |
| **Runtime pause/resume** | Press `Ctrl+C` once during a scan to pause workers, then choose `C` to continue or `E` to abort without involving session files. |
| **Differential report comparison** | OpenDoor can compare a previous and current SQLite/JSON report with `--diff old:new`, showing added, removed, and changed findings without rescanning the target. This turns scan reports into release-to-release exposure regression checks. |
| **CI/CD-ready results** | OpenDoor can return a failing exit code only when selected result buckets are found, making it usable as a release gate or exposure regression check without custom post-processing scripts. |
| **Auditable engineering** | OpenDoor is maintained with multi-platform CI, coverage checks, package checks, documentation builds, and a large unittest suite, making it easier to audit, contribute to, and depend on. |

## 🧬 Recognized technologies

OpenDoor includes a heuristic fingerprint engine for detecting probable application stacks, CMS platforms, frameworks, site builders, static-site tooling, infrastructure providers, HSTS / preload readiness, and WAF / anti-bot systems.

| Category                   | Examples |
|----------------------------|---|
| CMS                        | WordPress, Drupal, Joomla, TYPO3, GravCMS, Open Journal Systems, InstantCMS, DiafanCMS, CMS.S3 / Megagroup, Discuz!, NetCat |
| E-commerce                 | Magento, WooCommerce, Shopify, PrestaShop, OpenCart, Shopware, Webasyst / Shop-Script |
| Frameworks / app platforms | Laravel, Symfony, Django, Flask, FastAPI, Express, NestJS, Next.js, Nuxt, Rails, Spring |
| Runtime / language stack   | PHP, Node.js, JavaScript, Python, Ruby, .NET, Java/JVM, Elixir, static-site targets |
| Site builders              | Wix, Webflow, Squarespace, Tilda, Duda, Hostinger Website Builder |
| Static / docs generators   | MkDocs, Docusaurus, Hugo, Jekyll, VitePress |
| Infrastructure / hosting   | Cloudflare, AWS, Vercel, Netlify, GitHub Pages, GitLab Pages, Heroku, Azure, Google Cloud, Fastly, Akamai, Hostinger, DDoS-Guard, Tencent Cloud |
| Infrastructure / servers   | Nginx, Apache HTTP Server, Microsoft IIS, Caddy, LiteSpeed, lighttpd, Tornado, Gunicorn, Uvicorn, Hypercorn, Waitress, Apache Tomcat, Eclipse Jetty, Envoy, Traefik |
| WAF / anti-bot             | Cloudflare, AWS WAF, Azure Front Door, Akamai, Imperva, Sucuri, ModSecurity, DataDome, Kasada, BunkerWeb, F5 BIG-IP ASM |
| Security headers           | HSTS presence, max-age, includeSubDomains, preload directive, local preload readiness |

Full list of supported technologies:
[Fingerprinting technologies](https://opendoor.readthedocs.io/detection/fingerprinting)

Run fingerprint detection:

```bash
opendoor --host https://example.com --fingerprint
```

After the fingerprint pass finishes, OpenDoor prints a compact pre-scan summary before dictionary enumeration starts:

```text
Fingerprint result: cms/WordPress (95%)
Web stack: WordPress | PHP | Cloudflare
Security posture: HSTS preload-ready
```

Read more:

- [Fingerprinting guide](https://opendoor.readthedocs.io/detection/fingerprinting/)
- [WAF detection guide](https://opendoor.readthedocs.io/detection/waf-detection/)

## 📦 Installation

### pipx

Recommended for most CLI users:

```bash
pipx install opendoor
```

### pip

```bash
python3 -m pip install --upgrade opendoor
```

### Arch Linux / AUR

OpenDoor is available in the Arch User Repository:

```bash
yay -S opendoor
```

### Homebrew

OpenDoor is also available in the Brew package manager:

```bash
brew install opendoor
```

### Docker

OpenDoor is available as an official project Docker image via GitHub Container Registry.

```bash
docker pull ghcr.io/stanislav-web/opendoor:latest
docker run --rm -it ghcr.io/stanislav-web/opendoor:latest --version
```

Run a scan and write reports to the host:

```bash
mkdir -p reports

docker run --rm \
  -v "$PWD/reports:/work/reports" \
  ghcr.io/stanislav-web/opendoor:latest \
  --host https://example.com \
  --reports json,html \
  --reports-dir reports
```

### BlackArch Linux

OpenDoor is available in BlackArch Linux:

```bash
sudo pacman -Syu
sudo pacman -S opendoor
```

### From source

```bash
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor

python3 -m pip install -r requirements.txt
python3 opendoor.py --help
```

See the full [installation guide](https://opendoor.readthedocs.io/Installation-and-update/).

---

## 🚀 Quick usage

### Basic directory scan

```bash
opendoor --host https://example.com
```

### Crawl same-origin links

```bash
opendoor --host https://example.com --crawl
```

`--crawl` is opt-in and only works with directory scans. It uses `GET`, extracts conservative HTML attributes from already scanned responses, keeps same-origin URLs only, respects ignored extensions, skips POST forms and external origins, and reports discovered URLs through the normal result buckets.

### Subdomain scan

```bash
opendoor --host example.com --scan subdomains
```

### Target list

```bash
opendoor --hostlist targets.txt
```

Target files may mix URLs, domains, IPv4 addresses, IPv4 CIDR blocks, and inclusive IPv4 ranges:

```text
https://example.com
app.example.com
192.168.1.10
192.168.1.0/24
192.168.1.10-192.168.1.50
```

### Standard input

```bash
cat targets.txt | opendoor --stdin
```

The same mixed target format is supported through STDIN.

### Low-noise scan

```bash
opendoor \
  --host https://example.com \
  --method GET \
  --auto-calibrate \
  --include-status 200-299,301,302,403 \
  --exclude-status 404,429,500-599 \
  --exclude-size-range 0-256 \
  --sniff endpoint,secret,shadow,openredirect,malware,skipempty,collation,indexof,file,stacktrace \
  --reports std,json,csv,sarif
```

### Response sniffers

Response sniffers classify interesting response bodies during discovery. They are useful when status code and size are not enough to understand what was found.

```bash
opendoor \
  --host https://example.com \
  --method GET \
  --sniff endpoint,secret,shadow,openredirect,malware,stacktrace,indexof,file,collation \
  --reports std,json,csv,html,sqlite,sarif
```

Useful sniffers include:

| Sniffer             | Purpose                                                                                                                             |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| `indexof`           | Detect directory listing pages.                                                                                                     |
| `file`              | Detect known sensitive file exposure patterns.                                                                                      |
| `collation`         | Detects repeated or redirect-like fallback responses that can create false positives.                                               |
| `skipempty`         | Skip empty responses.                                                                                                               |
| `skipsizes=46`      | Skip responses with exact known noisy sizes.                                                                                        |
| `skipsizes=46:1024` | Skip responses inside a noisy size range.                                                                                           |
| `stacktrace`        | Detect exposed debug/runtime stack traces and internal error details.                                                               |
| `secret`            | Detect possible exposed API keys, tokens, private keys and credentials with redacted report metadata.                               |
| `shadow`            | Actively probe confirmed `200 OK` file-like hits for bounded backup/shadow variants such as `.bak`, `.old`, and path templates . |
| `openredirect`      | Actively verify redirect-like query parameters with controlled marker URLs and report only confirmed open redirect vulnerabilities. |
| `endpoint`          | Passively detect client-exposed WebSocket, Socket.IO, SSE/EventSource and AJAX endpoints from already-fetched responses.                       |
| `malware`           | Detect possible malicious content, webshell markers, injected scripts or obfuscated payloads.                                       |

Body-dependent sniffers automatically force `GET` internally when the configured method is `HEAD`.

Read more: [Sniffers reference](https://opendoor.readthedocs.io/Sniffers/)

### Authenticated scan from raw request

```bash
opendoor \
  --raw-request request.txt \
  --scheme https \
  --method GET \
  --auto-calibrate \
  --reports json,html,sqlite,sarif
```

### WAF-safe scan

```bash
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --timeout 60 \
  --retries 5 \
  --delay 0.5
```

### Fault-tolerant scan

Use a more conservative runtime profile for unstable targets, slow networks, temporary WAF blocks, proxy instability, or long-running authorized scans.

```bash
opendoor \
  --host https://example.com \
  --method GET \
  --timeout 60 \
  --retries 5 \
  --retries-fail-streak 25 \
  --auto-calibrate \
  --waf-detect \
  --waf-guard \
  --session-save session.json \
  --reports std,json,html
```

This profile makes scans more resilient by increasing per-request timeout and retry tolerance, limiting aborts to repeated exhausted paths, filtering soft-404 and catch-all responses with auto-calibration, stopping low-value scans when WAF-blocked responses dominate, and saving checkpoint state for later resume.

Resume the scan later:

```bash
opendoor --session-load session.json
```

During an active scan, press `Ctrl+C` once to pause workers, then choose `C` to continue or `E` to abort.

### Header and path bypass probes

Use this only on systems you are authorized to test. The feature is opt-in and probes blocked resources with controlled temporary headers and safe path variants.

```bash
opendoor \
  --host https://example.com \
  --method GET \
  --waf-detect \
  --header-bypass \
  --header-bypass-limit 32 \
  --reports std,json,csv,sarif,sqlite
```
When --header-bypass is enabled, OpenDoor first tries configured header-injection variants and then safe path-manipulation variants such as trailing slash, dot segment, semicolon suffix, case variation, and URL-encoded segment.
Customize trigger statuses, trusted IP values, and headers:

```bash
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass \
  --header-bypass-status 401,403 \
  --header-bypass-ips 127.0.0.1,10.0.0.1 \
  --header-bypass-headers X-Original-URL,X-Rewrite-URL,X-Forwarded-For,X-Real-IP \
  --reports json,html,sqlite,sarif,csv
```

### Proxy routing

Use a single explicit proxy:

```bash
opendoor --host https://example.com --proxy socks5://127.0.0.1:9050
```

Use the bundled rotating proxy pool:

```bash
opendoor --host https://example.com --proxy-pool
```

Use a custom rotating proxy list:

```bash
opendoor --host https://example.com --proxy-list proxies.txt
```

### OpenVPN transport

```bash
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn
```

If OpenVPN is installed outside `PATH`, pass the backend explicitly:

```bash
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn \
  --transport-bin /opt/homebrew/sbin/openvpn
```

On Windows, `--transport-bin` can point to `C:\Program Files\OpenVPN\bin\openvpn.exe`. If a GUI client or corporate VPN agent already owns the tunnel, start that VPN outside OpenDoor and run OpenDoor in direct mode.

### WireGuard transport

```bash
opendoor \
  --host https://example.com \
  --transport wireguard \
  --transport-profile ./profile.conf
```

More examples:

- [Basic scans](https://opendoor.readthedocs.io/examples/basic-scans/)
- [Batch scans](https://opendoor.readthedocs.io/examples/batch-scans/)
- [Authenticated scans](https://opendoor.readthedocs.io/examples/authenticated-scans/)
- [WAF-safe scans](https://opendoor.readthedocs.io/examples/waf-safe-scans/)
- [Header-bypass scans](https://opendoor.readthedocs.io/examples/header-bypass-scans/)
- [VPN transport scans](https://opendoor.readthedocs.io/examples/vpn-transport-scans/)
- [CI/CD examples](https://opendoor.readthedocs.io/examples/ci-cd/)

---

### Differential report comparison

OpenDoor can compare exactly two previous/current reports without running a new scan. Use this when you want to see what appeared, disappeared, or changed between two authorized scan results.

Supported input pairs are SQLite-to-SQLite and JSON-to-JSON only. Mixed formats, missing files, invalid reports, and unsupported report types fail with a graceful validation error.

```bash
opendoor --diff reports/baseline/example.com.sqlite:reports/current/example.com.sqlite --reports std,json
opendoor --diff reports/baseline/example.com.json:reports/current/example.com.json --reports std,json --reports-dir ./diff
```

### SARIF reports for CI/CD

OpenDoor can export findings as SARIF 2.1.0 for GitHub Code Scanning and SARIF-compatible security pipelines.

```bash
opendoor \
  --host https://example.com \
  --reports sarif,json \
  --reports-dir ./reports
```

GitHub Actions upload example:

```yaml
- name: Upload OpenDoor SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: reports/example.com/example.com.sarif
    category: opendoor
```
---

## 🎓 Mastering OpenDoor

Hands-on article series for learning OpenDoor through reproducible, authorized web reconnaissance workflows.

![OpenDoor](https://raw.githubusercontent.com/stanislav-web/OpenDoor/master/examples/screenshots/cli.png)

- [Part 1 — Context-Aware Web Recon Beyond Directory Brute Force](https://medium.com/@stanisov/mastering-opendoor-context-aware-web-recon-beyond-directory-brute-force-part-1-cc13eda8cd3d)
- [Part 2 — Low-Noise Recon with Redirects, Endpoint Sniffing, and Bounded Crawl](https://medium.com/@stanisov/mastering-opendoor-low-noise-recon-with-redirects-endpoint-sniffing-and-bounded-crawl-part-2-411b92675d6d)
- [Series companion page](https://opendoor.readthedocs.io/guides/mastering-opendoor/)

## 📚 Documentation

The full documentation is available on ReadTheDocs:

- [Home](https://opendoor.readthedocs.io/)
- [Quickstart](https://opendoor.readthedocs.io/quickstart/)
- [Installation and update](https://opendoor.readthedocs.io/Installation-and-update/)
- [Usage guide](https://opendoor.readthedocs.io/Usage/)
- [Target input](https://opendoor.readthedocs.io/concepts/target-input/)
- [Reports](https://opendoor.readthedocs.io/concepts/reports/)
- [Fingerprinting](https://opendoor.readthedocs.io/detection/fingerprinting/)
- [WAF detection and safe mode](https://opendoor.readthedocs.io/detection/waf-detection/)
- [WAF guard](https://opendoor.readthedocs.io/detection/waf-guard/)
- [Header Injection Bypass](https://opendoor.readthedocs.io/detection/header-bypass/)
- [Auto-calibration](https://opendoor.readthedocs.io/detection/auto-calibration/)
- [Network transports](https://opendoor.readthedocs.io/transports/overview/)
- [OpenVPN transport](https://opendoor.readthedocs.io/transports/openvpn/)
- [WireGuard transport](https://opendoor.readthedocs.io/transports/wireguard/)
- [Practical examples](https://opendoor.readthedocs.io/examples/basic-scans/)
- [Testing](https://opendoor.readthedocs.io/Testing/)
- [Contribution](https://opendoor.readthedocs.io/Contribution/)

---

## 🧪 Development

Install development dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

Run tests:

```bash
python -m unittest
```

Run coverage:

```bash
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m
```

Build documentation:

```bash
python3 -m venv .docs-venv
source .docs-venv/bin/activate
python -m pip install -r docs/requirements.txt
python -m mkdocs build --strict
```

Build package artifacts:

```bash
python -m build
```

See the full [testing guide](https://opendoor.readthedocs.io/Testing/) and [contribution guide](https://opendoor.readthedocs.io/Contribution/).

---

## 🔐 Security and secret hygiene

Do not commit real secrets or private transport profiles.

Never publish:

- real OpenVPN profiles;
- WireGuard private keys;
- auth-user-pass files;
- cookies;
- bearer tokens;
- customer target lists;
- private scan reports;
- sensitive CI artifacts.

Use placeholder examples only.

---

## ⚖️ Responsible use

OpenDoor is a security testing tool.

Use it only against systems you own or have explicit permission to test.

Features such as WAF detection, WAF-safe scanning, raw request replay, transport profiles, and Header Injection Bypass probes are intended for authorized security testing, defensive validation, and exposure regression checks.

The project does not grant permission to scan third-party systems, organizations, commercial services, or public infrastructure without authorization.

---

## 🧾 Changelog

See [CHANGELOG.md](CHANGELOG.md) and [GitHub Releases](https://github.com/stanislav-web/OpenDoor/releases).

---

## 🤝 Contributing

Pull requests are welcome.

Before contributing, read the [contribution guide](https://opendoor.readthedocs.io/Contribution/) and run the relevant tests.
OpenDoor improves through code contributions, documentation updates, testing, issue reports, security feedback, feature ideas, and community validation.
Thanks to everyone who has helped improve the project.

[![Contributors](https://contrib.rocks/image?repo=stanislav-web/OpenDoor)](https://github.com/stanislav-web/OpenDoor/graphs/contributors)

---

## 📄 License

OpenDoor is released under the GNU General Public License v3.0 only.

See [LICENSE](LICENSE).

---

## Support

If OpenDoor helps your authorized security work, you can support ongoing maintenance through Giveth.

[Support OpenDoor on Giveth](https://giveth.io/project/opendoor)

---
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/stanislav-web/OpenDoor) [![License: GPL v3](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
