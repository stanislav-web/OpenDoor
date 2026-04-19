Testing
=======

OpenDoor uses a lightweight `unittest`-based test suite.

The current modernization baseline keeps tests focused on:
- CLI behavior
- options parsing
- browser and threadpool behavior
- package/version helpers
- reporting
- readers
- events
- terminal helpers

Run tests
=========

#### Run the full test suite
```shell
python3 -m unittest
```

#### Run tests in a development virtual environment
```shell
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
python -m unittest
```

#### Run a single test module
```shell
python3 -m unittest tests.test_lib_package
python3 -m unittest tests.test_core_options
```

#### Run a single test class
```shell
python3 -m unittest tests.test_lib_package.TestPackage
```

#### Run a single test method
```shell
python3 -m unittest tests.test_lib_package.TestPackage.test_version
```

Build and packaging verification
================================

If you change packaging, metadata, manifests, entrypoints, or installation logic, the test suite alone is not enough.

Always verify:

```shell
python -m build
opendoor --help
opendoor --version
python opendoor.py --help
python opendoor.py --version
```

Recommended release-oriented verification
=========================================

Before a release, verify at least:

```shell
python -m unittest
python -m build
pipx uninstall opendoor
pipx install dist/opendoor-<version>-py3-none-any.whl
opendoor --help
opendoor --version
```

Recommended clean-environment verification:

```shell
python3 -m venv /tmp/opendoor-pypi-test
source /tmp/opendoor-pypi-test/bin/activate
python -m pip install --upgrade pip
python -m pip install opendoor
opendoor --help
opendoor --version
```

Lint
====

OpenDoor now uses a lightweight Ruff baseline.

```shell
ruff check .
```

Current lint policy is intentionally conservative for the legacy codebase:
- basic error checks
- basic runtime correctness checks
- no aggressive mass auto-fix workflow by default

Test guidance
=============

When changing old tests:
- prefer small fixes over broad rewrites
- prefer `unittest.mock`
- avoid real network and shell dependencies when deterministic patching is possible
- keep historical CLI behavior intact unless intentionally changed

Notes
=====

The current 5.x line is focused on:
- modern packaging
- stable installs
- documentation refresh
- maintainable release flow

Broader refactoring and deeper cleanup can continue in later iterations.
