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

## Part 2 scan: endpoint sniffer and bounded crawl

This command is intended for the second article in the Mastering OpenDoor series.
It keeps request volume bounded, uses the passive `endpoint` sniffer, and enables
one-hop same-origin crawl enrichment.

```shell
opendoor \
  --host http://127.0.0.1 \
  --port 8080 \
  --method GET \
  --threads 1 \
  --wordlist examples/mastering-lab/wordlist.txt \
  --include-status 200-299,301,302,401,403,500 \
  --exclude-status 404 \
  --sniff endpoint,indexof,file,stacktrace,skipempty \
  --crawl \
  --reports std,html,json,sarif \
  --reports-dir reports/mastering-lab-part-2
```

## Part 2 scan: bounded redirect materialization

```shell
opendoor \
  --host http://127.0.0.1 \
  --port 8080 \
  --method GET \
  --threads 1 \
  --wordlist examples/mastering-lab/wordlist.txt \
  --include-status 200-399,401,403,500 \
  --exclude-status 404 \
  --follow-redirects \
  --reports std,html,json,sarif \
  --reports-dir reports/mastering-lab-part-2
```
