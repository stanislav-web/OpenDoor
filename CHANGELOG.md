CHANGELOG
=======
v5.8.2 (25.04.2026)
---------------------------
- (enhancement) heuristic fingerprinting ( `--fingerprint` stabilizes and expands)
- (enhancement) improved infrastructure detection
- (enhancement) collision hardening for generic admin/backend/assets patterns
- (tests) negative regression coverage to reduce false positives

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
- 
v5.3.0 (21.04.2026)
---------------------------
- Added: `--header` to send custom request headers from CLI.
- Added: `--cookie` to send custom request cookies from CLI.
- Added: request provider support for multiple custom headers and cookies.
- Added: tests for custom request headers and cookies integration.
- Changed: `README.md` and `docs/Usage.md` updated for custom request metadata and refreshed CLI help examples.

v5.2.0 (20.04.2026)
---------------------------
- (feature) Added recursive directory scan support.
- (feature) Added configurable recursion depth via `--recursive-depth`.
- (feature) Added configurable HTTP status allowlist for recursive expansion via `--recursive-status`.
- (feature) Added configurable excluded extensions for recursive expansion via `--recursive-exclude`.
- (optimization) Browser request flow is now depth-aware for recursive workloads.
- (optimization) ThreadPool total items can be extended for recursive workloads.
- (docs) Updated `README.md` and `docs/Usage.md` for recursive scan support and refreshed CLI help output.
- (tests) Test suite expanded to 546 tests with recursive browser/config/thread-pool coverage.

v5.1.0 (20.04.2026)
---------------------------
- (feature)[#35](https://github.com/stanislav-web/OpenDoor/issues/35) Added response size to exported `txt`, `html`, and `json` reports.
- (feature)[#39](https://github.com/stanislav-web/OpenDoor/issues/39) Feature Request: Output response codes
- (feature) Populated directories by adding new unique +27965 actual paths
- (bugfix) Report plugins now create nested target directories correctly, e.g. `reports/example.com` instead of `reportsexample.com`.
- (bugfix)Fixed BOM decoding behavior in helper utilities and aligned tests with the corrected implementation.
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

v5.0.1 (19.04.2026)
---------------------------
- Fixed: Read the Docs badge updated to the current badge endpoint
- Removed: stale Codespaces Prebuilds badge that no longer resolves
- Changed: documentation stack refreshed for current Read the Docs / MkDocs workflow
- Changed: `docs/requirements.txt` reduced to the active MkDocs-based documentation stack
- Changed: `.readthedocs.yaml` updated for current RTD configuration
- Changed: documentation pages refreshed for the modern packaging and installation flow
- Fixed: docs build now aligns with the current project packaging and supported Python baseline

v5.0.0 (19.04.2026)
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
- Planned next: deeper refactoring, additional tests, warnings cleanup and internal code improvements

v4.2.0 (29.07.2023)
---------------------------
- Fixed: `--sniff skipempty,skipsizes=NUM:NUM...` moved pages to ignore in reports instead of just skipping
- Fixed: invalid response statuses received because of invalid headers were passed
- Fixed: --accept-cookie param. Now it is working correctly if the server provided Cookies for surfing
- Optimized `directories_count` and `subdomains_count` operation to reduce RAM usage.
- Removed: `-262` directories from internal wordlist because of trash
- Edit Keep-Alive connection type moved to a separate parameter `--keep-alive`
- Optimized internal wordlist directories.txt list (sort, removed trash lines)

v4.1.0 (07.07.2023)
---------------------------
-   Added `--sniff skipsizes=25:60:101:...`: allow skipping redirect to 200 OK pages which not found
-   Fixed `--sniff skipempty`: increase condition value to detect empty content <= 500 bytes detect as empty page instead of 100 bytes
-   Fixed `ResponseError: Unknown response status : 525`: added to define incorrect SSL handshakes
-   Fixed `Object of type HTTPHeaderDictItemView is not JSON serializable`: if `--debug` set `3`
-   Fixed `--accept-cookies` param. (Accept and route cookies from responses)
-   Fixed response encode failed`('Received response with content-encoding: gzip, but failed to decode it.', error('Error -3 while decompressing data: incorrect header check'))`
-   Added `+20` new directories to internal wordlist
-   Added `+74242` new subdomains to internal wordlist
-   Optimize internal wordlist directories.txt list (sort, removed trash lines)

v4.0.61 (30.06.2023)
---------------------------
-   Added +1007 directories
-   Optimize directories.txt list (sort, removed trash lines)
-   Fix [#ISSUE-64](https://github.com/stanislav-web/OpenDoor/issues/64) HTTPConnection.__init__() got an unexpected keyword argument 'cert_reqs'

v4.0.6 (26.06.2023)
---------------------------
-   Re-create documentation portal. Keep docs up to date. Publish on Pypi

v4.0.5 (25.06.2023)
---------------------------
-   Fix unit tests and resolve dev requirements

v4.0.4-stable (24.06.2023)
---------------------------
-   Fix unit tests and resolve dev requirements

v4.0.3 (24.06.2023)
-------------------
-   Fix [#ISSUE-44](https://github.com/stanislav-web/OpenDoor/issues/44) ignore invalid SSL by default

v4.0.2 (23.06.2023)
-------------------
-   Python 3.11 launch fix [#ISSUE-58](https://github.com/stanislav-web/OpenDoor/issues/58) added encoding to setup.py 

v4.0.1-beta (23.02.2021)
------------------------
-   Python 2.6,2.7 is unsupported
-   Update directories.dat  36994 -> 37019
-   [enhancement] [#PR-40](https://github.com/stanislav-web/OpenDoor/issues/40) added encoding to setup.py 
-   [bugfix] [#PR-48](https://github.com/stanislav-web/OpenDoor/issues/48) Python 3.9 / 3.10 compatibility
-   [bugfix] [#PR-20](https://github.com/stanislav-web/OpenDoor/issues/20) No timeout setup in request
-   [enhancement] [#PR-36](https://github.com/stanislav-web/OpenDoor/issues/36) Feature Request: Show only found items

v3.4.481-stable (02.10.2017)
----------------------------
-   Fixed bugs with externals wordlists
-   Added 80018 subdomains

v3.4.47-rc Gained more Power! (05.07.2017)
------------------------------------------
- Added IPs lookup for subdomain scans
- Added missing HTTP statuses
- Bugfix: encoding errors (supported cp1251,utf8,utf16) for body analyze
- Bugfix: allow to use both --random-list & --extension params
- Directory closing slash has been removed
- Support Internationalized Domain Names IDNA
- Removed --indexof (-i) params
- Add --ignore-extensions -i param to ignore a selected extension
- Added --sniff param to process responses
    - indexof   (detect Apache Index Of/ directories)
    - file      (detect large files)
    - collation (heuristic detect invalid web pages)
    - skipempty (skip empty valid pages)
- Internal dictionaries have been filtered out. Delete all duplicates
- Added +990 unique directories (36931)

v3.3.37-rc (22.06.2017)
------------------------
- Fixed errors
- Add config wizard (allows you to configure an own project)
    
v3.2.36-rc (04.06.2017)
------------------------
- Added custom reports directory --reports-dir /home/user/Reports
- Added user guide --docs
- Reusable proxy requests pooling in --tor, --torlist
- Prevent socks5 proxy warnings
- Optimizing scan execution
- Request delays allow using of milliseconds
- Python2.7 no longer support

v3.1.32-rc (02.06.2017)
------------------------
- Add extensions filter --extensions php,json etc

v3.0.32-rc (19.05.2017)
-----------------------
- Add global installation

v3.0.31-rc (20.02.2017)
------------------------
- update directories
- fixes for redirects

v3.0.3-rc (17.02.2017)
-----------------------
- fixes for https stuff scan
- cleared internal wordlists
- increased coverage
    
v3.0.3-beta (13.02.2017)
-------------------------
- detect SSL cert requires
- added 7150 directories
- fixes for https subdomains
- more unit coverages
    
v3.0.2-beta (31.01.2017)
------------------------
- relieved of unnecessary dependencies
- fully optimized code inside
- user-friendly interface
- multiple reporters (std,txt,json,html)
- added external wordlists support
- added external proxylist support
- added wordlist shuffling
- wordlist prefixes
- added multithreading control
- dynamic and smart requests (cookies + accept headers)
- apache index of/ and files detection

v2.7.96  - v1.0.0 (05.01.2017)
------------------------------

* *v1.0.0* - all the basic functionality is available
* *v1.0.1* - added debug level as param --debug
* *v1.2.1* - added filesystem logger (param --log)
* *v1.2.2* - added example of usage (param --examples)
* *v1.3.2* - added possibility to use random proxy from proxylist (param --proxy)
* *v1.3.3* - simplify dependency installation
* *v1.3.4* - added code quality watcher
* *v1.3.5* - added ReadTimeoutError ProxyError handlers
* *v1.3.51* - fixed code style, resolve file read errors
* *v1.3.52* - code doc style added
* *v2.3.52* - subdomains scan available! (param --check subdomains). Added databases
* *v2.3.54* - disabled treads error. Refactored
* *v2.4.62* - change port is available now! (param --port 8080). Code style fixes
* *v2.5.62* - HTTPS support added
* *v2.6.62* - added 19000 Possible directories!
* *v2.7.62* - added redirect handler (Beta)
* *v2.7.72* - added 52 directories, small changes for UI
* *v2.7.82* - added 683 directories
* *v2.7.92* - exclusion list added Data/exclusions.dat
* *v2.7.95* - large files definitions , bad requests detection handler
* *v2.7.96* - optimize debug levels (0 - 1 - 2 param --debug) , optimize imports
