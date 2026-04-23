Changelog
=========
v5.8.1 (23.04.2026)
---------------------------
- (feature) Extend fingerprinting (`--fingerpring`). Better defined Node/API backend stack
- (feature) Extend fingerprinting (`--fingerpring`). Better defined e-commerce/CMS
- (feature) Extend fingerprinting (`--fingerpring`). Better defined docs/static tooling
- (feature) Extend reporting (`--reports`) by adding `sqlite` report format
- (bugfix) ResponseError: Unknown response status : `511`

v5.8.0 (23.04.2026)
---------------------------
- (feature) Added persistent scan sessions with `--session-save` and `--session-load`.
- (feature) Added checkpoint autosave controls: `--session-autosave-sec` and `--session-autosave-items`.
- (feature) Added logical scan state restore for pending queue, processed items, recursive state and partial results.
- (feature) Added session snapshot validation with schema version checks and checksum verification.
- (feature) Added atomic session writes with `.tmp` swap and `.bak` fallback recovery.
- (feature) Added controller-level restore flow so resumed scans continue from saved session state instead of restarting from zero.
- (feature) Kept persistent sessions strictly opt-in: no session file is created or updated unless session mode is explicitly enabled.
- (improvement) Hardened browser runtime so legacy non-session flows and existing pause/resume behavior remain unchanged when session mode is disabled.
- (improvement) Improved session compatibility across interrupted scans, graceful stops and resumed executions.
- (tests) Expanded regression coverage across browser session lifecycle, controller restore flow, config accessors and session file validation.
- (tests) Coverage gate now passes at 98%.

v5.7.0 (22.04.2026)
---------------------------
- (feature) Added `--fingerprint` to run heuristic technology fingerprinting before the main scan.
- (feature) Added probable application stack detection for popular CMS, ecommerce platforms, frameworks, site builders, and static-site tooling.
- (feature) Added infrastructure fingerprinting for AWS (CloudFront, S3, ELB/ALB, API Gateway, Amplify), Cloudflare, Vercel, Netlify, GitHub Pages, GitLab Pages, Heroku, Azure, Google Cloud, Fastly, Akamai, and OpenResty.
- (feature) Added fingerprint summary fields to the standard report output, including application category/name/confidence and infrastructure provider/confidence.
- (ux) Fingerprinting now runs after connectivity checks and before the main scan without breaking the existing scan pipeline.
- (tests) Added regression coverage for fingerprint detection rules, runtime browser integration, controller orchestration, and report rendering.
- (tests) Full unittest suite passes after integration (`679` tests).

v5.6.0 (22.04.2026)
---------------------------
- (feature) Added `--raw-request` to load raw HTTP request templates from a file.
- (feature) Added `--scheme` to resolve relative raw request lines with explicit `http` or `https` scheme selection.
- (feature) Added raw-request parsing for request method, host, port, headers, cookies, body, and derived path prefix.
- (feature) Added host fallback from raw requests when `--host`, `--hostlist`, or `--stdin` are not provided.
- (feature) Added raw-request merge behavior where CLI `--host`, `--method`, `--header`, `--cookie`, `--prefix`, and `--port` override template defaults.
- (ux) Preserved explicit non-`HEAD` methods for raw-request templates while keeping legacy `HEAD -> GET` overrides only for body-required sniffers and filters.
- (tests) Added regression coverage for raw-request option parsing, filter normalization, browser config exposure, and HTTP/HTTPS request body forwarding.
- (tests) Full unittest suite passes after integration (`610` tests).

v5.5.0 (21.04.2026)
---------------------------
- (feature) Added response filter flags: `--include-status`, `--exclude-status`, `--exclude-size`, `--exclude-size-range`, `--match-text`, `--exclude-text`, `--match-regex`, `--exclude-regex`, `--min-response-length`, and `--max-response-length`.
- (feature) Added HTTP status range support for response filtering, e.g. `200-299,301,302,403`.
- (feature) Added exact size and inclusive byte-range filtering for noisy responses and false positives.
- (feature) Added body text and regex response filtering for more precise discovery workflows.
- (ux) Automatically override explicit `HEAD` to `GET` when selected response filters require response body access.
- (tests) Added regression coverage for response filter option parsing, validation, browser config normalization, and browser filtering behavior.
- (tests) Full unittest suite passes after integration (`585` tests).

v5.4.0 (21.04.2026)
---------------------------
- (feature) `--hostlist` support for multi-target scanning from a file
- (feature) `--stdin` support for reading targets from standard input
- (feature) mutually exclusive target source validation for `--host`, `--hostlist`, and `--stdin`
- (feature) target normalization, comment skipping, empty-line skipping, and deduplication
- (feature) sequential multi-target scan orchestration without breaking the single-host flow
- (tests) Added regression coverage for target source parsing in options/filter
- (tests) Added controller coverage for multi-target scan execution
- (tests) Full unittest suite passes after integration


v5.3.1 (21.04.2026)
---------------------------
- (fix) Fixed SOCKS proxy runtime support by adding `PySocks` as a required dependency.
- (fix) Added support for `socks://` proxy alias and normalized it to `socks5://`.
- (fix) Fixed proxy normalization for both standalone `--proxy` usage and proxy list entries.
- (tests) Added regression tests for SOCKS proxy alias handling and missing `PySocks` dependency behavior.
- (build) Refreshed package metadata and distribution artifacts for the `5.3.1` patch release.

v5.3.0 (21.04.2026)
---------------------------
- Added: `--header` to send custom request headers from CLI.
- Added: `--cookie` to send custom request cookies from CLI.
- Added: request provider support for multiple custom headers and cookies.
- Added: tests for custom request headers and cookies integration.
- Changed: `README.md` and `docs/Usage.md` updated for custom request metadata and refreshed CLI help examples.

v5.2.0 (20.04.2026)
---------------------------
- Added: recursive directory scan support
- Added: `--recursive-depth` for configurable recursion depth
- Added: `--recursive-status` for configurable recursive expansion status codes
- Added: `--recursive-exclude` for configurable recursive extension exclusions
- Changed: Browser request flow is now depth-aware for recursive scans
- Changed: ThreadPool total items may be extended for recursive workloads
- Changed: `README.md` and `docs/Usage.md` refreshed for recursive scan usage and updated CLI help output
- Tests: browser, config, and thread-pool coverage expanded for recursive scan behavior
- Tests: full suite now runs 546 passing tests

v5.1.0 (20.04.2026)
---------------------------
- (feature)[#35](https://github.com/stanislav-web/OpenDoor/issues/35) Added response size to exported `txt`, `html`, and `json` reports.
- (feature)[#39](https://github.com/stanislav-web/OpenDoor/issues/39) Feature Request: Output response codes
- (feature) Populated directories by adding new unique +27965 actual paths
- (bugfix) Report plugins now create nested target directories correctly, e.g. `reports/example.com` instead of `reportsexample.com`.
- (bugfix) Fixed BOM decoding behavior in helper utilities and aligned tests with the corrected implementation.
- (optimization) Refactored `FileSystem.readline()` to batch-load lines with much lower peak memory usage.
- (optimization) Optimized `Reader.get_lines()` hot path by precomputing handler params and reducing repeated string formatting work.
- (optimization) Optimized `ThreadPool.add()` submit-side accounting using submitted task tracking.
- (optimization) Kept `Reader` extension filters on the fast in-memory path after benchmark validation.
- (optimization) Updated benchmark workflow documentation and project maintenance flow.
- (optimization) Fixed benchmark callback accounting for batched `readline()` processing.
- (optimization) Improved compatibility of terminal, color, logger exception, and rainbow logger behavior under tests.
- (tests) Test suite expanded to 400+ tests.
- (tests) Added regression tests and edge case coverage for report size propagation.
- (tests) Added broad unit test coverage across core, HTTP, reporter, browser, proxy, socket, logger, terminal, color, and filesystem modules.

v5.0.1 (2026-04-19)
---------------------------
- Fixed: Read the Docs badge updated to the current badge endpoint
- Removed: stale Codespaces Prebuilds badge that no longer resolves
- Changed: documentation stack refreshed for current Read the Docs / MkDocs workflow
- Changed: `docs/requirements.txt` reduced to the active MkDocs-based documentation stack
- Changed: `.readthedocs.yaml` updated for current RTD configuration
- Changed: documentation pages refreshed for the modern packaging and installation flow
- Fixed: docs build now aligns with the current project packaging and supported Python baseline

v5.0.0 (2026-04-19)
---------------------------
- Added: `pyproject.toml` for modern Python packaging workflow
- Added: source and wheel build support through `python -m build`
- Added: refreshed `MANIFEST.in` for correct source distribution contents
- Added: `AGENTS.md` for contributor and agent workflow guidance
- Added: `Ruff` baseline for lightweight Python linting
- Changed: Python support baseline updated to `3.12`, `3.13`, `3.14`
- Changed: package build/install flow modernized for current Python ecosystem
- Changed: CLI update/version behavior refreshed for modern environments
- Changed: help text and install flow documentation clarified
- Changed: test suite refreshed for modern Python runtime and standard library mocks
- Changed: development dependencies refreshed to current maintained versions
- Fixed: build issues for source and wheel distribution generation
- Fixed: packaging metadata and install paths for modern setuptools/pip workflows
- Fixed: tests depending on external shell and network behavior
- Fixed: CLI banner rendering and package installation checks

v4.2.0 (2023-07-29)
---------------------------
- Fixed: `--sniff skipempty,skipsizes=NUM:NUM...` moved pages to ignore in reports instead of just skipping
- Fixed: invalid response statuses received because of invalid headers were passed
- Fixed: `--accept-cookies` behavior when cookies were provided by the server
- Optimized internal directories and subdomains counters to reduce RAM usage
- Removed: trash entries from the built-in directories list
- Changed: keep-alive support moved to a dedicated `--keep-alive` parameter

v4.1.x and older
---------------------------
Earlier historical releases remain part of the project history and Git tags.

For older details, see:
- Git tags in the repository
- PyPI release history
- commit history on GitHub
