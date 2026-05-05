# 🛡️ WAF detection and safe mode

OpenDoor can passively detect probable WAF, CDN, and anti-bot behavior.

Enable detection:

```shell
opendoor --host https://example.com --waf-detect
```

Enable safe mode:

```shell
opendoor --host https://example.com --waf-safe-mode
```

---

## What WAF detection does

WAF detection looks for signals that indicate protective infrastructure, such as:

- blocking responses;
- WAF-specific headers;
- CDN or edge infrastructure markers;
- suspicious response patterns;
- anti-bot behavior.

It is intended for safer scan classification and better operator awareness.

---

## Recognized WAF, anti-bot, and edge protection systems

The heuristic WAF detection engine currently recognizes probable signals for:

- 360 WAF
- Airlock
- Akamai
- Aliyun WAF
- Anquanbao
- Anubis
- AppTrana
- AWS WAF
- Azure Front Door
- Barracuda
- BinarySec
- BitNinja
- Bluedon WAF
- ChinaCache
- CityHost
- Cloudflare
- Comodo WAF
- DataDome
- Distil
- DoSArrest
- DotDefender
- F5 BIG-IP ASM
- Fastly
- FortiWeb
- GoDaddy Website Firewall
- GreyWizard
- Huawei Cloud WAF
- IBM DataPower
- Imperva
- Imunify360
- Instart DX
- Kasada
- ModSecurity
- NAXSI
- NetScaler / Citrix WAF
- NinjaFirewall
- PerimeterX / HUMAN
- Profense
- Radware
- Reblaze
- Sucuri
- WebKnight

Detection is heuristic. Treat results as probable signals and verify important findings manually.

OpenDoor keeps WAF detection passive: it classifies the responses that the scanner already receives and does not add extra WAF-triggering requests. Passive gateway or server markers that are commonly present on normal traffic are gated by block-like status codes in both vendor-specific detection and generic fallback detection to reduce false positives on successful pages.

---

## Safe mode

Safe mode enables a more cautious runtime profile after WAF or anti-bot behavior is detected.

```shell
opendoor --host https://example.com --waf-safe-mode
```

Use safe mode when scanning authorized targets protected by:

- WAF;
- CDN;
- anti-bot middleware;
- rate limiting;
- managed edge security.

---

## Recommended WAF-safe scan

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --auto-calibrate \
  --timeout 60 \
  --retries 5 \
  --delay 0.5 \
  --reports json,html
```

---

## WAF-safe scan with Header Injection Bypass

For authorized blocked-resource validation, Header Injection Bypass can be enabled as a separate opt-in feature.

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --waf-detect \
  --waf-safe-mode \
  --header-bypass \
  --header-bypass-limit 32 \
  --reports json,sqlite,csv
```

Header-bypass probes are temporary per-request headers and do not mutate global scan headers.

For details, see [Header Injection Bypass](header-bypass.md).

---

## WAF detection with CI/CD

```shell
opendoor \
  --host https://example.com \
  --waf-detect \
  --reports json,sqlite
```

This can help track whether protective infrastructure behavior changed between releases.

Header-bypass candidates can also be used as CI/CD signals:

```shell
opendoor \
  --host https://example.com \
  --method GET \
  --header-bypass \
  --reports json,sqlite,csv \
  --fail-on-bucket success,auth,forbidden,bypass
```

---

## Responsible use

This feature is for detection and cautious scanning of authorized targets.

Do not use OpenDoor documentation or examples as bypass guidance for third-party systems.

---

## Troubleshooting

### Many blocked responses

Reduce scan pressure:

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --threads 3 \
  --delay 1 \
  --timeout 60
```

### Too much noise

Combine WAF detection with auto-calibration and response filters:

```shell
opendoor \
  --host https://example.com \
  --waf-safe-mode \
  --auto-calibrate \
  --exclude-status 404,429,500-599
```
