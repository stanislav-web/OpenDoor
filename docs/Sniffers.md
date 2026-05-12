# 🔍 Sniffers

Sniffers are built-in response analysis plugins used to reduce false positives and classify interesting responses during directory discovery.

They are configured with:

```shell
opendoor --host https://example.com --sniff <plugins>
```

Multiple sniffers can be combined with commas:

```shell
opendoor --host https://example.com --sniff malware,secret,shadow,openredirect,stacktrace,skipempty,file,collation,indexof
```

Some sniffers accept parameters:

```shell
opendoor --host https://example.com --sniff skipsizes=24:41:50
```

---

## 🧭 When to use sniffers

Use sniffers when the target returns noisy or repetitive responses.

Common cases:

| Case | Useful sniffer |
|---|---|
| Empty success pages | `skipempty` |
| Known false-positive response sizes | `skipsizes` |
| Directory listings | `indexof` |
| Large downloadable files | `file` |
| Possible leaked API keys, tokens, private keys or credentials | `secret` |
| Possible malicious content, webshell markers, injected scripts or obfuscated payloads | `malware` |
| Exposed backup or shadow copies near confirmed files | `shadow` |
| Exposed debug stack traces or verbose error details | `stacktrace` |
| Redirect parameters that may accept arbitrary external targets | `openredirect` |
| Redirect-like or duplicated fallback responses | `collation` |

Sniffers are especially useful when combined with response filters and auto-calibration.

---

## 🧩 Sniffers vs filters vs auto-calibration

OpenDoor has several layers for response classification.

| Layer | Purpose |
|---|---|
| Response filters | Explicit user-defined rules, such as status, size, text, and regex filters. |
| Sniffers | Built-in heuristics and bounded active probes for common false positives and interesting response types. |
| Auto-calibration | Baseline-based classification for soft-404, wildcard, and catch-all responses. |

A practical low-noise scan often uses all three:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --auto-calibrate \
  --exclude-status 404,429,500-599 \
  --exclude-size-range 0-256 \
  --sniff malware,secret,shadow,openredirect,stacktrace,skipempty,file,collation,indexof
```

---

## 🧼 `skipempty`

Skips empty or blank responses.

```shell
opendoor --host https://example.com --sniff skipempty
```

Use it when the target returns successful HTTP statuses with an empty response body.

Example:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff skipempty
```

`skipempty` is useful for removing blank success pages that do not represent real content.

---

## 📏 `skipsizes`

Skips responses with known false-positive body sizes.

```shell
opendoor --host https://example.com --sniff skipsizes=24:41:50
```

The value is a colon-separated list of response sizes.

Use it when a target returns the same body size for many invalid paths.

Example workflow:

1. Run a small scan.
2. Identify repetitive false-positive response sizes.
3. Add those sizes to `skipsizes`.

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff skipsizes=24:41:50
```

For wider ranges, prefer response filters:

```shell
opendoor --host https://example.com --exclude-size-range 0-256,1024-2048
```

---

## 📂 `indexof`

Detects directory listing pages.

```shell
opendoor --host https://example.com --sniff indexof
```

Directory listings often expose files, backups, logs, generated assets, or deployment artifacts.

Example:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff indexof
```

Use this sniffer when you want OpenDoor to highlight directory index pages such as:

```text
Index of /
Index of /backup/
Index of /uploads/
```

---

## 📦 `file`

Detects responses that look like downloadable or interesting files.

```shell
opendoor --host https://example.com --sniff file
```

Use it when you want to identify assets such as archives, backups, dumps, logs, database exports, or other non-HTML resources.

Example:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff file
```

This sniffer is useful when scanning wordlists that include file names or backup extensions.

---


## 🔐 `secret`

Detects possible exposed secrets in successful textual responses.

```shell
opendoor --host https://example.com --sniff secret
```

The `secret` sniffer classifies matching `200 OK` responses into the `secret` bucket and attaches a redacted `secret_detection` metadata object to detailed reports. Without `--sniff secret`, the same successful response remains in the normal `success` bucket.

It currently looks for common leak families such as AWS access keys, GitHub tokens, Slack tokens, Stripe keys, Google API keys, JWT-like bearer tokens, private key blocks, database URLs with credentials, and generic key/token/password assignments.

Report metadata is intentionally redacted. OpenDoor stores the secret type, confidence, match count, matched type list and redacted preview, but not the raw secret value.

Example:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff malware,secret,shadow,stacktrace,indexof,file \
  --reports std,json,csv,html,sqlite,sarif
```

If the requested method is `HEAD`, OpenDoor overrides it to `GET` when `secret` is selected because this sniffer needs response body analysis.

```shell
opendoor \
  --host https://example.com \
  --auto-calibrate \
  --sniff malware,secret,shadow,stacktrace,skipempty,collation,indexof,file
```

---

## 🧬 `malware`

Passively detects suspicious malware and webshell indicators in successful textual responses.

```shell
opendoor --host https://example.com --sniff malware
```

The `malware` sniffer classifies matching responses into the `malware` bucket and attaches a `malware_detection` metadata object to detailed reports. WebShell and Malware findings are intentionally reported under the same `Malware` runtime marker and bucket, while subtype details are preserved in metadata.

It currently looks for high-signal content patterns such as:

- webshell family markers and file-manager panels;
- PHP command-execution constructs wired to request parameters;
- suspicious obfuscation clusters such as encoded payload loaders;
- injected iframe or script payload patterns;
- browser-side crypto-miner indicators.

Example:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff malware,secret,shadow,stacktrace,indexof,file \
  --reports std,json,csv,html,sqlite,sarif
```

If the requested method is `HEAD`, OpenDoor overrides it to `GET` when `malware` is selected because this sniffer needs response body analysis.

```shell
opendoor \
  --host https://example.com \
  --auto-calibrate \
  --sniff malware,secret,shadow,stacktrace,skipempty,collation,indexof,file
```

---

## 🕵️ `shadow`

Actively probes for exposed backup/shadow copies next to confirmed successful files.

```shell
opendoor --host https://example.com --method GET --sniff shadow
```

Unlike passive body-only sniffers, `shadow` generates a bounded set of postfix candidates only after OpenDoor has already found a `200 OK` file-like response. For example, a confirmed `/index.php` hit can trigger probes such as `/index.php.bak`, `/index.php.old` etc.
A candidate is classified into the `shadow` bucket only when the probe is successful and the normalized response content matches the original base file. Matching findings include `shadow_detection` metadata such as base URL, suffix variant, confidence, reason and size comparison.

Example:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff shadow,malware,secret,stacktrace,indexof,file \
  --reports std,json,csv,html,sqlite,sarif
```

Use `shadow` when developers may accidentally deploy old, backup or editor-created copies of application files across PHP, Python, Node.js or mixed stacks.

---

## 🔁 `openredirect`

Actively verifies redirect-like query parameters with controlled external marker values.

```shell
opendoor --host https://example.com --method GET --sniff openredirect
```

Unlike a passive external-redirect detector, `openredirect` reports only confirmed open redirect vulnerabilities. It builds bounded verification requests from discovered URLs that already contain redirect-like query parameters such as `next`, `redirect`, `redirect_uri`, `returnUrl`, `continue`, `callback`, `target`, `destination`, `goto`, `to`, `r`, `u`, or `RelayState`.

For example, a discovered URL such as:

```text
https://example.com/login?returnUrl=/profile
```

can be verified with controlled marker targets such as:

```text
https://example.com/login?returnUrl=https%3A%2F%2Fopendoor.invalid%2F
```

A finding is created only when the target responds with a redirect status and a `Location` header pointing to the marker host:

```text
302 Location: https://opendoor.invalid/
```

OpenDoor does not need to own `opendoor.invalid` and does not follow the external redirect. The marker is used only as evidence that the endpoint accepted an arbitrary external redirect target.

Matching findings are classified into the `openredirect` bucket and include `openredirect_detection` metadata such as source URL, probe URL, parameter, payload, variant, marker host, confirmed Location header and confidence.

Example:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff openredirect,malware,secret,stacktrace,indexof,file \
  --reports std,json,csv,html,sqlite,sarif
```

---

## 🧯 `stacktrace`

Detects exposed debug stack traces and verbose internal error details.

```shell
opendoor --host https://example.com --sniff stacktrace
```

The `stacktrace` sniffer classifies matching responses into the `stacktrace` bucket and attaches a `stacktrace_detection` metadata object to detailed reports.
It is useful for fingerprinting runtime leaks in error responses, including Python, Node.js, NestJS, PHP, Java and SQL error patterns.

Example:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff malware,secret,shadow,stacktrace,indexof,file \
  --reports std,json,csv,html,sqlite,sarif
```

If the requested method is `HEAD`, OpenDoor overrides it to `GET` when `stacktrace` is selected because this sniffer needs response body analysis.

```shell
opendoor \
  --host https://example.com \
  --auto-calibrate \
  --sniff malware,secret,shadow,stacktrace,skipempty,collation,indexof,file
```

---

## 🔀 `collation`

Detects repeated or redirect-like fallback responses that can create false positives.

```shell
opendoor --host https://example.com --sniff collation
```

Use it when the target appears to return visually similar or structurally repeated pages for many invalid paths.

Example:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff collation
```

For modern targets with soft-404 behavior, `collation` usually works best together with auto-calibration:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --auto-calibrate \
  --sniff collation
```

---

## 🧪 Common combinations

### General low-noise scan

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --auto-calibrate \
  --sniff malware,secret,shadow,openredirect,stacktrace,skipempty,file,collation,indexof
```

### Known false-positive sizes

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff skipempty,skipsizes=24:41:50
```

### Directory listing focused scan

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --sniff indexof,file
```

### Batch scan with sniffers

```shell
opendoor \
  --hostlist targets.txt \
  --method GET \
  --auto-calibrate \
  --sniff shadow,openredirect,malware,skipempty,file,collation,indexof \
  --reports json,sqlite
```

---

## ⚙️ Recommended usage

For most modern targets:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --auto-calibrate \
  --sniff malware,secret,shadow,openredirect,stacktrace,skipempty,file,collation,indexof
```

For fast scans where response body analysis is not required, keep the default request method and use status/size filters instead.

---

## 🧯 Troubleshooting

### Too many false positives

Add auto-calibration and stricter filters:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --auto-calibrate \
  --exclude-status 404,429,500-599 \
  --exclude-size-range 0-256 \
  --sniff skipempty,collation
```

### Missing interesting body matches

Use `GET` instead of `HEAD`:

```shell
opendoor --host https://example.com --method GET --sniff indexof,file
```

Body-based analysis is more useful with `GET` requests.

### Known repetitive page size

Use `skipsizes` for exact sizes:

```shell
opendoor --host https://example.com --sniff skipsizes=1234:5678
```

Use `--exclude-size-range` for ranges:

```shell
opendoor --host https://example.com --exclude-size-range 1000-2000
```

---

## ✅ Summary

| Sniffer                | Purpose                                                          |
|------------------------|------------------------------------------------------------------|
| `skipempty`            | Skip empty or blank responses                                    |
| `skipsizes=NUM:NUM...` | Skip known false-positive body sizes                             |
| `indexof`              | Detect directory listing pages                                   |
| `file`                 | Detect downloadable or interesting files                         |
| `collation`            | Detect repeated fallback or redirect-like responses              |
| `stacktrace`           | Detect possible errors in responses                              |
| `secret`               | Detects possible exposed secrets in successful textual responses |
| `malware`              | Detect possible malware, webshell and injected payload indicators |
| `shadow`               | Detect possible archive or backuped files                        |
| `openredirect`         | Verify redirect parameters for confirmed open redirect issues     |
