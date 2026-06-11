# Mastering OpenDoor

Mastering OpenDoor is a practical article series for learning authorized web reconnaissance, context-aware directory discovery, response analysis, low-noise enrichment, and report-driven exposure validation with OpenDoor.

The full articles are published on Medium. This page is the official companion page for stable commands, lab setup, useful references, and responsible-use boundaries.

> Use OpenDoor only on systems you own or have explicit permission to test.

---

## Articles

| Article | Status | Focus |
|---|---|---|
| [Part 1 — Context-Aware Discovery](https://medium.com/@stanisov/mastering-opendoor-context-aware-web-recon-beyond-directory-brute-force-part-1-cc13eda8cd3d) | Published | Local lab setup, first scan, fingerprint-first workflow, response buckets, body-aware sniffers, and HTML/JSON/SARIF reports. |
| [Part 2 — Low-Noise Recon with Redirects, Endpoint Sniffing, and Bounded Crawl](https://medium.com/@stanisov/mastering-opendoor-low-noise-recon-with-redirects-endpoint-sniffing-and-bounded-crawl-part-2-411b92675d6d) | Published | Redirect classification, passive endpoint discovery, bounded same-origin crawl enrichment, runtime diagnostics, and structured report metadata. |
| Part 3 — Noise Control and Scan Trust | Planned | Auto-calibration, fingerprint detection, WAF-aware scanning, soft-404 and wildcard response handling, and CI/CD-style fail-on rules. |

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

## Part 1 baseline command

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

## Part 1 low-noise response-analysis command

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

## Part 2 bounded crawl and endpoint-sniffing command

```shell
opendoor \
  --host http://127.0.0.1 \
  --port 8080 \
  --method GET \
  --threads 1 \
  --wordlist examples/mastering-lab/wordlist.txt \
  --include-status 200-299,301,302,401,403,500 \
  --exclude-status 404 \
  --sniff endpoint,indexof,file,stacktrace,skipempty \
  --crawl \
  --reports std,html,json,sarif \
  --reports-dir reports/mastering-lab-part-2
```

Use this command to demonstrate bounded same-origin crawl enrichment and passive endpoint extraction from already-fetched response bodies.

The crawl remains controlled: it enriches the queue from same-origin links, scripts, and form actions discovered in fetched HTML responses. It is not an unbounded spider and does not execute JavaScript.

---

## Part 2 redirect-following command

```shell
opendoor \
  --host http://127.0.0.1 \
  --port 8080 \
  --method GET \
  --threads 1 \
  --wordlist examples/mastering-lab/wordlist.txt \
  --include-status 200-399,401,403,500 \
  --exclude-status 404 \
  --follow-redirects \
  --reports std,html,json,sarif \
  --reports-dir reports/mastering-lab-part-2-redirects
```

Use this command when the goal is to classify the final same-host response instead of preserving redirect evidence as the primary finding.

---

## Useful references

- [OpenDoor documentation](https://opendoor.readthedocs.io/)
- [Usage guide](https://opendoor.readthedocs.io/Usage/)
- [Same-origin crawl](https://opendoor.readthedocs.io/Usage/#same-origin-crawl)
- [Sniffers](https://opendoor.readthedocs.io/Sniffers/)
- [Reports and SARIF](https://opendoor.readthedocs.io/concepts/reports/)

---

## What the series covers

- authorized target setup;
- installation and update basics;
- first directory discovery scan;
- fingerprint-first discovery;
- response buckets and signal interpretation;
- response sniffers;
- redirect classification;
- passive endpoint discovery;
- bounded same-origin crawl enrichment;
- runtime diagnostics;
- auto-calibration and response filtering;
- fingerprint detection;
- WAF-aware scanning;
- soft-404 and wildcard response handling;
- HTML, JSON, SQLite, and SARIF reports;
- CI/CD exposure regression workflows.

---

## What the series avoids

- scanning real third-party targets without authorization;
- publishing cookies, bearer tokens, VPN profiles, or private reports;
- WAF bypass deep dives;
- credential submission;
- exploit payloads;
- browser automation;
- proxy-style request replay;
- aggressive or hidden request-volume behavior.

---

## Publication workflow

Use this page as the stable project-side reference for the Medium series:

1. prepare and validate the local lab commands;
2. publish the full article on Medium;
3. add the Medium link to the table above;
4. keep long explanations on Medium and stable commands in this documentation page.
