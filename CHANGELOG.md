CHANGELOG
=======

v5.18.0 (TBD)
---------------------------
- (performance) browser runtime cleanup lifecycle to preserve scan results and crawl diagnostics until reports are finalized, while releasing heavy in-memory request/cache state after result consumption.

v5.17.0 (10.06.2026)
---------------------------
- (critical) avoided expensive collation comparisons on large response bodies, preventing slow classification of valid large 200 OK pages while preserving normal success reporting and small-template soft404 detection.
- (fix) responseError: Unknown response status : `507 (Insufficient storage)` so scans no longer abort on unexpected HTTP status codes.
- (fix) responseError: Unknown response status : `408 (Request Timeout)` so scans no longer abort on unexpected HTTP status codes.
- (fix) preserved explicit `--header "User-Agent: ..."` precedence across proxy/proxy-pool requests and aligned debug output with the effective custom User-Agent.
- (fix) expanded JavaScript cookie-gate suppression preventing bootstrap pages from being reported as `OK` or `OK (Shadow)` findings.
- (fix) reduced `--sniff secret` false positives by requiring Slack token structural validation.
- (fix) reduced `--sniff malware` false positives by ignoring `document.write(unescape(...))` loaders inside inactive HTML comments, while preserving detection for active script loaders.
- (fix) `--sniff file` now classifies exposed `.db` files such as `Thumbs.db`, `cache.db`, and other database-like paths as `OK (File)` even when MIME metadata is missing or the response is HEAD-like, while avoiding soft-200 textual fallback pages.
- (fix) fixed host normalization so plain hostnames containing `http` or `https` in the label are no longer misdetected as already having a URL scheme.
- (fix) made Browser pending request deduplication thread-safe across session, transient, crawl and recursive queue paths.
- (feature) added `--sniff endpoint` to passively detect exposed WebSocket, Socket.IO, SSE/EventSource and AJAX endpoints from already-fetched responses without active connections, JavaScript execution or queue expansion.
- (feature) added built-in passive redirect classification for discovered 3xx responses, adding concise `R(...)` CLI markers and bounded redirect metadata to existing reports without following redirects or increasing request volume.
- (feature) added opt-in `--crawl` mode for bounded same-origin one-hop queue enrichment from HTML links/forms with normal report classification, crawl-aware progress output, and runtime crawl diagnostics.
- (feature) added explicit `--follow-redirects` support for bounded same-host redirects so canonical redirect chains can be materialized and classified by their final response without changing default passive redirect behavior.
- (enhancement) hardened `--sniff openredirect` marker verification with shared redirect-target normalization, explicit false-positive controls and additive payload-family report metadata without changing the public command or expanding payload volume.
- (enhancement) hardened GravCMS fingerprint detection with a stronger passive generator.
- (enhancement) added BunkerWeb passive WAF detection.
- (enhancement) added UNA CMS fingerprint detection from UNA branding.
- (enhancement) added conservative passive Nubex CMS detection.
- (enhancement) enriched redacted JWT secret findings with bounded, non-verifying claims metadata without storing raw tokens or changing scan behavior.
- (enhancement) added per-bucket report item deduplication to prevent duplicate findings from dirty wordlists, repeated scan inputs, resumed sessions, and future crawl-discovered URLs while preserving distinct findings across different buckets.
- (enhancement) added memory usage to terminal Runtime diagnostics automatically when `--debug` output is enabled, without a separate CLI flag or any change to request volume/report schemas.
- (core) added additive structured `passive_finding` metadata for `secret`, `malware`, `stacktrace`, `shadow` and `openredirect` reports while preserving existing detection behavior, buckets, labels and legacy metadata.
- (ux) `--sniff file` scan output now labels file sniffer hits as `OK (File)` like other sniffer findings without changing report buckets or detection semantics.
- (ux) added Runtime diagnostics traffic counters for response bodies, response headers and logical request attempts, preserved across session checkpoints.
- (ux) shortened slow-item watchdog warnings and added processing phase labels for clearer scan diagnostics.
- (performance) improved scan resource cleanup by closing worker pools, request connection pools, memory monitor tracing state, and temporary scan resources during browser shutdown.
- (performance) reduced memory pressure for scans without session checkpoints by avoiding persistent session bookkeeping when `--session-save` is disabled.
- (build) added Chocolatey package metadata for Windows distribution.
- (build) added package manager validation workflow.
- (dictionary) cleaned and normalized the internal directories list (+481 potential interesting paths).
- (deps-dev) [PR#119](https://github.com/stanislav-web/OpenDoor/pull/119) bump the python-runtime-dependencies group with 2 updates.
- (deps-dev) [PR#120](https://github.com/stanislav-web/OpenDoor/pull/120) bump codecov/codecov-action from 6 to 7 in the github-actions group.

v5.16.2 (31.05.2026)
---------------------------
- (critical) fixed scan crashes caused by corrupted gzip/encoded HTTP responses by handling `DecodeError` as a recoverable transport failure instead of aborting worker threads.
- (fix) JavaScript cookie-gate bootstrap pages such as `document.cookie` + `location.reload()` responses are no longer reported as `OK` findings.
- (fix) subdomain scans so missing/no-response candidates are skipped without triggering the directory retry fail-streak abort guard.
- (fix) directory scan prefix normalization so `--prefix ex` and `--prefix ex/` both scan under `/ex/<path>` instead of concatenating paths as `/ex<path>`.
- (fix) reduced WAF-safe auto-calibration noise by using neutral calibration probe paths when `--waf-safe-mode` is enabled, avoiding high-risk `.php`, `.map`, `admin`, and `wp-*` probe shapes.
- (fix) `--fingerprint` no longer treats generic WordPress static-path probes as strong WordPress evidence unless corroborated by root-page WordPress signals.
- (fix) `--auto-calibrate` now disables weak HTTP baselines when too many probes are blocked, ignored, or failed, preventing sparse signatures from over-filtering scan results.
- (fix) `--sniff shadow` false positives on soft-200/fallback routes by adding a negative-control probe before reporting backup-file variants.
- (fix) `--sniff malware` false positives when fallback pages repeatedly echo webshell-like names inside URL/query attributes, while preserving real webshell UI and executable payload detections.
- (fix) `--sniff malware` false positives on security-plugin documentation by suppressing name-only webshell vocabulary in documentation context while preserving executable payload and shell UI detections.
- (fix) `--sniff malware` false positives on legacy Google Analytics loaders while preserving suspicious document.write, atob, String.fromCharCode and PHP payload detections.
- (fix) `--sniff secret` scan output so secret sniffer hits are labeled as `OK (Secret)` like other sniffer findings.
- (fix) `--fingerprint` now detects DataLife Engine (DLE) from conservative runtime globals and engine asset signals.
- (fix) `--fingerprint` now prefers Webflow hosted-platform signals over endpoint-only WordPress static path artifacts.
- (fix) `--fingerprint` now detects CMS.S3 / Megagroup from strong root-page builder/runtime markers without relying on generic WordPress endpoint probes.
- (fix) transport-exhausted directory entries are now tracked in `transport_failed.txt` and JSON diagnostics, and scans automatically pause after repeated transport failures to avoid burning through the wordlist during temporary network outages.
- (enhancement) added Camaleon CMS without adding active probes.
- (enhancement) added Evolution CMS fingerprint detection.
- (enhancement) added strong UMI.CMS fingerprint detection rules.
- (enhancement) added Melbis Shop Platform fingerprint detection rules.
- (enhancement) added conservative MogutaCMS fingerprint detection without active probes.
- (enhancement) added Ruby on Rails fingerprint detection with conservative passive CSRF, Rails UJS/Turbo, asset-pipeline and Rails error markers while avoiding standalone Rack.
- (enhancement) reduced `--sniff malware` false positives for standard Bitrix admin login pages by allowlisting the built-in hidden `auth_frame` iframe only when strong Bitrix login markers are present.
- (enhancement) `--sniff secret` now detects additional low-noise token patterns, including GitHub fine-grained tokens, Square-style tokens, leaked bearer headers and expanded credential assignments.
- (ux) clarified Runtime Diagnostics queue accounting by showing consumed items, submitted HTTP jobs, and pre-request skipped items separately.
- (ux) clarified runtime pause/resume behavior by making the Ctrl+C pause prompt visible after in-flight worker output drains and by documenting Enter/C continue and E/Q abort semantics.
- (dictionary) cleaned and normalized the internal directories list (+1247 potential interesting paths).
- (docs) added a `Mastering OpenDoor` companion documentation page for the upcoming article series.
- (deps-dev) [PR#115](https://github.com/stanislav-web/OpenDoor/pull/115) bump ruff from 0.15.13 to 0.15.14 in the python-runtime-dependencies group.

v5.16.1 (24.05.2026)
---------------------------
- (fix) reduced duplicate fingerprint traffic by reusing exact same method+URL probe responses within a single fingerprint pass.
- (fix) avoided false early-finish warnings when planned wordlist entries are intentionally skipped before HTTP submission, such as internally ignored paths.
- (fix) aligned `indexof` runtime progress output with other sniffer findings by rendering it as `OK (IndexOf)` without changing detection or report semantics.
- (fix) preserved managed runtime wordlist workspaces across interactive `Ctrl+C` pause/resume while keeping cleanup for aborts, process termination and normal scan completion.
- (fix) normalized `--fingerprint` handling across CLI, wizard and session resume flows while keeping fingerprinting opt-in and cached session results reusable.
- (fix) normalized WAF detection flags across CLI, wizard and session resume flows while preserving `waf_safe_mode` as an opt-in runtime profile that enables passive WAF detection.
- (fix) validated `--threads` values, preserved explicit thread-count overrides for wizard/session resume flows, and raised the safe runtime thread clamp from 25 to 50.
- (fix) validated scan report selections, normalized `--reports-dir`, and preserved explicit report output overrides for wizard/session resume flows.
- (fix) validated recursive scan options, preserved explicit recursive CLI overrides for wizard/session resume flows, and kept recursive defaults stable at runtime.
- (fix) validated `--method` values, preserved explicit method overrides for wizard/session resume flows, and kept raw-request method handling deterministic.
- (fix) validated `--port` values as TCP ports, preserved explicit port overrides for wizard/session resume flows, and rejected invalid raw-request Host ports early.
- (fix) propagated `--fail-on-bucket` exit codes through the installed `opendoor` entrypoint so CI/CD runs behave the same as `python opendoor.py`.
- (fix) preserved fractional `--delay` values (0.1, 0.25...etc), rejected negative delays, and allowed explicit delay overrides for wizard/session resume flows.
- (fix) reduced malware sniffer false positives by ignoring legitimate Google Tag Manager noscript hidden iframes while preserving detection for non-GTM hidden iframe injections.
- (fix) kept scans running when individual paths exhaust configured retries while preserving configurable abort protection for consecutive retry failures.
- (fix) ignored-path progress output so `skip [...]` shows the current scan position instead of `00000`.
- (fix) proxy CLI overrides for wizard and session resume flows so explicit `--proxy`, `--proxy-pool`, and `--proxy-list --proxy-rotation` selections replace restored proxy settings correctly.
- (fix) filtered/calibrated progress counters to use the same dynamic width as regular scan findings.
- (fix) fingerprint evidence output to avoid repeating identical evidence values when the same marker is confirmed by multiple signal sources.
- (fix) ResponseError: Unknown response status : `477` (non standart error) so scans no longer abort on unexpected HTTP status codes. 
- (fix) stopped pre-skipping common error, index, redirect-like, and not-found paths from the bundled ignore list so they are scanned and classified normally.
- (fix) made active shadow probe requests honor the configured scan delay while preserving existing retry, timeout, proxy and request-stack behavior.
- (enhancement) improved the active `shadow` sniffer with bounded path-template probes such as `{file}}2.{ext}` while keeping per-scan probe limits.
- (enhancement) improved the `stacktrace` sniffer to detect exposed database connection identity errors like `Could not make a database connection using user@host` while avoiding generic connection-error false positives.
- (enhancement) hardened `--header` validation and normalization, including wizard/session CLI override handling.
- (enhancement) added remote HTTP(S) wordlist support through `--wordlist`, including streaming download progress and a 500 MB safety limit.
- (enhancement) added `--proxy-rotation random|sequential` to control existing `--proxy-list` rotation, preserving `random` as the default and adding deterministic file-order sequential mode.
- (enhancement) added DotCMS and DiafanCMS detection to `--fingerprint`.
- (enhancement) added configurable `--retries-fail-streak` to control scan aborts after consecutive exhausted retry paths. Default: `10`.
- (enhancement) expanded passive WAF recognition coverage with additional 21 WAF systems. Details : (https://opendoor.readthedocs.io/detection/waf-detection/).
- (ux) added debug-only runtime diagnostics to the terminal scan summary.
- (dictionary) cleaned and normalized the internal directories list (+2365 potential interesting paths).

v5.16.0 (17.05.2026)
---------------------------
- (fix) rendered fingerprint progress as a rotating single-line indicator and persisted only the final `done` state to reduce duplicate progress output.
- (fix) proxy and transport-loss handling: proxy scans now validate the proxy without directly probing the target, filtered proxy timeouts remain visible, and direct scans abort cleanly after repeated exhausted transport failures when a target goes offline mid-scan.
- (fix) made auto-calibrated rotating progress cross-platform by truncating suppressed-response lines to terminal width and clearing them before real findings.
- (fix) diversified auto-calibration probe URL shapes so sites that return different soft-404/catch-all responses for root-level, application-like and static asset paths are calibrated more reliably.
- (fix) made HTML report status tabs work as anchor-backed navigation with JavaScript filtering as progressive enhancement, improving large report responsiveness and browser compatibility.
- (fix) handled `ResponseError: Unknown response status : 523` so scans no longer abort on unexpected HTTP status codes.
- (fix) graceful handling for unavailable standalone SOCKS/HTTP proxies.
- (fix) authenticated HTTP proxy support for HTTPS CONNECT requests and masked proxy credentials in debug, warning, and error output.
- (fix) cleaned WAF/header-bypass diagnostics: cookie accept debug now logs once, watchdog tracks long-running probe heartbeats, and piped logs no longer include ANSI clear-line sequences.
- (fix) extension filters: `--extensions` and `--ignore-extensions` are now mutually exclusive, extension matching handles query strings/fragments, matching is case-insensitive, and documentation now describes `--extensions` as a filter rather than generation.
- (fix) wizard regex filters so comma-containing patterns are preserved safely.
- (fix) reduced report noise by keeping filtered responses out of user-facing reports while preserving them in raw JSON/session data.
- (fix) response-filter overrides for resumed sessions and precompiled regex filters for faster runtime checks.
- (fix) proxy rotation console output so debug and warning messages no longer corrupt fingerprint, calibration, and scan progress lines.
- (fix) reused initialized proxy request providers across pre-scan and scan phases to avoid redundant proxy-list initialization.
- (fix) preserved direct scan provider refresh when scan targets are rewritten by runtime options.
- (fix) reduced auto-calibration console noise by suppressing per-probe response output while keeping the calibration summary.
- (fix) noisy debug output in `--proxy-pool` mode by logging proxy selection only when a new proxy pool is created.
- (feature) added `--waf-guard` with configurable `--waf-guard-after` and `--waf-guard-threshold` to stop scans early when initial classified responses are overwhelmingly WAF-blocked.
- (feature) added `--diff` to compare exactly two previous/current OpenDoor SQLite or JSON reports and show added, removed and changed findings without running a new scan.
- (feature) added `--sniff malware` to passively classify suspicious malware, webshell, injected script and obfuscated payload indicators into the `malware` bucket with structured metadata across runtime output and reports.
- (feature) added `--sniff shadow` active Shadow Copy Detection to probe confirmed `200 OK` file-like hits for exposed backup/suffix copies such as `.bak`, `.old`, and similar variants.
- (feature) added `--sniff secret` to classify successful textual responses with possible leaked API keys, tokens, private keys, JWTs and credential URLs into the `secret` bucket.
- (feature) added `--sniff openredirect` for verified open redirect detection: OpenDoor now performs bounded active checks on discovered redirect-like query parameters, reports findings in the `openredirect` bucket, and preserves evidence across text, JSON, CSV, HTML, SQLite, and SARIF reports.
- (feature) added opt-in `--tls-legacy` mode for weak-DH HTTPS targets and improved TLS handshake diagnostics with `DH_KEY_TOO_SMALL` guidance.
- (enhancement) scan runtime temp handling by moving generated wordlist artifacts into per-scan managed workspaces with cross-platform cleanup on normal exit, errors, and abort signals.
- (enhancement) added `socks5h://` proxy URL support for standalone proxy and proxy-list flows without changing existing proxy debug output.
- (enhancement) improved `--update` as a safe cross-platform helper: it no longer depends on scanner data assets, does not execute package-manager commands, and now prints update instructions for pipx, pip, Homebrew, Docker, Linux packages, Windows, and source checkout installs.
- (enhancement) hardened response filter handling across CLI, wizard configuration, and session resume flows.
- (enhancement) hardened proxy routing: `--proxy`, `--proxy-list`, and `--proxy-pool` are now mutually exclusive, rotating proxies skip dead entries during the current scan runtime, authenticated proxy-list entries support HTTPS CONNECT, and selected rotating proxies are shown in debug with credentials masked.
- (enhancement) refactored the internal sniffer architecture to support independent multi-finding detection, additive security findings, suppressor separation and shared active-sniffer orchestration while preserving existing `--sniff` CLI aliases and report buckets.
- (enhancement) improved controlled 403 `header-bypass` probing with additional safe path-normalization variants, including encoded-dot, semicolon-prefix, dot-semicolon-prefix, double-slash semicolon, and dot-dot semicolon suffix checks for arbitrary protected paths discovered during scans.
- (enhancement) hardened Stacktrace sniffer detection to avoid false positives from normal HTML/CSS source code such as `.*-warning`, `.*-error`, and similar style/class names.
- (enhancement) hardened WordPress fingerprinting by adding static asset probes and preventing weak login/xmlrpc-only evidence from becoming a primary CMS match
- (enhancement) preserves redacted Secret Sniffer metadata in standard, text, CSV, JSON, HTML, SQLite and SARIF reports without storing raw secret values.
- (enhancement) added Mobirise site-builder detection to `--fingerprint` using generator, asset and markup signals common to Mobirise landing pages.
- (enhancement) added QRATOR / Qrator Labs infrastructure detection to `--fingerprint`.
- (dependencies) removed unused `six` and replaced `tabulate` in the STD summary reporter with a native psql-like table formatter.
- (ux) reduced stdout Summary noise by hiding low-value diagnostic counters and detailed fingerprint/HSTS/privacy internals while preserving them in structured reports.
- (ux) improved connection preflight diagnostics for localhost/proxy transport checks.
- (dictionary) bundled `data/shadow-suffixes.dat` in source and wheel distributions so PyPI, Homebrew-style source builds and local installs include the built-in shadow suffix catalog by default.
- (dictionary) cleaned and normalized internal directories list (+xxx potencial interesting paths).
- (build) added staged Ruff quality gates and advisory Vulture dead-code checks, with updated contributor rules and cleanup documentation.

v5.15.3 (09.05.2026)
---------------------------
- (critical) prevented silent partial scans when randomized runtime wordlists are truncated by validating shuffled list size and warning on early EOF before report generation
- (critical) restored runtime `Ctrl+C` pause/resume so the first interrupt opens the continue/exit menu during active worker joins instead of immediately canceling the scan.
- (fix) hardened STD reporter summary generation for partial or malformed report payloads
- (fix) detect Bitrix from CMS header and harden Strapi fingerprinting
- (fix) tuned runtime fingerprint scoring so endpoint-only framework probes no longer imply Node.js/Python runtime
- (fix) added conservative PHP route-marker runtime evidence for legacy PHP sites without exposed `X-Powered-By` headers
- (fix) broken random-list shuffle and JS challenge detection 
- (fix) `--accept-cookies` routing so accepted cookies are preserved across scan requests and header-bypass variants.
- (fix) gated passive WAF/gateway headers in both vendor-specific matching and generic fallback so normal 200 responses are not promoted to blocked
- (fix) isolated default fingerprint fallback results with deep copies to prevent nested metadata leakage between failed or empty detection runs
- (fix) added vendor-specific and generic-fallback gating for passive gateway/server markers to avoid classifying normal 200 responses as blocked WAF pages
- (fix) `--debug 0` being incorrectly treated as debug level 1.
- (fix) `file` response sniffer false positives for large textual web/API responses. Large `text/html`, `text/*`, JSON, XML, XHTML and SVG responses are no longer classified as files only because their body or `Content-Length` exceeds the large-response threshold.
- (fix) hardened `--transport` / `--transport-profile` flow with startup validation, proxy-mode safeguards and transport healthcheck execution
- (fix) added cross-platform VPN executable resolution via `--transport-bin`, common OpenVPN/WireGuard backend lookup paths and actionable OS-specific diagnostics when VPN backends are missing
- (fix) hardened `--sniff indexof` directory-listing detection to avoid title-only false positives while preserving Apache, nginx, IIS and generic autoindex layouts
- (fix) validated `--retries` / wizard `retries` as a non-negative integer and normalized runtime retry values before passing them to urllib3
- (fix) restored interactive HTML report controls by making visible URL copy, text search and status-group navigation use stable row metadata and explicit UI feedback
- (fix) deduplicate duplicate subdomain scan candidates before they are submitted to the HTTP worker queue.
- (fix) keep subdomain scan progress totals aligned when duplicate candidates are dropped.
- (fix) Cache rendered subdomain IP lookups per hostname to avoid repeated DNS resolution in subdomain reports.
- (enhancement) added passive privacy-risk detection to `--fingerprint` for possible supercookie tracking surfaces.
- (enhancement) added supercookie/privacy-risk metadata to `std`, `txt`, `csv`, `json`, `html`, `sqlite`, and `sarif` reports.
- (enhancement) added `--header-bypass-profile safe|offensive` with offensive header spoofing and expanded path-normalization variants for controlled 401/403 bypass probing.
- (enhancement) expanded header-bypass evidence with profile, status transition, score and reason metadata across detailed reports.
- (enhancement) added `--sniff stacktrace` to detect exposed stack traces and debug error details across Python, Node.js, PHP, NestJS, Java, SQL, and Oracle responses.
- (enhancement) expanded passive WAF recognition with block-response signatures for DDoS-GUARD, Tencent Cloud WAF, Google Cloud Armor, SafeLine, Vercel WAF, Wallarm and Wordfence, complementing existing infrastructure fingerprinting where applicable.
- (enhancement) detect common HTTP `Server` header engines as fingerprint infrastructure, including Nginx, Apache HTTP Server, Microsoft IIS, Caddy, LiteSpeed, lighttpd, Tornado, Gunicorn, Uvicorn, Hypercorn, Waitress, Apache Tomcat, Eclipse Jetty, Envoy and Traefik
- (enhancement) Added clear response-level diagnostics for `--debug 3`.
- (enhancement) prettify HTML reports make it more intelligible for UX
- (enhancement) expanded passive WAF recognition with additional vendor signatures sourced from public WAF fingerprint catalogs
- (enhancement) expanded passive WAF recognition with DDoS-GUARD, Google Cloud Armor, SafeLine, Tencent Cloud WAF, Vercel WAF, Wallarm and Wordfence signatures while keeping passive edge headers gated behind block-like statuses
- (enhancement) added 360 WAF, Airlock, Aliyun WAF, Anquanbao, BinarySec, CityHost, BitNinja, Bluedon WAF, ChinaCache, Comodo WAF, DoSArrest, DotDefender, GoDaddy Website Firewall, GreyWizard, IBM DataPower, Imunify360, Instart DX, NAXSI, NinjaFirewall, Profense and WebKnight detection
- (enhancement) deduplicated WAF evidence signals before report propagation
- (enhancement) updated internal wordlists
- (deprecated) made `scheme` the source of truth for HTTP/HTTPS mode and deprecated standalone wizard `ssl` configuration to prevent mismatched request providers
- (docs) documented runtime pause/resume controls separately from session checkpoint resume.
- (docs) updated documentation with added more detailed examples and hits
- (debug) added compact STD fingerprint evidence counters for report-level QA
- (debug) added scan worker stall diagnostics and ensured queued tasks are always marked done after worker errors to avoid silent hangs during long-running requests
- (debug) added compact fingerprint evidence signals to `fingerprint.txt` for easier QA of runtime/infrastructure detection
- (dependencies) update dependencies to the latest versions
- (tests) added regression coverage for new WAF signatures, passive-header false-positive protection and fingerprint fallback isolation
- (tests) expanded coverage for transport healthcheck cleanup branches, OpenVPN liveness diagnostics and hardened indexof detection paths
- (tests) coverage gate remains configured at `99%`

v5.15.2 (04.05.2026)
---------------------------
- (enhancement) added compact pre-scan fingerprint summary with detected web stack and security posture
- (enhancement) added offline HSTS and preload-readiness detection to the existing `--fingerprint` pass without adding a new CLI flag
- (enhancement) stores security-header posture as `fingerprint.security_headers.hsts` with grade, max-age, includeSubDomains, preload, redirect and warning metadata
- (enhancement) preserves HSTS metadata in standard, text, CSV, HTML, SQLite, JSON and SARIF reports
- (docs) documented compact pre-scan fingerprint summary and HSTS / preload readiness output
- (tests) added regression coverage for compact fingerprint summary rendering
- (tests) added regression coverage for preload-ready, weak and HTTP-only HSTS handling plus report propagation
- (tests) coverage gate remains configured at `99%`

v5.15.1 (03.05.2026)
---------------------------
- (fix) removed literal `opendoor` markers from active fingerprint 404-baseline, HTTP calibration and DNS wildcard calibration probe paths
- (fix) fingerprint 404-baseline now uses a neutral randomized `.well-known` missing-resource path instead of `/.opendoor-fingerprint-not-found-probe`
- (tests) updated fingerprint, HTTP calibration and DNS wildcard calibration coverage for neutral probe paths
- (enhancement) added runtime-aware technology stack fingerprinting for PHP, Node.js, JavaScript, Python, Ruby, .NET, Java/JVM, Elixir and static-site targets
- (enhancement) preserved runtime stack metadata in fingerprint results as `fingerprint.runtime`
- (enhancement) included runtime stack fields in standard, text, CSV, HTML, SQLite, JSON and SARIF reports
- (enhancement) added `runtime_signals` storage to SQLite reports and runtime properties to SARIF results
- (enhancement) logo update
- (docs) documented runtime-aware fingerprinting and report fields
- (tests) added regression coverage for runtime detection and report propagation
- (tests) coverage gate remains configured at `99%`

v5.15.0 (02.05.2026)
---------------------------
- (feature) added SARIF 2.1.0 report output via `--reports sarif` for CI/CD security workflows
- (feature) SARIF reports are compatible with GitHub Code Scanning ingestion through `github/codeql-action/upload-sarif`
- (enhancement) mapped OpenDoor result buckets to stable SARIF rule identifiers and levels
- (enhancement) preserved URL, status code, response size, WAF, bypass and fingerprint metadata in SARIF result properties
- (enhancement) emitted target-level passive fingerprint metadata as a SARIF note result when `--fingerprint` data is available
- (docs) documented SARIF reports, GitHub Actions upload and CI/CD usage
- (tests) added SARIF reporter regression coverage
- (tests) coverage gate remains configured at `99%`

v5.14.6 (02.05.2026)
---------------------------
- (fix) avoided classifying passive Cloudflare CDN headers as blocked WAF responses
- (fix) preserved normal `301` and `404` classification for Cloudflare CDN responses so `--auto-calibrate` can build a usable baseline
- (fix) delayed `--waf-safe-mode` activation for isolated ordinary WAF blocks
- (fix) safe mode now activates immediately only for explicit challenge/rate-limit signals or after repeated blocked responses in a short rolling window
- (fix) blocked responses no longer trigger recursive expansion before safe mode activation
- (fix) preserved WAF safe-mode block-window state in session snapshots
- (tests) added regression coverage for passive Cloudflare CDN responses, isolated WAF blocks, threshold activation and immediate challenge/rate-limit activation
  
v5.14.5 (01.05.2026)
---------------------------
- (enhancement) expanded the passive `--fingerprint` catalog with selected regional CMS and site-builder signatures
- (enhancement) added InstantCMS, Duda, Hostinger Website Builder, CMS.S3 / Megagroup, Webasyst / Shop-Script, Discuz! and NetCat detection
- (enhancement) added strong HTTP-visible infrastructure signatures for Hostinger, DDoS-Guard and Tencent Cloud
- (enhancement) intentionally skipped DNS/ASN-only and weak URL-only providers to avoid false positives
- (docs) updated fingerprinting documentation and recognized technology examples
- (tests) added regression coverage for every new fingerprint signature
- (tests) full unittest suite passes after integration
- (tests) coverage gate passes at `99%`

v5.14.4 (01.05.2026)
---------------------------
- (enhancement) improved `--auto-calibrate` for subdomain scans with DNS wildcard calibration
- (enhancement) added random subdomain baseline probes to detect wildcard and catch-all DNS responses
- (enhancement) subdomain candidates that resolve only to wildcard baseline addresses are classified into the `calibrated` bucket before HTTP probing
- (enhancement) DNS wildcard calibration remains opt-in through `--scan subdomains --auto-calibrate` and does not change default scan behaviour
- (enhancement) DNS wildcard baseline addresses are preserved in session calibration state
- (tests) added regression coverage for DNS wildcard baseline detection, candidate matching and runtime filtering
- (tests) full unittest suite passes after integration
- (tests) coverage gate passes at `99%`

v5.14.3 (01.05.2026)
---------------------------
- (enhancement) improved `--auto-calibrate` with lightweight semantic response diffing for soft-404 detection
- (enhancement) added visible-text, semantic phrase, semantic term, DOM-token and text-density calibration signals
- (enhancement) improved dynamic body normalization for emails, path-like fragments and long encoded tokens
- (enhancement) semantic calibration remains opt-in through the existing `--auto-calibrate` flow and does not change default scan behaviour
- (tests) added regression coverage for semantic soft-404 matching and calibration helper edge cases
- (tests) full unittest suite passes after integration
- (tests) coverage gate passes at `99%`

v5.14.2 (01.05.2026)
---------------------------
- (enhancement) extended `--header-bypass` with controlled path-manipulation probes after header-injection probes
- (enhancement) added safe path-bypass variants: trailing slash, double leading slash, dot segment, semicolon suffix, case variation and URL-encoded segment
- (enhancement) path-bypass probes are strict opt-in through the existing `--header-bypass` flow and do not change default scan behaviour
- (enhancement) successful path-bypass candidates are stored in the existing `bypass` result bucket
- (enhancement) added path-bypass report metadata: `bypass=path`, `bypass_variant`, `bypass_value`, `bypass_url`, `bypass_from_code` and `bypass_to_code`
- (enhancement) JSON, HTML, CSV and SQLite reports preserve path-bypass evidence through detailed report items
- (tests) added regression coverage for path-bypass generation, runtime reporting and debug output branches
- (tests) full unittest suite passes after integration (`1221` tests)
- (tests) coverage gate passes at `99%`

v5.14.1 (01.05.2026)
---------------------------
- (enhancement) expanded target input parsing with IPv4 CIDR support for batch scans
- (enhancement) added inclusive IPv4 range expansion for `--hostlist` and `--stdin` workflows
- (enhancement) preserved mixed URL/domain/IP target files with deterministic deduplication before scanning
- (enhancement) multi-target scans now continue after per-target scan or transport errors and return exit code `1`
- (fix) documented CSV in the `--reports` help text

v5.14.0 (01.05.2026)
---------------------------
- (feature) added official Docker image distribution via GitHub Container Registry
- (feature) added automated Docker image publishing through GitHub Actions
- (feature) added multi-architecture Docker builds for `linux/amd64` and `linux/arm64`
- (feature) added release-based Docker tags: `latest`, full SemVer, `major.minor`, and `major`
- (feature) added SHA-based Docker tags for manual workflow runs
- (enhancement) added a minimal non-root Docker runtime for the OpenDoor CLI
- (enhancement) added `.dockerignore` to keep Docker build context clean and exclude local secrets, reports, caches and build artifacts
- (docs) documented Docker installation, version checks, report volume mounts and custom wordlist mounts
- (docs) updated installation and update documentation with Docker / GHCR usage
- (verification) Docker build passes locally
- (verification) GHCR workflow publish passes successfully
- (verification) anonymous GHCR pull works
- (verification) Dockerized `opendoor --version` works
- (verification) Dockerized `opendoor --help` works

v5.13.2 (01.05.2026)
---------------------------
- (enhancement) added visible progress output for `--fingerprint`
- (enhancement) extended CMS fingerprinting with a larger passive CMS catalog
- (enhancement) added additional CMS, e-commerce, site-builder and webmail detection signatures
- (enhancement) added passive fingerprint signals based on meta generator, HTTP headers, cookies and static markup markers
- (enhancement) kept extended fingerprinting lightweight without adding aggressive CMS probing
- (enhancement) removed foreign project-specific prefixes from internal fingerprint catalog names
- (enhancement) hardened wordlist orchestration for `--random-list`
- (enhancement) replace json2html conversion with built-in HTML report renderer
- (enhancement) preserve detailed report_items for WAF and header-bypass evidence
- (fix) fixed `--random-list` behavior on macOS when GNU `shuf` is not installed
- (fix) replaced shell-based `shuf` command construction with safe subprocess execution
- (fix) added Python shuffle fallback for systems without `shuf`
- (fix) fixed source wordlist line counting before temporary randomized list creation
- (fix) preserved external wordlist handling when randomization is enabled
- (fix) tightened boolean normalization for `random_list`, `extensions` and `ignore_extensions`
- (docs) updated fingerprinting documentation with the expanded CMS coverage
- (dependency) remove `json2html` from runtime and dev dependency checks
- (tests) added regression coverage for fingerprint progress rendering and callback flow
- (tests) added regression coverage for Sitecore, Microsoft SharePoint, BigCommerce and RoundCube Webmail detection
- (tests) added regression coverage for wordlist randomization backend selection and fallback behavior
- (tests) added regression coverage for external wordlist orchestration with randomization and extensions
- (tests) full unittest suite passes after integration (`1201python -m coverage report -m` tests)
- (tests) coverage gate passes at `99%`

v5.13.1 (30.04.2026)
---------------------------
- (enhancement) improved `--keep-alive` transport behaviour for HTTP and HTTPS scans
- (enhancement) non-default HTTP and HTTPS scan paths now reuse long-lived `PoolManager` instances instead of creating a new manager per request
- (enhancement) proxy mode now reuses cached proxy managers per proxy endpoint
- (enhancement) proxy-list scans now reuse `ProxyManager` and `SOCKSProxyManager` instances when the same proxy endpoint is selected again
- (enhancement) HTTPS connection pools now use blocking pool semantics aligned with HTTP pools
- (bugfix) fixed `keep_alive=False` being treated as enabled in browser configuration
- (bugfix) fixed shared request header mutation when applying `Connection: keep-alive`
- (bugfix) fixed ineffective keep-alive behaviour in proxy mode caused by per-request proxy manager creation
- (bugfix) fixed ineffective keep-alive behaviour in non-default HTTP and HTTPS paths caused by per-request `PoolManager` creation
- (bugfix) fixed lazy SOCKS proxy manager initialization check
- (tests) added regression coverage for keep-alive configuration parsing
- (tests) added regression coverage for HTTP and HTTPS keep-alive request behaviour
- (tests) added regression coverage for proxy manager reuse and SOCKS proxy initialization
- (tests) added regression coverage to ensure per-request headers do not mutate shared request headers
- (tests) full unittest suite passes after integration (`1178` tests)
- (tests) coverage gate passes at `99%`

v5.13.0 (29.04.2026)
---------------------------
- (feature) added controlled Header Injection Bypass via `--header-bypass`
- (feature) added per-header bypass probes for blocked `401` and `403` responses
- (feature) added `--header-bypass-headers` to customize header names used for bypass probes
- (feature) added `--header-bypass-ips` to customize trusted IP values used in bypass probes
- (feature) added `--header-bypass-status` to customize response status codes that trigger bypass probing
- (feature) added `--header-bypass-limit` to limit bypass probe variants per blocked URL, with `0` meaning unlimited
- (feature) added the `bypass` result bucket for successful header-injection bypass candidates
- (enhancement) header bypass probes are strict opt-in and do not affect default scan behaviour when disabled
- (enhancement) bypass probing runs as a controlled scanner extension instead of mutating global request headers
- (enhancement) HTTP, HTTPS and proxy request providers now support temporary per-request `extra_headers`
- (enhancement) temporary bypass headers are applied only to the current probe request and never leak into normal scan requests
- (enhancement) bypass detection records exact evidence: bypass type, header name, header value, original status code and resulting status code
- (enhancement) bypass scoring reports only meaningful status transitions, such as `401/403 -> 2xx/3xx` or another non-blocked response
- (enhancement) bypass probe generation is deterministic and supports path-based, host/origin, trusted-IP and URL-style header families
- (enhancement) header-bypass options are preserved in session checkpoints and restored through session resume flows
- (enhancement) bypass metadata is preserved in detailed report items
- (enhancement) TXT reports now include header-bypass evidence in bypass lines
- (enhancement) STD reports automatically include the `bypass` bucket in scan statistics
- (enhancement) JSON and HTML reports preserve full bypass metadata through `report_items`
- (enhancement) CSV reports now include `bypass`, `bypass_header`, `bypass_value`, `bypass_from_code` and `bypass_to_code` columns
- (enhancement) SQLite reports now persist bypass metadata in nullable item columns while preserving legacy payload compatibility
- (enhancement) legacy report formatting remains backward-compatible for plain URL-only items and WAF metadata
- (enhancement) header-bypass input validation rejects invalid header names and unsafe CRLF header values
- (enhancement) session resume, wizard and filtered option flows preserve explicit header-bypass CLI overrides
- (tests) added unittest coverage for header-bypass probe generation, limits, deduplication, scoring and metadata
- (tests) added regression coverage for CLI parsing, config normalization and option validation
- (tests) added regression coverage for HTTP, HTTPS and proxy per-request `extra_headers`
- (tests) added Browser runtime coverage for disabled mode, configured statuses, successful bypass candidates and empty probe responses
- (tests) added session export coverage for header-bypass settings
- (tests) added report coverage for TXT, JSON, HTML, CSV and SQLite bypass metadata
- (tests) added formatter edge coverage for WAF-only and partial bypass metadata variants
- (tests) full unittest suite passes after integration (`1177` tests)
- (tests) coverage gate passes at `99%`

v5.12.0 (28.04.2026)
---------------------------
- (feature) added Network Transport Profiles via `--transport`
- (feature) added common transport profile interface via `--transport-profile`
- (feature) added transport profile list support via `--transport-profiles`
- (feature) added sequential per-target VPN rotation via `--transport-rotate per-target`
- (feature) added OpenVPN transport support through `openvpn --config`
- (feature) added optional OpenVPN `auth-user-pass` support via `--openvpn-auth`
- (feature) added WireGuard transport support through `wg-quick up/down`
- (feature) added OS-level VPN tunnel routing for scan traffic
- (enhancement) existing HTTP/SOCKS proxy mode remains backward-compatible
- (enhancement) VPN transports can be combined with existing proxy and proxy-list workflows
- (enhancement) tunnel mode starts before `ping`, `fingerprint`, `auto-calibrate`, `scan` and `done`
- (enhancement) transport cleanup is guaranteed through `try/finally` on normal completion and scan errors
- (enhancement) multi-target scans can use one shared transport session when rotation is disabled
- (enhancement) per-target rotation runs targets sequentially to avoid unsafe parallel VPN route switching
- (enhancement) wizard and session resume flows preserve explicit transport CLI overrides
- (enhancement) added terminal notifications for transport start and stop events
- (enhancement) added transport options to `opendoor.conf`
- (enhancement) added `direct`, `proxy`, `openvpn`, and `wireguard` transport validation
- (enhancement) added mocked process runner for safe CI coverage without real VPN dependencies
- (tests) added unittest coverage for transport options, validation, adapters and process lifecycle
- (tests) added controller regression coverage for transport start/stop, scan failure cleanup and per-target rotation
- (tests) added filter regression coverage for transport/session/wizard option handling
- (tests) full unittest suite passes after integration (`1082` tests)
- (tests) coverage gate raised and passes at `99%`

v5.11.0 (28.04.2026)
---------------------------
- (feature) added smart auto-calibration via `--auto-calibrate`
- (feature) added baseline filtering for soft-404, wildcard and catch-all responses
- (feature) added `--calibration-samples` to control the number of random calibration probes
- (feature) added `--calibration-threshold` to control calibration match strictness
- (feature) added multi-signal calibration signatures based on status code, OpenDoor bucket, normalized body hash, HTML skeleton hash, title, redirect target, stable headers, size, word count and line count
- (feature) added `calibrated` result bucket for responses filtered by auto-calibration
- (enhancement) auto-calibration remains strict opt-in and does not change default scan behaviour when disabled
- (enhancement) auto-calibration forces `HEAD` to `GET` only when enabled because response body analysis is required
- (enhancement) dynamic response fragments such as UUIDs, timestamps, long numeric IDs, nonce and CSRF-like values are normalized before hashing
- (enhancement) calibration matches now preserve `calibration_score` and `calibration_reason` in detailed report items
- (enhancement) calibration baseline is persisted in session checkpoints and restored on resume
- (enhancement) auto-calibration options are preserved for wizard and session resume flows
- (enhancement) blocked WAF probe responses are skipped during calibration baseline creation
- (enhancement) failed calibration probes no longer stop the scan; OpenDoor safely continues without a usable baseline
- (enhancement) CI/CD `--fail-on-bucket` remains compatible with auto-calibration and can explicitly target the `calibrated` bucket
- (tests) added unittest coverage for calibration signatures, normalization, scoring, matching and fallback paths
- (tests) added regression coverage for Browser calibration runtime, session persistence and controller orchestration
- (tests) full unittest suite passes after integration (`999` tests)
- (tests) coverage gate passes at `98%`

v5.10.0 (28.04.2026)
---------------------------
- (feature) added CI/CD fail-on exit codes via `--fail-on-bucket`
- (feature) added optional pipeline failure rules for selected result buckets, e.g. `success,auth,forbidden,blocked`
- (feature) CI/CD mode now returns exit code `1` when configured buckets are found
- (enhancement) default scan exit behaviour remains unchanged when `--fail-on-bucket` is not used
- (enhancement) CI/CD fail-on rules are applied after all targets are scanned
- (enhancement) added `fail_on_bucket` support to wizard configuration
- (enhancement) added explicit CI/CD mode startup and final result messages
- (enhancement) `--fail-on-bucket` is preserved for wizard and session resume flows
- (enhancement) added CSV report plugin via `--reports csv`
- (enhancement) improved wizard configuration support for new scan options
- (enhancement) increased WAF safe mode cooldown on blocked and challenge responses
- (enhancement) added adaptive handling for `429` rate-limit responses
- (enhancement) added support for numeric `Retry-After` values on temporary `503` responses
- (enhancement) avoided treating plain `403 Forbidden` responses as rate limiting
- (enhancement) added gradual cooldown recovery after clean responses
- (enhancement) adaptive cooldown state is persisted in session checkpoints
- (dictionary) cleaned and normalized directories list
- (dictionary) refreshed subdomains wordlist with `+1251780` entries
- (tests) added unittest coverage for CI/CD fail-on exit codes
- (tests) added unittest coverage for adaptive cooldown behavior

v5.9.2 (27.04.2026)
---------------------------
- (dictionary) cleaned and normalized directories list
- (dictionary) cleaned and normalized browser user agents list
- (enhancement) added Open Journal Systems to fingerprints
- (enhancement) improved browser-like HTTP defaults for normal scan requests
- (enhancement) changed default `User-Agent` from `PostmanRuntime` to browser-like Chrome
- (enhancement) aligned default `Accept` and `Accept-Encoding` headers with browser document navigation
- (enhancement) generated `Referer` no longer includes default `:80` and `:443` ports
- (enhancement) generated `Origin` is no longer added by default for `GET` and `HEAD` requests
- (bugfix) reduced false positives in the `indexOf` sniffer
- (bugfix) fixed per-request user agent rotation with `--random-agent`
- (bugfix) fixed `ResponseError: Unknown response status : 411`
- (bugfix) fixed `ResponseError: Unknown response status : 509`
- (bugfix) custom headers from `--header` and `--raw-request` are no longer overwritten by generated defaults
- (bugfix) `--accept-cookies` now forwards only valid `name=value` cookie pairs from `Set-Cookie`
- (bugfix) cookie attributes such as `Path`, `HttpOnly`, `Secure`, `SameSite`, `Expires`, and `Max-Age` are no longer routed as request cookies
- (tests) added regression coverage for browser-like headers, custom header preservation and cookie routing

v5.9.1 (27.04.2026)
---------------------------
- (enhancement) added `--waf-safe-mode` for cautious scanning after WAF detection
- (enhancement) `--waf-safe-mode` automatically enables passive `--waf-detect`
- (enhancement) safe mode serializes follow-up requests after WAF detection and applies cooldown between requests
- (enhancement) blocked WAF responses no longer trigger recursive expansion while safe mode is active
- (enhancement) WAF safe mode state is persisted in session checkpoints and restored on resume
- (enhancement) added template warning for safe mode activation
- (tests) expanded regression coverage for WAF safe mode runtime, session restore and Browser branches
- (tests) full unittest suite passes after integration (`883` tests)

v5.9.0 (26.04.2026)
---------------------------
- (feature) added passive WAF / anti-bot recognition behind the opt-in `--waf-detect` flag
- (feature) added vendor-aware WAF identification with confidence scoring in debug output and reports
- (feature) added support for Anubis, Cloudflare, Sucuri, Akamai, Imperva, Distil, F5 BIG-IP ASM, AWS WAF, Azure Front Door, Fastly, ModSecurity, DataDome, PerimeterX / HUMAN, Kasada, Barracuda, Radware, FortiWeb, Reblaze, NetScaler / Citrix WAF, AppTrana, and Huawei Cloud WAF
- (enhancement) WAF detection remains strict opt-in and does not affect default scan behavior or performance without `--waf-detect`
- (enhancement) WAF metadata is preserved in standard debug output and detailed reports while keeping the response status as `blocked`
- (tests) expanded WAF coverage and stabilized passive recognition paths

v5.8.2 (26.04.2026)
---------------------------
- (dictionary) added `+11572` potential directories to the wordlist
- (enhancement) stabilized and expanded heuristic fingerprinting via `--fingerprint`
- (enhancement) improved infrastructure detection
- (enhancement) hardened collision handling for generic admin, backend, and assets patterns
- (enhancement) improved `--sniff indexof` detection across Apache, nginx, IIS, and generic directory listing layouts
- (enhancement) improved `--sniff collation` detection for repeated soft-404 and error templates
- (enhancement) improved `--sniff file` detection for explicit downloads, binary responses, and large bodies without `Content-Length`
- (enhancement) improved `--sniff skipempty` to skip only truly empty or semantically empty short responses
- (enhancement) improved `--sniff skipsizes` with safer size handling, invalid header fallback, and KB range support
- (bugfix) fixed false positives in sniff plugins for short login pages, short useful JSON responses, and binary placeholders
- (bugfix) fixed backward compatibility regressions in `CollationResponsePlugin`
- (tests) added negative regression coverage to reduce false positives
- (tests) expanded coverage for `file`, `indexof`, `collation`, `skipempty`, and `skipsizes`
- (tests) full unittest suite passes after integration (`790` tests)

v5.8.1 (23.04.2026)
---------------------------
- (feature) extended fingerprinting via `--fingerprint` with better defined Node/API backend stack detection
- (feature) extended fingerprinting via `--fingerprint` with better defined e-commerce and CMS detection
- (feature) extended fingerprinting via `--fingerprint` with better defined docs and static tooling detection
- (feature) extended reporting via `--reports` by adding the `sqlite` report format
- (bugfix) fixed `ResponseError: Unknown response status : 511`

v5.8.0 (23.04.2026)
---------------------------
- (feature) added persistent scan sessions with `--session-save` and `--session-load`
- (feature) added checkpoint autosave controls via `--session-autosave-sec` and `--session-autosave-items`
- (feature) added logical scan state restore for pending queue, processed items, recursive state, and partial results
- (feature) added session snapshot validation with schema version checks and checksum verification
- (feature) added atomic session writes with `.tmp` swap and `.bak` fallback recovery
- (feature) added controller-level restore flow so resumed scans continue from saved session state instead of restarting from zero
- (enhancement) kept persistent sessions strictly opt-in: no session file is created or updated unless session mode is explicitly enabled
- (enhancement) hardened browser runtime so legacy non-session flows and existing pause/resume behavior remain unchanged when session mode is disabled
- (enhancement) improved session compatibility across interrupted scans, graceful stops, and resumed executions
- (tests) expanded regression coverage across browser session lifecycle, controller restore flow, config accessors, and session file validation
- (tests) coverage gate now passes at `98%`

v5.7.0 (22.04.2026)
---------------------------
- (feature) added `--fingerprint` to run heuristic technology fingerprinting before the main scan
- (feature) added probable application stack detection for popular CMS, ecommerce platforms, frameworks, site builders, and static-site tooling
- (feature) added infrastructure fingerprinting for AWS CloudFront, S3, ELB/ALB, API Gateway, Amplify, Cloudflare, Vercel, Netlify, GitHub Pages, GitLab Pages, Heroku, Azure, Google Cloud, Fastly, Akamai, and OpenResty
- (feature) added fingerprint summary fields to the standard report output, including application category, name, confidence, infrastructure provider, and infrastructure confidence
- (ux) fingerprinting now runs after connectivity checks and before the main scan without breaking the existing scan pipeline
- (tests) added regression coverage for fingerprint detection rules, runtime browser integration, controller orchestration, and report rendering
- (tests) full unittest suite passes after integration (`679` tests)

v5.6.0 (22.04.2026)
---------------------------
- (feature) added `--raw-request` to load raw HTTP request templates from a file
- (feature) added `--scheme` to resolve relative raw request lines with explicit `http` or `https` scheme selection
- (feature) added raw-request parsing for request method, host, port, headers, cookies, body, and derived path prefix
- (feature) added host fallback from raw requests when `--host`, `--hostlist`, or `--stdin` are not provided
- (feature) added raw-request merge behavior where CLI `--host`, `--method`, `--header`, `--cookie`, `--prefix`, and `--port` override template defaults
- (ux) preserved explicit non-`HEAD` methods for raw-request templates while keeping legacy `HEAD -> GET` overrides only for body-required sniffers and filters
- (tests) added regression coverage for raw-request option parsing, filter normalization, browser config exposure, and HTTP/HTTPS request body forwarding
- (tests) full unittest suite passes after integration (`610` tests)

v5.5.0 (21.04.2026)
---------------------------
- (feature) added response filter flags: `--include-status`, `--exclude-status`, `--exclude-size`, `--exclude-size-range`, `--match-text`, `--exclude-text`, `--match-regex`, `--exclude-regex`, `--min-response-length`, and `--max-response-length`
- (feature) added HTTP status range support for response filtering, e.g. `200-299,301,302,403`
- (feature) added exact size and inclusive byte-range filtering for noisy responses and false positives
- (feature) added body text and regex response filtering for more precise discovery workflows
- (ux) automatically overrides explicit `HEAD` to `GET` when selected response filters require response body access
- (tests) added regression coverage for response filter option parsing, validation, browser config normalization, and browser filtering behavior
- (tests) full unittest suite passes after integration (`585` tests)

v5.4.0 (21.04.2026)
---------------------------
- (feature) added `--hostlist` support for multi-target scanning from a file
- (feature) added `--stdin` support for reading targets from standard input
- (feature) added mutually exclusive target source validation for `--host`, `--hostlist`, and `--stdin`
- (feature) added target normalization, comment skipping, empty-line skipping, and deduplication
- (feature) added sequential multi-target scan orchestration without breaking the single-host flow
- (tests) added regression coverage for target source parsing in options and filters
- (tests) added controller coverage for multi-target scan execution
- (tests) full unittest suite passes after integration

v5.3.1 (21.04.2026)
---------------------------
- (bugfix) fixed SOCKS proxy runtime support by adding `PySocks` as a required dependency
- (bugfix) added support for the `socks://` proxy alias and normalized it to `socks5://`
- (bugfix) fixed proxy normalization for standalone `--proxy` usage and proxy list entries
- (tests) added regression coverage for SOCKS proxy alias handling and missing `PySocks` dependency behavior
- (build) refreshed package metadata and distribution artifacts for the `5.3.1` patch release

v5.3.0 (21.04.2026)
---------------------------
- (feature) added `--header` to send custom request headers from CLI
- (feature) added `--cookie` to send custom request cookies from CLI
- (feature) added request provider support for multiple custom headers and cookies
- (docs) updated `README.md` and `docs/Usage.md` for custom request metadata and refreshed CLI help examples
- (tests) added custom request headers and cookies integration coverage

v5.2.0 (20.04.2026)
---------------------------
- (feature) added recursive directory scan support
- (feature) added configurable recursion depth via `--recursive-depth`
- (feature) added configurable HTTP status allowlist for recursive expansion via `--recursive-status`
- (feature) added configurable excluded extensions for recursive expansion via `--recursive-exclude`
- (optimization) browser request flow is now depth-aware for recursive workloads
- (optimization) ThreadPool total items can be extended for recursive workloads
- (docs) updated `README.md` and `docs/Usage.md` for recursive scan support and refreshed CLI help output
- (tests) expanded test suite to `546` tests with recursive browser, config, and thread-pool coverage

v5.1.0 (20.04.2026)
---------------------------
- (feature) added response size to exported `txt`, `html`, and `json` reports ([#35](https://github.com/stanislav-web/OpenDoor/issues/35))
- (feature) added response code output support ([#39](https://github.com/stanislav-web/OpenDoor/issues/39))
- (dictionary) populated directories with `+27965` unique actual paths
- (bugfix) report plugins now create nested target directories correctly, e.g. `reports/example.com` instead of `reportsexample.com`
- (bugfix) fixed BOM decoding behavior in helper utilities and aligned tests with the corrected implementation
- (optimization) refactored `FileSystem.readline()` to batch-load lines with much lower peak memory usage
- (optimization) optimized `Reader.get_lines()` hot path by precomputing handler params and reducing repeated string formatting work
- (optimization) optimized `ThreadPool.add()` submit-side accounting using submitted task tracking
- (optimization) kept `Reader` extension filters on the fast in-memory path after benchmark validation
- (optimization) updated benchmark workflow documentation and project maintenance flow
- (optimization) fixed benchmark callback accounting for batched `readline()` processing
- (optimization) improved compatibility of terminal, color, logger exception, and rainbow logger behavior under tests
- (tests) expanded test suite to `400+` tests
- (tests) added regression tests and edge case coverage for report size propagation
- (tests) added broad unit test coverage across core, HTTP, reporter, browser, proxy, socket, logger, terminal, color, and filesystem modules

v5.0.1 (19.04.2026)
---------------------------
- (docs) updated Read the Docs badge to the current badge endpoint
- (docs) removed stale Codespaces Prebuilds badge that no longer resolves
- (docs) refreshed documentation stack for the current Read the Docs / MkDocs workflow
- (docs) reduced `docs/requirements.txt` to the active MkDocs-based documentation stack
- (docs) updated `.readthedocs.yaml` for current Read the Docs configuration
- (docs) refreshed documentation pages for the modern packaging and installation flow
- (bugfix) docs build now aligns with the current project packaging and supported Python baseline

v5.0.0 (19.04.2026)
---------------------------
- (feature) added `pyproject.toml` for modern Python packaging workflow
- (feature) added source and wheel build support through `python -m build`
- (feature) added refreshed `MANIFEST.in` for correct source distribution contents
- (feature) added `AGENTS.md` for contributor and agent workflow guidance
- (feature) added `Ruff` baseline for lightweight Python linting
- (enhancement) updated Python support baseline to `3.12`, `3.13`, and `3.14`
- (enhancement) modernized package build and install flow for the current Python ecosystem
- (enhancement) refreshed CLI update and version behavior for modern environments
- (enhancement) clarified help text and install flow documentation
- (enhancement) refreshed test suite for modern Python runtime and standard library mocks
- (enhancement) refreshed development dependencies to current maintained versions
- (bugfix) fixed build issues for source and wheel distribution generation
- (bugfix) fixed packaging metadata and install paths for modern setuptools and pip workflows
- (bugfix) fixed tests depending on external shell and network behavior
- (bugfix) fixed CLI banner rendering and package installation checks
- (planning) planned deeper refactoring, additional tests, warning cleanup, and internal code improvements

v4.2.0 (29.07.2023)
---------------------------
- (bugfix) `--sniff skipempty,skipsizes=NUM:NUM...` now moves pages to ignore in reports instead of only skipping them
- (bugfix) invalid response statuses received because of invalid headers are now passed through correctly
- (bugfix) fixed `--accept-cookie` so server-provided cookies are accepted and routed correctly while surfing
- (enhancement) moved Keep-Alive connection type control to a separate `--keep-alive` parameter
- (optimization) optimized `directories_count` and `subdomains_count` operations to reduce RAM usage
- (dictionary) removed `-262` trash entries from the internal directories wordlist
- (dictionary) optimized internal `directories.txt` by sorting entries and removing trash lines

v4.1.0 (07.07.2023)
---------------------------
- (feature) added `--sniff skipsizes=25:60:101:...` to skip redirect-to-200 pages that represent not-found responses
- (feature) added `+20` new directories to the internal wordlist
- (feature) added `+74242` new subdomains to the internal wordlist
- (bugfix) increased `--sniff skipempty` threshold to detect empty content up to `500` bytes instead of `100` bytes
- (bugfix) fixed `ResponseError: Unknown response status : 525` by defining incorrect SSL handshake responses
- (bugfix) fixed `Object of type HTTPHeaderDictItemView is not JSON serializable` when `--debug` is set to `3`
- (bugfix) fixed `--accept-cookies` to accept and route cookies from responses
- (bugfix) fixed gzip response decoding failures for malformed `Content-Encoding: gzip` responses
- (dictionary) optimized internal `directories.txt` by sorting entries and removing trash lines

v4.0.61 (30.06.2023)
---------------------------
- (dictionary) added `+1007` directories
- (dictionary) optimized `directories.txt` by sorting entries and removing trash lines
- (bugfix) fixed `HTTPConnection.__init__() got an unexpected keyword argument 'cert_reqs'` ([#64](https://github.com/stanislav-web/OpenDoor/issues/64))

v4.0.6 (26.06.2023)
---------------------------
- (docs) recreated documentation portal
- (docs) kept documentation up to date
- (build) published package on PyPI

v4.0.5 (25.06.2023)
---------------------------
- (bugfix) fixed unit tests
- (build) resolved development requirements

v4.0.4-stable (24.06.2023)
---------------------------
- (bugfix) fixed unit tests
- (build) resolved development requirements

v4.0.3 (24.06.2023)
-------------------
- (bugfix) fixed invalid SSL handling by ignoring invalid SSL by default ([#44](https://github.com/stanislav-web/OpenDoor/issues/44))

v4.0.2 (23.06.2023)
-------------------
- (bugfix) fixed Python `3.11` launch by adding encoding to `setup.py` ([#58](https://github.com/stanislav-web/OpenDoor/issues/58))

v4.0.1-beta (23.02.2021)
------------------------
- (breaking) removed support for Python `2.6` and `2.7`
- (dictionary) updated `directories.dat` from `36994` to `37019`
- (enhancement) added encoding to `setup.py` ([#40](https://github.com/stanislav-web/OpenDoor/issues/40))
- (bugfix) fixed Python `3.9` and `3.10` compatibility ([#48](https://github.com/stanislav-web/OpenDoor/issues/48))
- (bugfix) fixed missing request timeout setup ([#20](https://github.com/stanislav-web/OpenDoor/issues/20))
- (enhancement) added support for showing only found items ([#36](https://github.com/stanislav-web/OpenDoor/issues/36))

v3.4.481-stable (02.10.2017)
----------------------------
- (bugfix) fixed bugs with external wordlists
- (dictionary) added `80018` subdomains

v3.4.47-rc Gained more Power! (05.07.2017)
------------------------------------------
- (feature) added IP lookup for subdomain scans
- (feature) added Internationalized Domain Names support via IDNA
- (feature) added `--ignore-extensions` / `-i` to ignore selected extensions
- (feature) added `--sniff indexof` to detect Apache `Index Of` directories
- (feature) added `--sniff file` to detect large files
- (feature) added `--sniff collation` to heuristically detect invalid web pages
- (feature) added `--sniff skipempty` to skip empty valid pages
- (bugfix) added missing HTTP statuses
- (bugfix) fixed encoding errors for body analysis with `cp1251`, `utf8`, and `utf16`
- (bugfix) allowed using both `--random-list` and `--extension` parameters together
- (enhancement) removed directory closing slash from generated paths
- (breaking) removed legacy `--indexof` / `-i` parameter
- (dictionary) filtered internal dictionaries and removed duplicates
- (dictionary) added `+990` unique directories (`36931` total)

v3.3.37-rc (22.06.2017)
------------------------
- (feature) added config wizard for configuring a project
- (bugfix) fixed errors

v3.2.36-rc (04.06.2017)
------------------------
- (feature) added custom reports directory via `--reports-dir /home/user/Reports`
- (feature) added user guide access via `--docs`
- (feature) added reusable proxy request pooling for `--tor` and `--torlist`
- (enhancement) optimized scan execution
- (enhancement) request delays now support milliseconds
- (bugfix) prevented SOCKS5 proxy warnings
- (breaking) removed Python `2.7` support

v3.1.32-rc (02.06.2017)
------------------------
- (feature) added extension filtering via `--extensions php,json`

v3.0.32-rc (19.05.2017)
-----------------------
- (feature) added global installation support

v3.0.31-rc (20.02.2017)
------------------------
- (dictionary) updated directories
- (bugfix) fixed redirects

v3.0.3-rc (17.02.2017)
-----------------------
- (bugfix) fixed HTTPS scan issues
- (dictionary) cleared internal wordlists
- (tests) increased test coverage

v3.0.3-beta (13.02.2017)
-------------------------
- (feature) added SSL certificate requirement detection
- (dictionary) added `7150` directories
- (bugfix) fixed HTTPS subdomain handling
- (tests) increased unit coverage

v3.0.2-beta (31.01.2017)
------------------------
- (feature) added multiple reporters: `std`, `txt`, `json`, and `html`
- (feature) added external wordlist support
- (feature) added external proxy list support
- (feature) added wordlist shuffling
- (feature) added wordlist prefixes
- (feature) added multithreading control
- (feature) added dynamic and smart requests with cookies and accept headers
- (feature) added Apache `Index Of` and file detection
- (enhancement) improved user-friendly interface
- (optimization) optimized internal code
- (cleanup) removed unnecessary dependencies

v2.7.96 - v1.0.0 (05.01.2017)
------------------------------
- (feature) v1.0.0: basic functionality became available
- (feature) v1.0.1: added debug level via `--debug`
- (feature) v1.2.1: added filesystem logger via `--log`
- (feature) v1.2.2: added usage examples via `--examples`
- (feature) v1.3.2: added random proxy selection from proxy list via `--proxy`
- (enhancement) v1.3.3: simplified dependency installation
- (cleanup) v1.3.51: fixed code style and resolved file read errors
- (docs) v1.3.52: added code documentation style
- (feature) v2.3.52: added subdomain scan support via `--check subdomains`
- (feature) v2.4.62: added custom port support via `--port 8080`
- (feature) v2.5.62: added HTTPS support
- (feature) v2.7.62: added redirect handler beta
- (feature) v2.7.92: added exclusion list at `Data/exclusions.dat`
- (feature) v2.7.95: added large file definitions and bad request detection handler
- (bugfix) v1.3.5: added `ReadTimeoutError` and `ProxyError` handlers
- (bugfix) v2.3.54: fixed thread-related errors and refactored related code
- (dictionary) v2.6.62: added `19000` possible directories
- (dictionary) v2.7.72: added `52` directories
- (dictionary) v2.7.82: added `683` directories
- (ux) v2.7.72: added small UI changes
- (optimization) v2.7.96: optimized debug levels (`0`, `1`, `2`) via `--debug` and optimized imports
