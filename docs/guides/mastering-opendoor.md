# Mastering OpenDoor

Mastering OpenDoor is a practical article series for learning authorized web reconnaissance, context-aware directory discovery, response analysis, and report-driven exposure validation with OpenDoor.

The full articles are published on Medium. This page is the official companion page for stable commands, lab setup, and responsible-use boundaries.

> Use OpenDoor only on systems you own or have explicit permission to test.

---

## Articles

| Article | Status | Focus |
|---|---|---|
| [Part 1 — Context-Aware Discovery](https://medium.com/@stanisov/mastering-opendoor-context-aware-web-recon-beyond-directory-brute-force-part-1-cc13eda8cd3d) | Published | Local lab setup, first scan, fingerprint-first workflow, response buckets, body-aware sniffers, and HTML/JSON/SARIF reports. |
| Part 2 — Low-Noise Recon | Planned | Auto-calibration, response filters, WAF-safe scanning, and practical scan profiles. |
| Part 3 — Automation and CI/CD | Planned | JSON, HTML, SQLite, SARIF, fail-on buckets, report diffing, and exposure regression checks. |

---

## Recommended local lab target

Use the deterministic local lab from the repository while following the series.

Start the lab in one terminal:

```shell
python examples/mastering-lab/server.py
```

The server listens on:

```text
http://127.0.0.1:8080
```

Use another terminal for OpenDoor commands. Do not scan third-party public systems while reproducing the examples unless you have explicit permission.

---

## Baseline command

```shell
opendoor \
  --host http://127.0.0.1 \
  --port 8080 \
  --method GET \
  --threads 1 \
  --wordlist examples/mastering-lab/wordlist.txt \
  --fingerprint \
  --reports std,html,json \
  --reports-dir reports/mastering-lab
```

This command is intentionally conservative and suitable for the first article in the series.

---

## Low-noise command

```shell
opendoor \
  --host http://127.0.0.1 \
  --port 8080 \
  --method GET \
  --threads 1 \
  --wordlist examples/mastering-lab/wordlist.txt \
  --include-status 200-299,301,401,403,500 \
  --exclude-status 404 \
  --sniff indexof,file,stacktrace,skipempty \
  --reports std,html,json,sarif \
  --reports-dir reports/mastering-lab
```

Use this command after the baseline scan to demonstrate cleaner report output and body-aware response analysis.

---

## What the series covers

- authorized target setup;
- installation and update basics;
- first directory discovery scan;
- fingerprint-first discovery;
- response buckets and signal interpretation;
- auto-calibration and response filtering;
- response sniffers;
- HTML, JSON, SQLite, and SARIF reports;
- CI/CD exposure regression workflows.

---

## What the series avoids

- scanning real third-party targets without authorization;
- publishing cookies, bearer tokens, VPN profiles, or private reports;
- WAF bypass deep dives;
- credential submission;
- exploit payloads;
- aggressive or hidden request-volume behavior.

---

## Publication workflow

Use this page as the stable project-side reference for the Medium series:

1. prepare and validate the local lab commands;
2. publish the full article on Medium;
3. add the Medium link to the table above;
4. keep long explanations on Medium and stable commands in this documentation page.
