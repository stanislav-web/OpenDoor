# AGENTS.md

## Purpose

This file describes how contributors and coding agents should work with the OpenDoor repository.

OpenDoor is a terminal-based OWASP-oriented web directory and subdomain scanner.
The current repository state is being modernized for the 2026 Python ecosystem while preserving CLI behavior and keeping Linux distribution packaging practical.

---

## Current project goals

The current major line is **5.0.0**.

Primary goals of this upgrade line:
- keep the scanner runnable and releasable on modern Python
- preserve the public CLI shape unless explicitly changed
- keep source and wheel distribution generation healthy
- keep packaging friendly for Linux distributions and maintainers
- continue with refactoring and new tests in later iterations

---

## Supported Python versions

Target Python baseline:
- **3.12**
- **3.13**
- **3.14**

Do not add new code that depends on unsupported Python versions below 3.12.

---

## Preferred install and build flows

### End-user installation
Prefer:
- `pipx install opendoor`
- `python3 -m pip install opendoor`

### Development installation
Prefer:
- `python3 -m venv .venv`
- `python -m pip install -r requirements-dev.txt`
- `python -m pip install -e .`

### Distribution / package maintainer flow
Prefer:
- `python3 -m build`

Expected artifacts:
- `dist/opendoor-<version>.tar.gz`
- `dist/opendoor-<version>-py3-none-any.whl`

Do not reintroduce legacy guidance based on `python setup.py install`.

---

## Required verification steps

Before proposing a release-oriented change, verify at least:

```bash
python -m unittest
python -m pip install -e .
python -m build
opendoor --help
opendoor --version
python opendoor.py --help
python opendoor.py --version
```

If a change affects packaging, installation, metadata, manifests, or entrypoints, `python -m build` is mandatory.

If a change affects CLI arguments or runtime help, verify both:
- installed entrypoint: `opendoor`
- direct launcher: `python opendoor.py`

---

## Change policy

### Allowed in the current modernization line
- packaging modernization
- metadata cleanup
- Python version baseline refresh
- dependency refresh
- build fixes
- test stabilization
- documentation refresh
- safe internal cleanup that does not change user-visible scanner behavior

### Avoid unless explicitly requested
- broad architectural rewrites
- changing scanner logic heuristics
- removing public CLI flags
- renaming report formats or sniff plugins
- changing output semantics without tests and changelog updates

---

## Packaging rules

- Keep `pyproject.toml` present and valid.
- Keep `setup.py` working while the repository still uses it.
- Keep `MANIFEST.in` aligned with all files required to build from sdist.
- If `setup.py` reads a file at build time, make sure that file is included in source distributions.
- Keep packaging suitable for Linux distribution maintainers.
- Do not rely on local Git state or SSH access from inside the application.
- Prefer standard Python packaging behavior over custom shell update logic.

---

## Documentation rules

When modifying installation or release behavior, update:
- `README.md`
- `CHANGELOG.md` when appropriate
- `AGENTS.md` if contributor workflow changed

README style should preserve the current public project presentation:
- badges
- changelog excerpt
- install variants
- help section
- tests/build section
- documentation links

Do not replace the repository style with an unrelated template.

---

## Test rules

- Prefer `unittest.mock` over external `mock`.
- Avoid tests that depend on real network, DNS, SSH, or shell environment when deterministic patching is possible.
- When touching old tests, keep their intent unchanged unless the existing behavior is invalid under the new Python baseline.
- When fixing test fragility, prefer precise patches over broad rewrites.

---

## Code style rules

- Keep code comments and docstrings in English.
- Prefer explicit, readable code over clever shortcuts.
- Make small, reviewable changes.
- Avoid introducing unnecessary dependencies.
- Keep OS-distribution packaging in mind when changing install/build layout.

---

## Release/versioning notes

The active major line is **5.0.0**.
Use the changelog to reflect meaningful user-visible changes.

When preparing release-related work:
- keep `VERSION`, `README.md`, and packaging metadata aligned
- verify the package can be built from source
- verify the built package can still expose the `opendoor` CLI entrypoint

---

## Future work guidance

Planned next work after the modernization baseline:
- warning cleanup
- deeper internal refactoring
- broader automated test coverage
- metadata refinement
- release polish
- better distro packaging ergonomics where useful

These are valid directions, but should be delivered in controlled steps.

---

## Maintainer context

Primary maintainer:
- `@stanislav-web`

Contributors and agents should optimize for:
- stability
- reproducibility
- modern packaging
- minimal surprise for end users
- minimal friction for Linux distribution maintainers
