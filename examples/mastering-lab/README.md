# OpenDoor Mastering Lab

This directory contains the deterministic local HTTP target used by the
Mastering OpenDoor article series.

The lab binds to `127.0.0.1` only and is intended for authorized local testing,
documentation screenshots and repeatable command validation.

## Start the lab

```shell
python examples/mastering-lab/server.py
```

Use another terminal for OpenDoor commands.

## Baseline scan

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

## Low-noise scan

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
