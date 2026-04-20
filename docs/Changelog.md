Changelog
=========

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
