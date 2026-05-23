# 🛡️ WAF-safe scans

This page shows cautious scan profiles for authorized targets protected by WAF, CDN, anti-bot, or rate-limiting infrastructure.

---

## Basic WAF detection

```shell
opendoor --host https://example.com --waf-detect
```

---

## Safe mode

```shell
opendoor --host https://example.com --waf-safe-mode
```

Safe mode enables a more cautious scan profile after probable WAF or anti-bot behavior is detected.

---

## WAF-safe low-pressure scan

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --method GET \
  --threads 3 \
  --delay 1 \
  --timeout 60 \
  --retries 5 \
  --retries-fail-streak 10 \
  --auto-calibrate \
  --reports json,html
```

---

## WAF-safe scan with filters

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --method GET \
  --include-status 200-299,301,302,403 \
  --exclude-status 404,429,500-599 \
  --exclude-size-range 0-256 \
  --reports json,sqlite,csv
```

---

## WAF guard early stop

Use WAF guard when a protected target returns WAF-blocked responses for almost every early path and a full wordlist scan would add little value.

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --waf-guard \
  --waf-guard-after 50 \
  --waf-guard-threshold 0.95 \
  --reports json,html
```

For short diagnostics, lower the sample size:

```shell
opendoor \
  --host https://example.com \
  --wordlist ./test.dat \
  --waf-safe-mode \
  --waf-guard \
  --waf-guard-after 3 \
  --waf-guard-threshold 0.95
```

---

## WAF-safe Header Injection Bypass scan

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --waf-detect \
  --waf-safe-mode \
  --threads 3 \
  --delay 1 \
  --timeout 60 \
  --retries 5 \
  --retries-fail-streak 10 \
  --header-bypass \
  --header-bypass-limit 32 \
  --reports json,sqlite,csv
```

Header-bypass probes are temporary per-request headers. They do not mutate global scan headers.

Use this only on systems you are authorized to test.

---

## Custom header-bypass profile

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --waf-safe-mode \
  --header-bypass \
  --header-bypass-status 401,403 \
  --header-bypass-ips 127.0.0.1,10.0.0.1,192.168.1.1 \
  --header-bypass-headers X-Original-URL,X-Rewrite-URL,X-Forwarded-For,X-Real-IP \
  --header-bypass-limit 32 \
  --reports json,html,sqlite
```

---

## WAF-safe CI profile

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --auto-calibrate \
  --header-bypass \
  --reports json,sqlite,csv \
  --fail-on-bucket success,auth,forbidden,bypass
```

---

## Retry-failure abort threshold

For unstable targets, combine `--retries` with `--retries-fail-streak`. `--retries` controls attempts inside one path request. `--retries-fail-streak` controls how many consecutive paths may exhaust those retries before the scan aborts.

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --timeout 60 \
  --retries 5 \
  --retries-fail-streak 10
```

Path-specific exhausted retries are still recorded as skipped/ignored. Any normally processed response resets the consecutive failure counter.

---

## Notes

WAF detection is for classification and safer authorized scanning.

Header Injection Bypass is a separate opt-in validation feature for blocked resources. It records evidence only when a controlled probe changes the response into a meaningful result.

WAF guard is a scan-control feature. It stops early only when primary scan responses are classified as overwhelmingly WAF-blocked. It does not treat plain origin `403` responses as WAF blocks by itself.

Do not treat these examples as bypass guidance for third-party systems.
