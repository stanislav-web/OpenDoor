# 🧩 Header and path bypass scans

This page contains practical bypass examples for authorized testing of blocked resources.

Header-bypass mode is opt-in. It probes blocked resources with temporary per-request headers and safe path-manipulation variants.

---

## Basic header-bypass scan

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass
```

By default, OpenDoor probes `401` and `403` responses.

---

## Header and path probe order

When `--header-bypass` is enabled, OpenDoor tries probes in a controlled order:

1. configured header-injection variants;
2. safe path-manipulation variants.

Path variants include:

- trailing slash;
- double leading slash;
- dot segment;
- semicolon suffix;
- case variation;
- URL-encoded segment.

All successful candidates are stored in the `bypass` bucket.

---

## WAF-aware header-bypass scan

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

Use this profile when testing authorized WAF-protected targets.

---

## Custom statuses and headers

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass \
  --header-bypass-status 401,403 \
  --header-bypass-headers X-Original-URL,X-Rewrite-URL,X-Forwarded-For,X-Real-IP \
  --header-bypass-limit 32 \
  --reports json,html,sqlite
```

---

## Custom trusted IP values

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass \
  --header-bypass-ips 127.0.0.1,10.0.0.1,192.168.1.1 \
  --reports json,csv
```

---

## CI/CD header-bypass gate

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass \
  --reports json,sqlite,csv \
  --fail-on-bucket success,auth,forbidden,bypass
```

The `bypass` bucket can fail the pipeline when candidates are found.

---

## Recommended report formats

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass \
  --reports std,json,csv,sqlite,sarif
```

Use:

- `std` for operator summary;
- `json` for full machine-readable metadata;
- `csv` for stable bypass columns;
- `sqlite` for structured local analysis.
- `sarif` for GitGub cctions.

---

## Report metadata

Header-based candidates may include:

- `bypass=header`;
- `bypass_header`;
- `bypass_value`;
- `bypass_from_code`;
- `bypass_to_code`.

Path-based candidates may include:

- `bypass=path`;
- `bypass_variant`;
- `bypass_value`;
- `bypass_url`;
- `bypass_from_code`;
- `bypass_to_code`.

---

## Notes

- Header-bypass probes are disabled by default.
- Header probes use temporary per-request headers.
- Path probes use temporary probe URLs and do not mutate the original scan target.
- Normal scan headers are not mutated.
- Use `--header-bypass-limit` to keep probe volume controlled.
- Method switching and large payload sets are intentionally deferred.
- Use this only on systems you are authorized to test.
