# 🛡️ WAF guard

`--waf-guard` is an opt-in stop condition for authorized scans where a WAF, CDN, or anti-bot layer is blocking nearly every early response.

It prevents long low-value scans when OpenDoor has already classified the initial responses as overwhelmingly WAF-blocked.

---

## Enable WAF guard

```shell
opendoor \
  --host https://example.com \
  --waf-guard
```

When enabled, OpenDoor also enables WAF detection internally so that the guard can distinguish probable WAF-blocked responses from ordinary origin `403 Forbidden` responses.

`--waf-guard` does **not** automatically enable `--waf-safe-mode`. Use both when you want cautious request timing and early stop behavior:

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --waf-guard
```

---

## Configure the stop condition

```shell
opendoor \
  --host https://example.com \
  --waf-guard \
  --waf-guard-after 50 \
  --waf-guard-threshold 0.95
```

| Option | Default | Meaning |
|---|---:|---|
| `--waf-guard` | disabled | Enable early stop when initial classified responses are overwhelmingly WAF-blocked. |
| `--waf-guard-after` | `50` | Minimum number of classified primary scan responses before WAF guard can trigger. |
| `--waf-guard-threshold` | `0.95` | WAF-blocked response ratio required to stop the scan. |

The threshold is a ratio from `0.01` to `1.0`.

Examples:

```shell
# Stop when 95% or more of the first 50 classified responses are WAF-blocked.
opendoor --host https://example.com --waf-guard

# Smaller diagnostic sample for a short test wordlist.
opendoor --host https://example.com --waf-guard --waf-guard-after 10

# Require a perfect WAF-block ratio before stopping.
opendoor --host https://example.com --waf-guard --waf-guard-threshold 1.0
```

---

## Console output

When WAF guard is enabled, OpenDoor prints the configured guard condition:

```text
WAF guard enabled: after=50, threshold=95.0%
```

When the condition is reached, OpenDoor stops the scan gracefully:

```text
WAF guard triggered: block ratio is 100.0% after 50 classified responses. Stopping scan.
```

The trigger message means that OpenDoor has classified enough primary scan responses and the WAF-blocked ratio reached the configured threshold.

---

## What WAF guard counts

WAF guard counts only completed **primary scan responses**.

It does not count:

- fingerprint probes;
- auto-calibration probes;
- header-bypass subrequests;
- skipped duplicate URLs;
- ignored URLs;
- ordinary origin `403 Forbidden` responses without WAF classification.

---

## Interaction with other WAF features

### WAF detection

`--waf-guard` requires WAF classification and enables WAF detection internally.

You can still pass `--waf-detect` explicitly for readability:

```shell
opendoor --host https://example.com --waf-detect --waf-guard
```

### WAF safe mode

`--waf-safe-mode` reduces scan pressure. `--waf-guard` decides whether the scan should stop early.

They solve different problems and can be combined:

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --waf-guard \
  --waf-guard-after 50 \
  --waf-guard-threshold 0.95
```

### Header Injection Bypass

`--header-bypass` remains a separate opt-in validation feature.

When both features are enabled, WAF guard can stop the remaining scan after the configured classified-response sample. Header-bypass probes do not inflate the WAF guard sample size.

For short diagnostics, keep the bypass limit small:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --waf-safe-mode \
  --header-bypass \
  --header-bypass-limit 4 \
  --waf-guard \
  --waf-guard-after 10
```

---

## When to use it

Use `--waf-guard` when:

- the first scan responses are repeatedly classified as WAF-blocked;
- a protected target returns the same WAF block page for valid and invalid paths;
- a long wordlist would produce mostly blocked results;
- you want a safe early exit instead of scanning thousands of low-value blocked paths.

Do not use it when your goal is to inventory every blocked path for a report. In that case, keep `--waf-guard` disabled and use `--fail-on-bucket blocked` or report filters instead.

---

## Local diagnostic example

For a small WAF-protected test target:

```shell
CLI_COLOR=0 opendoor \
  --host https://localhost/ \
  --method GET \
  --wordlist ./test.dat \
  --threads 1 \
  --debug 1 \
  --waf-safe-mode \
  --waf-guard \
  --waf-guard-after 3 \
  --waf-guard-threshold 0.95 \
  --reports txt,json,html
```

Expected behavior when every early response is WAF-blocked:

```text
WAF guard enabled: after=3, threshold=95.0%
33.3% [3/9] - 403 - 6KB - WAF: Cloudflare (92%) /uploads
WAF guard triggered: block ratio is 100.0% after 3 classified responses. Stopping scan.
```

---

## Responsible use

WAF guard is a defensive scan-control feature. It is intended to reduce noisy, low-value scans against systems you own or are explicitly authorized to test.
