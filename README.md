# OpenDoor — OWASP Web Directory Scanner

![OpenDoor](https://raw.githubusercontent.com/stanislav-web/OpenDoor/master/logo.png)

**OpenDoor** is an open-source CLI scanner for authorized web reconnaissance, directory discovery, subdomain enumeration, fingerprint detection, WAF detection, controlled header-bypass probing, response filtering, reporting, and transport-based scanning workflows.

It helps security researchers, penetration testers, bug bounty hunters, DevSecOps engineers, and developers identify exposed paths, login panels, directory listings, restricted resources, backup files, web shells, subdomains, and other potentially sensitive web assets.

> Use OpenDoor only on systems you own or have explicit permission to test.

---

## ✅ Project status

[![PyPI version](https://img.shields.io/pypi/v/opendoor)](https://pypi.org/project/opendoor/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-green.svg)](https://www.python.org/)
[![Documentation Status](https://app.readthedocs.org/projects/opendoor/badge/?version=latest)](https://opendoor.readthedocs.io/)
[![Docker Image](https://github.com/stanislav-web/OpenDoor/actions/workflows/docker-image.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/docker-image.yml)
[![License: GPL v3](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

[![Coverage](https://codecov.io/github/stanislav-web/OpenDoor/graph/badge.svg?token=dyBxutYBso)](https://codecov.io/github/stanislav-web/OpenDoor)
[![CodeQL](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/stanislav-web/OpenDoor/actions/workflows/github-code-scanning/codeql)
[![Dependency Review](https://github.com/stanislav-web/OpenDoor/actions/workflows/dependency-review.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/dependency-review.yml)
[![Codacy Security Scan](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml/badge.svg?branch=master)](https://github.com/stanislav-web/OpenDoor/actions/workflows/codacy.yml)

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
- [Docker image](https://github.com/users/stanislav-web/packages/container/package/opendoor)
- [AUR package](https://aur.archlinux.org/packages/opendoor)
- [BlackArch package](https://blackarch.org/webapp.html)
- [Issues](https://github.com/stanislav-web/OpenDoor/issues)

---

## ✨ Features

- directory discovery;
- recursive directory discovery;
- subdomain enumeration;
- multi-threading scans;
- single target, target file, stdin, IPv4 CIDR, and IPv4 range input modes;
- custom wordlists, prefixes, and extension filters;
- custom request headers, cookies, and raw HTTP request templates;
- response filters by status, size, text, regex, and body length;
- smart auto-calibration for soft-404, wildcard, catch-all, semantic response-diff, and DNS wildcard cases;
- technology fingerprint detection CMS, ecommerce platforms, frameworks;
- passive WAF detection and WAF-safe scan mode;
- controlled header and path bypass probes for blocked `401` and `403` resources;
- resumable scan sessions with checkpoint autosave;
- CI/CD fail-on result bucket rules;
- official Docker image distribution via GitHub Container Registry;
- reports in terminal, text, JSON, CSV, HTML, and SQLite formats;
- proxy, OpenVPN, and WireGuard transport profiles;
- sequential per-target transport rotation for batch workflows;
- configuration wizard for repeatable scan profiles.
- built-in wordlists

---

## 🧭 Where does OpenDoor make sense?

It is designed for real targets where speed alone is not enough: WAFs, CDNs, soft-404 pages, wildcard routes, restricted resources, authenticated areas, unstable networks, multi-target batches, and transport-controlled scans.
OpenDoor focuses on **context-aware discovery** instead of blind enumeration.

### What makes OpenDoor different

| Capability | Why it matters |
|---|---|
| **Fingerprint-first scanning** | OpenDoor can identify probable CMS platforms, frameworks, infrastructure providers, and WAF signals before deeper discovery. This helps you scan with context instead of blindly throwing a generic wordlist at the target. |
| **WAF-aware behavior** | OpenDoor can detect probable WAF / anti-bot behavior and switch to a safer runtime profile with `--waf-safe-mode`, reducing noisy blocked scans and making defensive responses easier to understand. |
| **Controlled bypass evidence** | OpenDoor can optionally probe blocked `401` and `403` resources with controlled header-injection and path-manipulation variants. It records exact evidence such as bypass type, header or path variant, probe value, original status code, and resulting status code without mutating global scan headers. |
| **Multi-signal auto-calibration** | OpenDoor does not rely only on status code or response size. It compares multiple response signals such as body hashes, visible text, semantic soft-404 phrases, DOM-token structure, titles, redirects, stable headers, word count, line count, text density, normalized dynamic tokens, and DNS wildcard baselines to reduce soft-404 and wildcard false positives. |
| **Transport-level workflows** | OpenDoor supports direct, proxy, OpenVPN, and WireGuard transport modes. It can also rotate transport profiles per target in authorized batch scans, which is not the same as manually starting a VPN before running a scanner. |
| **Resumable long scans** | OpenDoor can save scan checkpoints and resume later. This matters when scans are interrupted by crashes, unstable networks, blocked routes, terminal disconnects, or long multi-target jobs. |
| **CI/CD-ready results** | OpenDoor can return a failing exit code only when selected result buckets are found, making it usable as a release gate or exposure regression check without custom post-processing scripts. |
| **Auditable engineering** | OpenDoor is maintained with multi-platform CI, coverage checks, package checks, documentation builds, and a large unittest suite, making it easier to audit, contribute to, and depend on. |

## 🧬 Recognized technologies

OpenDoor includes a heuristic fingerprint engine for detecting probable application stacks, CMS platforms, frameworks, site builders, static-site tooling, infrastructure providers, and WAF / anti-bot systems.

| Category | Examples |
|---|---|
| CMS | WordPress, Drupal, Joomla, TYPO3, Open Journal Systems, InstantCMS, CMS.S3 / Megagroup, Discuz!, NetCat |
| E-commerce | Magento, WooCommerce, Shopify, PrestaShop, OpenCart, Shopware, Webasyst / Shop-Script |
| Frameworks / app platforms | Laravel, Symfony, Django, Flask, FastAPI, Express, NestJS, Next.js, Nuxt, Rails, Spring |
| Site builders | Wix, Webflow, Squarespace, Tilda, Duda, Hostinger Website Builder |
| Static / docs generators | MkDocs, Docusaurus, Hugo, Jekyll, VitePress |
| Infrastructure / hosting | Cloudflare, AWS, Vercel, Netlify, GitHub Pages, GitLab Pages, Heroku, Azure, Google Cloud, Fastly, Akamai, Hostinger, DDoS-Guard, Tencent Cloud |
| WAF / anti-bot | Cloudflare, AWS WAF, Azure Front Door, Akamai, Imperva, Sucuri, ModSecurity, DataDome, Kasada, F5 BIG-IP ASM |

Full list of supported technologies:
[Fingerprinting technologies](https://opendoor.readthedocs.io/detection/fingerprinting)

Run fingerprint detection:

```bash
opendoor --host https://example.com --fingerprint
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

When the Homebrew formula is available:

```bash
brew install opendoor
```

### Docker

OpenDoor is available as an official project Docker image via GitHub Container Registry.

```bash
docker pull ghcr.io/stanislav-web/opendoor:latest
docker run --rm ghcr.io/stanislav-web/opendoor:latest --version
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
  --sniff skipempty,collation,indexof,file \
  --reports std,json,csv,sarif
```

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

---

## 📄 License

OpenDoor is released under the GNU General Public License v3.0 only.

See [LICENSE](LICENSE).

---

## Support

If OpenDoor helps your authorized security work, you can support ongoing maintenance through Giveth.

[Support OpenDoor on Giveth](https://giveth.io/project/opendoor)

---
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/stanislav-web/OpenDoor)



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
