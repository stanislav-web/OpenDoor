# Mastering OpenDoor

Mastering OpenDoor is a practical article series for learning authorized web reconnaissance, context-aware directory discovery, response analysis, and report-driven exposure validation with OpenDoor.

The full articles are intended for Medium. This page is the official companion page for stable commands, lab setup, and responsible-use boundaries.

> Use OpenDoor only on systems you own or have explicit permission to test.

---

## Articles

| Article | Status | Focus |
|---|---|---|
| Part 1 — Context-Aware Discovery | Planned | Installation, first scan, fingerprint-first workflow, response buckets, and basic reports. |
| Part 2 — Low-Noise Recon | Planned | Auto-calibration, response filters, sniffers, WAF-safe scanning, and practical scan profiles. |
| Part 3 — Automation and CI/CD | Planned | JSON, HTML, SQLite, SARIF, fail-on buckets, report diffing, and exposure regression checks. |

Medium links will be added after publication.

---

## Recommended local lab target

Use a local authorized target while following the series.

```shell
http://127.0.0.1:8080
```

Do not scan third-party public systems while reproducing the examples unless you have explicit permission.

---

## Baseline command

```shell
opendoor \
  --host http://127.0.0.1:8080 \
  --fingerprint \
  --reports std,html,json
```

This command is intentionally conservative and suitable for the first article in the series.

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
