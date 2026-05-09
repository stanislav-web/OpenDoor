# 🧩 Header Injection Bypass

Header Injection Bypass is an opt-in OpenDoor feature for authorized testing of blocked `401` and `403` resources, plus WAF-classified blocked responses when WAF detection or WAF-safe mode is enabled.

It sends controlled, temporary per-request headers and records exact evidence when a blocked response changes to a meaningful result.

Use it only on systems you own or have explicit permission to test.

---

## Enable Header Injection Bypass

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass
```

By default, OpenDoor probes `401` and `403` responses. When a response is classified as `blocked` by WAF detection, `--header-bypass` can also probe it even if the HTTP status is a WAF/challenge redirect such as `301` or `302`. Regular redirects are not probed unless their status is explicitly added through `--header-bypass-status`.

---

## Recommended WAF-aware usage

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

Use WAF-safe mode, lower thread counts, delays, and longer timeouts for cautious scans of protected authorized targets.

With `--debug 1`, OpenDoor also reports the header-bypass lifecycle: enabled configuration, skipped WAF-blocked responses, probe start, candidate detection, and no-candidate completion. This makes it visible whether `--header-bypass` is active or simply not triggered by the current response.

---

## CLI options

| Option | Purpose |
|---|---|
| `--header-bypass` | Enable controlled header-bypass probes |
| `--header-bypass-profile` | Probe profile: `safe` or `offensive` |
| `--header-bypass-headers` | Comma-separated header names to test |
| `--header-bypass-ips` | Comma-separated trusted IP values for trusted-IP style headers |
| `--header-bypass-status` | Comma-separated status codes or ranges that trigger probes |
| `--header-bypass-limit` | Maximum probe variants per blocked URL; `0` means unlimited |

---

## Offensive profile

The default `safe` profile keeps the stable header family. The `offensive` profile is still opt-in and controlled, but adds extended proxy/CDN/client-IP headers, method-override headers, scheme/HTTPS forwarding headers, and additional trusted IP values. It also benefits from the same path-normalization probes and variant limit.

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --waf-detect \
  --header-bypass \
  --header-bypass-profile offensive \
  --header-bypass-limit 96 \
  --reports std,json,csv,html,sqlite,sarif
```

Use this only on systems you own or have explicit permission to test. Keep a finite limit for normal use; use `--header-bypass-limit 0` only when you intentionally want all generated variants.

---

## Customize trigger statuses

```shell
opendoor \
  --host https://example.com \
  --header-bypass \
  --header-bypass-status 401,403
```

Status ranges are supported:

```shell
opendoor \
  --host https://example.com \
  --header-bypass \
  --header-bypass-status 401-403
```

---

## Customize trusted IP values

```shell
opendoor \
  --host https://example.com \
  --header-bypass \
  --header-bypass-ips 127.0.0.1,10.0.0.1,192.168.1.1
```

These values are used with trusted-IP style headers such as:

- `X-Forwarded-For`;
- `X-Real-IP`;
- `X-Client-IP`;
- `Client-IP`;
- `True-Client-IP`;
- `CF-Connecting-IP`.

---

## Customize tested headers

```shell
opendoor \
  --host https://example.com \
  --header-bypass \
  --header-bypass-headers X-Original-URL,X-Rewrite-URL,X-Forwarded-For,X-Real-IP
```

OpenDoor supports path-based, host/origin, trusted-IP, URL-style, method-override, scheme and HTTPS-forwarding header families. The extended families are available through `--header-bypass-profile offensive` unless you explicitly list them with `--header-bypass-headers`.

---

## Limit probe variants

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

---

## How OpenDoor reports candidates

Successful candidates are stored in the `bypass` result bucket.

Detailed report items include:

| Field | Meaning |
|---|---|
| `bypass` | Bypass type, currently `header` |
| `bypass_header` | Header that produced the candidate |
| `bypass_value` | Header value used for the probe |
| `bypass_from_code` | Original blocked status code |
| `bypass_to_code` | Resulting status code |

Example text report line:

```text
https://example.com/admin - 200 - 90B | bypass=header, header=X-Original-URL, value=/admin, 403->200
```

---

## Report format support

| Report | Header-bypass evidence |
|---|---|
| `std` | Shows the `bypass` bucket in summary statistics |
| `txt` | Includes bypass evidence in bypass report lines |
| `json` | Preserves full metadata in `report_items` |
| `csv` | Adds dedicated bypass columns |
| `html` | Preserves detailed `report_items` metadata |
| `sqlite` | Stores bypass metadata in nullable item columns |

---

## CI/CD gate

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass \
  --reports json,sqlite,csv \
  --fail-on-bucket success,auth,forbidden,bypass
```

The `bypass` bucket can fail a pipeline when header-bypass candidates are found.

---

## Design notes

Header Injection Bypass is implemented as a controlled scanner extension:

- disabled by default;
- temporary headers are applied only to the current probe request;
- global scan headers are not mutated;
- probe generation is deterministic;
- probe count is bounded by `--header-bypass-limit`;
- reports preserve exact evidence.

This feature is not a raw HTTP parser discrepancy engine and is not intended to replace specialized bypass research tools.

---

## Responsible use

Use this feature only for authorized security testing, defensive validation, and exposure regression checks.

Do not use OpenDoor against third-party systems without explicit permission.
