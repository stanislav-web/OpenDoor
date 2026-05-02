# 📊 Reports

OpenDoor can write scan results in several formats.

Reports are configured with:

```shell
opendoor --host https://example.com --reports std,json,html
```

Use a custom output directory:

```shell
opendoor --host https://example.com --reports json,sqlite --reports-dir ./reports
```

---

## Supported formats

| Format | Purpose |
|---|---|
| `std` | Terminal output |
| `txt` | Plain text output |
| `json` | Machine-readable output |
| `csv` | Spreadsheet-friendly output |
| `html` | Human-readable report |
| `sqlite` | Structured local database for post-processing |
| `sarif` | SARIF 2.1.0 output for CI/CD code scanning |

Use the exact formats shown by:

```shell
opendoor --help
```

because available report plugins can vary by build.

---

## Terminal output

```shell
opendoor --host https://example.com --reports std
```

Use `std` for interactive work.

The terminal summary includes all result buckets, including `bypass` when Header Injection Bypass candidates are found.

---

## Text

```shell
opendoor --host https://example.com --reports txt
```

Use `txt` when you want one plain text file per result bucket.

Header-bypass candidates include evidence in the bypass report lines, for example:

```text
https://example.com/admin - 200 - 90B | bypass=header, header=X-Original-URL, value=/admin, 403->200
```

---

## JSON

```shell
opendoor --host https://example.com --reports json
```

Use JSON for automation, pipelines, post-processing, and CI/CD artifact uploads.

JSON preserves detailed `report_items` metadata, including WAF, fingerprint, calibration, and header-bypass fields.

---

## CSV

```shell
opendoor --host https://example.com --reports csv
```

Use CSV for spreadsheets, simple data analysis, and CI artifacts that need stable columns.

CSV includes dedicated Header Injection Bypass columns:

| Column | Meaning |
|---|---|
| `bypass` | Bypass type, currently `header` |
| `bypass_header` | Header that produced the candidate |
| `bypass_value` | Header value used for the probe |
| `bypass_from_code` | Original blocked status code |
| `bypass_to_code` | Resulting status code |

---

## SARIF

```shell
opendoor --host https://example.com --reports sarif
```

Use SARIF when OpenDoor findings should be consumed by CI/CD security tooling such as GitHub Code Scanning.

OpenDoor writes SARIF 2.1.0 files with one run per generated report. Result buckets are mapped to stable rule ids such as:

| Bucket | SARIF rule id | Level |
|---|---|---|
| `success` | `opendoor.finding.success` | `warning` |
| `indexof` | `opendoor.finding.indexof` | `warning` |
| `auth` | `opendoor.finding.auth` | `warning` |
| `forbidden` | `opendoor.finding.forbidden` | `note` |
| `blocked` | `opendoor.finding.blocked` | `warning` |
| `bypass` | `opendoor.finding.bypass` | `warning` |
| fingerprint metadata | `opendoor.fingerprint.detected` | `note` |

SARIF result `properties` preserve OpenDoor-specific evidence: target, URL, bucket, status code, response size, WAF metadata, bypass metadata and fingerprint metadata.

Example GitHub Code Scanning upload:

```yaml
permissions:
  contents: read
  security-events: write

steps:
  - uses: actions/checkout@v6

  - name: Run OpenDoor
    run: |
      opendoor \
        --host https://example.com \
        --reports sarif,json \
        --reports-dir ./reports

  - name: Upload OpenDoor SARIF
    uses: github/codeql-action/upload-sarif@v3
    with:
      sarif_file: reports/example.com/example.com.sarif
      category: opendoor
```


## HTML

```shell
opendoor --host https://example.com --reports html
```

Use HTML for a readable standalone report.

HTML preserves detailed `report_items` metadata, including header-bypass evidence.

---

## SQLite

```shell
opendoor --host https://example.com --reports sqlite
```

Use SQLite when you want structured local analysis, later filtering, or integration with other tools.

SQLite is useful for:

- large scans;
- batch scans;
- CI artifacts;
- recurring exposure checks;
- historical comparison.

SQLite persists Header Injection Bypass metadata in nullable item columns:

| Column | Meaning |
|---|---|
| `bypass` | Bypass type |
| `bypass_header` | Header that produced the candidate |
| `bypass_value` | Header value used for the probe |
| `bypass_from_code` | Original blocked status code |
| `bypass_to_code` | Resulting status code |

---

## Multiple reports

```shell
opendoor \
  --host https://example.com \
  --reports std,json,html,sqlite,csv,sarif \
  --reports-dir ./reports
```

This is useful when one scan needs both human-readable and machine-readable output.

---

## Header-bypass evidence

When `--header-bypass` is enabled and a candidate is found, OpenDoor stores the result in the `bypass` bucket.

Detailed report items include:

| Field | Meaning |
|---|---|
| `bypass` | Bypass type, currently `header` |
| `bypass_header` | Header that produced the candidate |
| `bypass_value` | Header value used for the probe |
| `bypass_from_code` | Original blocked status code |
| `bypass_to_code` | Resulting status code |

Report support:

| Report | Header-bypass evidence |
|---|---|
| `std` | Shows the `bypass` bucket in summary statistics |
| `txt` | Includes bypass evidence in bypass report lines |
| `json` | Preserves full metadata in `report_items` |
| `csv` | Adds dedicated bypass columns |
| `html` | Preserves detailed `report_items` metadata |
| `sqlite` | Stores bypass metadata in nullable item columns |
| `sarif` | Preserves bypass evidence in SARIF result properties |

---

## CI/CD reports

```shell
opendoor \
  --host https://example.com \
  --reports json,sqlite,csv,sarif \
  --fail-on-bucket success,auth,forbidden,bypass
```

In CI/CD, prefer machine-readable formats such as `json`, `sqlite`, `csv`, and `sarif`.

Use the `bypass` bucket when Header Injection Bypass candidates should fail the pipeline.

---

## Report hygiene

Reports may contain sensitive findings.

Do not commit scan reports that include:

- private target URLs;
- internal paths;
- authentication-related endpoints;
- customer systems;
- cookies;
- tokens;
- private infrastructure details.

Store reports as CI artifacts or local evidence, not as public repository files.
