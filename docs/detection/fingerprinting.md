# 🧬 Fingerprinting

Fingerprinting attempts to identify probable technologies before or during a scan.

Enable it with:

```shell
opendoor --host https://example.com --fingerprint
```

---

## What fingerprinting helps with

Fingerprinting can help identify probable:

- CMS platforms;
- e-commerce platforms;
- frameworks and application platforms;
- runtime / language families;
- site builders;
- static-site and documentation generators;
- hosting platforms;
- infrastructure providers;
- CDN or edge infrastructure signals.
- long-lived HSTS policy combined with first-party subdomain fan-out;
- persistent ETag/cache validators with long cache lifetime;
- long-lived identifier-like cookies.

This helps you choose better wordlists, filters, and scan strategy.

This is not part of the main scanning process, so it is advisable not to use the `fingerprinting technique` in the main session, as there is a risk of being banned by the WAF already during the scanning process.

---

## Basic example

```shell
opendoor --host https://example.com --fingerprint
```

Combine with directory discovery:

```shell
opendoor \
  --host https://example.com \
  --fingerprint \
  --scan directories
```

---

## Compact pre-scan summary

When fingerprinting is enabled, OpenDoor prints a compact summary immediately after the fingerprint pass and before dictionary enumeration starts. This gives operators an early target profile without waiting for report generation.

Example:

```text
Fingerprint result: cms/WordPress (95%)
Web stack: WordPress | PHP | Cloudflare
Security posture: HSTS preload-ready
Fingerprint evidence: /wp-login
```

The compact summary intentionally stays short. Full evidence, candidates, HSTS fields and report-specific metadata remain in JSON, HTML, CSV, SQLite, TXT, STD and SARIF outputs.

---

## Fingerprinting with reports

```shell
opendoor \
  --host https://example.com \
  --fingerprint \
  --reports json,html
```

Use machine-readable reports when you want to process detected technologies later.

---

## Fingerprinting and scan strategy

A detected technology can influence:

| Signal | Possible scan adjustment |
|---|---|
| CMS | Use CMS-specific wordlists |
| Static hosting | Focus on exposed files and deployment artifacts |
| CDN or edge provider | Enable WAF detection and safer request settings |
| Framework | Scan common framework routes and asset paths |
| Admin panel signal | Focus on auth and restricted resources |

---

## Recognized systems

The heuristic fingerprint engine currently recognizes the following platform families.

### CMS

- Bitrix
- Bludit
- Bolt CMS
- Concrete CMS
- Contao
- Craft CMS
- Directus
- Discourse
- DotCMS
- Drupal
- Evolution CMS
- Ghost
- GravCMS
- Joomla
- Matomo
- MediaWiki
- MODX
- Moodle
- Neos
- Nextcloud
- OctoberCMS
- Open Journal Systems
- ownCloud
- phpBB
- phpMyAdmin
- Pimcore
- TYPO3
- Umbraco
- WordPress
- 3dCart
- Adobe Business Catalyst
- AEM
- Ametys CMS
- Amiro.CMS
- Apostrophe CMS
- BigTree CMS
- BrowserCMS
- CKAN
- CMS.S3 / Megagroup
- Discuz!
- InstantCMS
- DiafanCMS
- NetCat
- CMS CONTENIDO
- CMS Made Simple
- CMSimple
- DataLife Engine
- DNN Platform
- Dynamicweb
- EPiServer
- ExpressionEngine
- Fork CMS
- GetSimple CMS
- Hippo CMS
- ImpressPages CMS
- Kooboo CMS
- Liferay
- Microsoft SharePoint
- Mura CMS
- OpenCms
- Orchard CMS
- Percussion CMS
- PencilBlue
- phpCMS
- phpWind
- Quick.Cms
- RoundCube Webmail
- Serendipity
- SilverStripe
- Sitecore
- Sitefinity
- Subrion CMS
- Sulu
- Textpattern CMS
- TiddlyWiki
- Tiki Wiki CMS Groupware
- UMI.CMS
- WebGUI
- WebsiteBaker CMS
- Wolf CMS
- XOOPS
- XpressEngine
- e107
- eZ Publish
- sNews

### E-commerce

- Magento
- Moguta CMS
- nopCommerce
- OpenCart
- PrestaShop
- Shopify
- Shopware
- WooCommerce
- Webasyst / Shop-Script
- BigCommerce
- CS-Cart
- CubeCart
- EC-CUBE
- Odoo
- Salesforce Commerce Cloud
- ShopFA
- Shoper
- Shopery
- Shoptet
- Smartstore
- Spree
- WHMCS
- Zen Cart CMS
- ePages

### Frameworks and app platforms

- Angular
- ASP.NET
- Astro
- Django
- Express
- FastAPI
- Fastify
- Flask
- Gatsby
- Hapi
- Koa
- Laravel
- NestJS
- Next.js
- Nuxt
- Phoenix
- React
- Remix
- Ruby on Rails
- Spring
- Strapi
- SvelteKit
- Symfony
- Vue

### Site builders

- Squarespace
- Mobirise
- Tilda
- Webflow
- Wix
- Blogger
- Bubble
- Duda
- GoDaddy Website Builder
- Hostinger Website Builder
- Jimdo
- Weebly

### Static and docs generators

- Docusaurus
- Hugo
- Jekyll
- MkDocs
- VitePress
- AsciiDoc

### Infrastructure providers and hosting edge signals

- AWS
- AWS API Gateway
- AWS Amplify
- AWS CloudFront
- AWS ELB / ALB
- AWS S3
- Akamai
- CityHost
- Cloudflare
- DDoS-Guard
- Fastly
- GitHub Pages
- GitLab Pages
- Google App Engine
- Google Cloud
- Google Cloud / Google Frontend
- Google Cloud Run
- Heroku
- Microsoft Azure
- Microsoft Azure App Service
- Netlify
- OpenResty
- QRATOR / Qrator Labs
- Tencent Cloud
- Vercel

### Server header infrastructure signals

When the HTTP `Server` header exposes web or application server software,
OpenDoor reports it under `fingerprint.infrastructure` without changing the
runtime stack result. Examples include:

- Nginx
- Apache HTTP Server
- Microsoft IIS
- Caddy
- LiteSpeed
- lighttpd
- Tornado
- Gunicorn
- Uvicorn
- Hypercorn
- Waitress
- Apache Tomcat
- Eclipse Jetty
- Envoy
- Traefik

### Stack technologies

- PHP
- Node.js
- JavaScript
- Python
- Ruby
- .NET
- Java/JVM
- Elixir
- Static site

---

## Security headers posture

When `--fingerprint` is enabled, OpenDoor also performs an offline HSTS posture check against the observed target root response. It does not query external preload services. The check uses only headers returned by the target host.

The HSTS result is stored under `fingerprint.security_headers.hsts` in machine-readable reports.

Example JSON fragment:

```json
{
  "fingerprint": {
    "security_headers": {
      "hsts": {
        "present": true,
        "header": "max-age=31536000; includeSubDomains; preload",
        "max_age": 31536000,
        "include_subdomains": true,
        "preload": true,
        "preload_ready": true,
        "http_to_https_redirect": true,
        "grade": "preload-ready",
        "warnings": []
      }
    }
  }
}
```

OpenDoor grades HSTS as:

| Grade | Meaning |
|---|---|
| `missing` | No effective HSTS was observed on the final HTTPS response, or the final response was plain HTTP. |
| `invalid` | HSTS exists, but `max-age` is missing or invalid. |
| `disabled` | HSTS is explicitly disabled with `max-age=0`. |
| `weak` | HSTS exists, but `max-age` is below 180 days. |
| `moderate` | HSTS is usable, but below the common preload minimum of one year. |
| `good` | HSTS has at least one year `max-age`, but lacks `includeSubDomains`. |
| `strong` | HSTS has at least one year `max-age` and `includeSubDomains`. |
| `preload-ready` | Local preload-readiness checks passed: HTTPS final response, `max-age >= 31536000`, `includeSubDomains`, and `preload`. |

Warnings are intentionally explicit, for example `missing_hsts`, `max_age_too_low`, `missing_include_subdomains`, `preload_not_ready`, or `not_https`.

---

## Recommended workflow

```shell
opendoor \
  --host https://example.com \
  --fingerprint \
  --auto-calibrate \
  --reports std,json,csv
```

This gives a better initial view of the target before deeper scans.

---

## Notes

Fingerprinting is heuristic. Treat results as probable signals, not as guaranteed facts.

Always verify important findings manually.

For WAF and anti-bot detection, see [WAF detection and safe mode](waf-detection.md).
