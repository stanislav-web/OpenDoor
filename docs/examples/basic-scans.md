# 🔎 Basic scans

This page contains small practical examples for everyday OpenDoor usage.

---

## Directory discovery

```shell
opendoor --host https://example.com
```

Equivalent explicit mode:

```shell
opendoor --host https://example.com --scan directories
```

Use this when you want to discover exposed paths, files, panels, backups, and restricted resources.

---

## Subdomain discovery

```shell
opendoor --host example.com --scan subdomains
```

Use a domain name instead of a full URL.

---

## Use a custom wordlist

Local file:

```shell
opendoor --host https://example.com --wordlist ./wordlists/paths.txt
```

Remote HTTP(S) file:

```shell
opendoor --host https://example.com --wordlist https://example.com/wordlists/paths.txt
```

Use custom wordlists when the target stack or application naming patterns are known. Local and remote custom wordlists are marked as `external`; bundled OpenDoor dictionaries are marked as `internal`.

Remote wordlists are downloaded into the managed per-scan temporary workspace before scanning. The same counters, filters, extension handling, and scan progress are used after download. Remote files larger than 500 MB are rejected; download very large wordlists separately and pass the local file path.

---

## Filter by extensions

```shell
opendoor --host https://example.com --extensions php,json,txt
```

This keeps only wordlist entries that already end with the selected extensions.

Short form:

```shell
opendoor --host https://example.com -e php,json,txt
```

---

## Ignore extensions

```shell
opendoor --host https://example.com --ignore-extensions aspx,jsp
```

Short form:

```shell
opendoor --host https://example.com -i aspx,jsp
```

---

## Use GET instead of HEAD

```shell
opendoor --host https://example.com --method GET
```

Use `GET` when you need body-based analysis, text filters, regex filters, fingerprinting context, or body-oriented sniffers.

---

## Add headers

```shell
opendoor --host https://example.com --header "X-Test: 1"
```

Multiple headers can be passed by repeating `--header`:

```shell
opendoor \
  --host https://example.com \
  --header "X-Test: 1" \
  --header "Authorization: Bearer TOKEN"
```

Do not commit real tokens.

---

## Add cookies

```shell
opendoor --host https://example.com --cookie "sid=abc123"
```

Cookies are useful for authorized scans of authenticated areas.

Do not commit real session cookies.

---

## Save reports

```shell
opendoor --host https://example.com --reports std,json,html --reports-dir ./reports
```

Use machine-readable formats for automation:

```shell
opendoor --host https://example.com --reports json,sqlite
```

---

## Low-noise scan

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --auto-calibrate \
  --include-status 200-299,301,302,403 \
  --exclude-status 404,429,500-599 \
  --exclude-size-range 0-256 \
  --sniff skipempty,collation,indexof,file \
  --reports std,json
```

This is a good starting point for modern web applications with custom error pages or wildcard routing.
