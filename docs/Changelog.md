Changelog
=========

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
