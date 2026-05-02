# 🧪 CI/CD examples

OpenDoor can be used in CI/CD pipelines as an exposure check or regression gate.

---

## Basic CI command

```shell
opendoor \
  --host https://example.com \
  --reports json,sqlite,sarif
```

---

## Fail on selected buckets

```shell
opendoor \
  --host https://example.com \
  --fail-on-bucket success,auth,forbidden,blocked,bypass
```

OpenDoor completes the scan and exits with code `1` if selected result buckets are found.

Use the `bypass` bucket when Header Injection Bypass candidates should fail the pipeline.

---

## Low-noise CI gate

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --auto-calibrate \
  --include-status 200-299,301,302,403 \
  --exclude-status 404,429,500-599 \
  --reports json,sqlite,csv,sarif \
  --fail-on-bucket success,auth,forbidden,bypass
```

---

## CI gate with Header Injection Bypass

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --waf-detect \
  --header-bypass \
  --header-bypass-limit 32 \
  --reports json,sqlite,csv,sarif \
  --fail-on-bucket success,auth,forbidden,bypass
```

Use this only for authorized exposure regression checks.

---

## Batch CI gate

```shell
opendoor \
  --hostlist targets.txt \
  --auto-calibrate \
  --reports json,sqlite,csv,sarif \
  --fail-on-bucket success,auth,forbidden,bypass
```

---

## GitHub Actions example

```yaml
name: OpenDoor exposure check

on:
  workflow_dispatch:
  schedule:
    - cron: "0 3 * * *"

jobs:
  opendoor:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install OpenDoor
        run: |
          python3 -m pip install --user pipx
          python3 -m pipx ensurepath
          pipx install opendoor

      - name: Run OpenDoor
        run: |
          opendoor \
            --host https://example.com \
            --method GET \
            --auto-calibrate \
            --header-bypass \
            --header-bypass-limit 32 \
            --reports json,sqlite,csv,sarif \
            --reports-dir ./reports \
            --fail-on-bucket success,auth,forbidden,bypass

      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: opendoor-reports
          path: reports/
```

---

## GitHub Code Scanning with SARIF

```yaml
name: OpenDoor SARIF scan

on:
  workflow_dispatch:

permissions:
  contents: read
  security-events: write

jobs:
  opendoor-sarif:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v6

      - name: Install OpenDoor
        run: |
          python3 -m pip install --user pipx
          python3 -m pipx ensurepath
          pipx install opendoor

      - name: Run OpenDoor
        run: |
          opendoor \
            --host https://example.com \
            --method GET \
            --auto-calibrate \
            --reports sarif,json \
            --reports-dir ./reports \
            --fail-on-bucket success,auth,forbidden,bypass

      - name: Upload OpenDoor SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: reports/example.com/example.com.sarif
          category: opendoor
```

Use `security-events: write` so GitHub Actions can upload SARIF into Code Scanning.


## GitLab CI example

```yaml
opendoor:
  image: python:3.13
  script:
    - python -m pip install --upgrade pip pipx
    - python -m pipx ensurepath
    - pipx install opendoor
    - |
      opendoor \
        --host https://example.com \
        --method GET \
        --auto-calibrate \
        --header-bypass \
        --header-bypass-limit 32 \
        --reports json,sqlite,csv,sarif \
        --reports-dir ./reports \
        --fail-on-bucket success,auth,forbidden,bypass
  artifacts:
    when: always
    paths:
      - reports/
```

---

## CI safety notes

Do not put secrets directly in repository workflows.

Use CI secret stores for:

- tokens;
- cookies;
- authenticated raw requests;
- proxy credentials;
- VPN credentials.

Do not upload public artifacts containing sensitive findings.
