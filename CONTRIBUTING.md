# Contributing to OpenDoor

Thank you for considering a contribution to OpenDoor.

OpenDoor is an open-source CLI scanner for authorized web reconnaissance, directory discovery, subdomain enumeration, fingerprint detection, WAF detection, controlled header-bypass probing, response filtering, reporting, and transport-based scanning workflows.

This file is the GitHub-facing contribution guide. The extended documentation lives in:

- [Contribution guide](docs/Contribution.md)
- [Testing guide](docs/Testing.md)
- [Project documentation](docs/)

---

## Contribution principles

Good contributions are:

- focused;
- tested;
- easy to review;
- compatible with the current CLI behavior;
- documented when they change user-facing behavior;
- safe for public open-source distribution.

Prefer small, isolated pull requests over large mixed changes.

---

## Responsible security work

OpenDoor is a security testing tool. Contributions must support authorized testing only.

Do not contribute:

- exploit payload collections intended for abuse;
- credential theft logic;
- stealth or persistence features;
- destructive scanning behavior;
- malware-like behavior;
- real private VPN profiles, API tokens, cookies, bearer tokens, or credentials.

Do not commit real OpenVPN or WireGuard secrets.

Use placeholder examples only:

```text
data/openvpn-profiles/example.ovpn
data/wireguard-profiles/example.conf
```

These files must contain placeholders, not real production credentials.

---

## Development setup

Clone the repository:

```shell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor
```

Create a virtual environment:

```shell
python3 -m venv .venv
source .venv/bin/activate
```

Install development dependencies:

```shell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

Verify the CLI:

```shell
opendoor --version
opendoor --help
python opendoor.py --version
python opendoor.py --help
```

---

## Supported Python versions

The active OpenDoor 5.x line targets:

- Python 3.12
- Python 3.13
- Python 3.14
- Python 3.15

Do not add code that depends on unsupported Python versions below 3.12.

---

## Branch workflow

Create a focused branch:

```shell
git checkout -b feature/my-change
```

Recommended branch prefixes:

| Prefix | Purpose |
|---|---|
| `feature/` | New user-facing functionality |
| `fix/` | Bug fixes |
| `docs/` | Documentation-only changes |
| `test/` | Test-only changes |
| `refactor/` | Internal cleanup without behavior change |
| `release/` | Release preparation |

Keep commits focused. If a change touches code, tests, and docs, that is fine when all changes support the same feature or fix.
All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Required checks

Run the relevant checks before opening a pull request.

### Full test suite

```shell
python -m unittest
```

Equivalent explicit discovery:

```shell
python -m unittest discover -s tests -p "test_*.py"
```

### Coverage

OpenDoor uses `coverage.py` with `.coveragerc`.

```shell
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m
```

The current configured coverage threshold is `fail_under = 99`. Do not lower it without maintainer approval.

### Lint

```shell
ruff check .
```

The current Ruff policy is intentionally conservative for the legacy codebase. Prefer targeted fixes over broad automatic rewrites.

### Documentation

```shell
python -m mkdocs build --strict
```

If `mkdocs` is not available, use a documentation virtual environment:

```shell
python3 -m venv .docs-venv
source .docs-venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r docs/requirements.txt
python -m mkdocs build --strict
```

Do not commit local documentation build artifacts such as `.docs-venv/` or `site/`.

---

## Test expectations

Every behavior change should include tests unless there is a clear reason not to.

Tests should be:

- deterministic;
- isolated;
- readable;
- free from real network dependencies;
- free from real VPN/process side effects;
- explicit about expected behavior.

Use `unittest` as the default test runner. Do not introduce `pytest` commands or test dependencies unless the maintainer explicitly requests it.

Avoid increasing per-test timeouts to hide instability. Fix the underlying nondeterminism instead.

When a test fails, verify whether the failure comes from the test or from the implementation before changing assertions.

---

## Areas that usually need tests

| Change area | Expected test coverage |
|---|---|
| CLI option parsing | Unit tests for options and config propagation |
| Response filters | Unit tests for include/exclude behavior |
| Sniffers | Unit tests for plugin classification |
| Auto-calibration | Unit tests for baseline and matching behavior |
| Fingerprinting | Unit tests for known positive/negative samples |
| WAF detection | Unit tests for passive detection signals |
| Header-bypass probing | Unit tests for opt-in behavior and eligible statuses |
| Sessions | Unit tests for save/load/resume compatibility |
| Reports | Unit tests for output writers and file creation |
| Transports | Unit tests with mocked OpenVPN/WireGuard/process calls |
| Packaging | Installation smoke checks and runtime asset checks |
| Documentation | `python -m mkdocs build --strict` |

---

## Documentation changes

Update documentation when a change affects:

- CLI flags;
- config file options;
- reports;
- scan behavior;
- result buckets;
- installation;
- release process;
- Homebrew, PyPI, Docker, or Linux packaging;
- transport setup;
- WAF, fingerprinting, header-bypass, or auto-calibration behavior.

Documentation lives in:

```text
docs/
```

Build locally:

```shell
python -m mkdocs build --strict
```

Serve locally:

```shell
python -m mkdocs serve
```

Open:

```text
http://127.0.0.1:8000/
```

---

## Packaging changes

If you change packaging metadata, runtime data files, entry points, dependencies, manifests, or install layout, run packaging checks.

Build:

```shell
python -m build
```

Install into a clean virtual environment:

```shell
python3 -m venv /tmp/opendoor-package-check
source /tmp/opendoor-package-check/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install /path/to/OpenDoor/dist/opendoor-*.whl

opendoor --version
opendoor --help
```

Verify required runtime assets after installation:

```shell
python - <<'PY'
from pathlib import Path
import sys

root = Path(sys.prefix)

paths = [
    "opendoor.conf",
    "data/directories.dat",
    "data/subdomains.dat",
    "data/useragents.dat",
    "data/proxies.dat",
    "data/ignored.dat",
    "data/openvpn-profiles/example.ovpn",
    "data/wireguard-profiles/example.conf",
]

for rel in paths:
    print(rel, (root / rel).exists())
PY
```

All required runtime assets should exist.

---

## Homebrew formula changes

When validating a Homebrew formula locally:

```shell
HOMEBREW_NO_INSTALL_FROM_API=1 brew install --build-from-source --verbose opendoor
HOMEBREW_NO_INSTALL_FROM_API=1 brew test opendoor
HOMEBREW_NO_INSTALL_FROM_API=1 brew audit --strict --new --online opendoor
```

A Homebrew test must not depend on external network access.

---

## Secret hygiene

Before committing, check for accidental secrets.

Useful check:

```shell
git grep -n -I -E '(BEGIN .*PRIVATE KEY|PrivateKey = [A-Za-z0-9+/=]{20,}|PresharedKey = [A-Za-z0-9+/=]{20,}|<key>|</key>)'
```

Do not commit:

- real VPN profiles;
- private keys;
- auth-user-pass files;
- cookies;
- API tokens;
- bearer tokens;
- customer target lists;
- generated reports with sensitive findings;
- sensitive CI artifacts.

---

## Pull request checklist

Before opening a pull request:

- [ ] The change is focused and reviewable.
- [ ] User-facing behavior is documented.
- [ ] Tests were added or updated where needed.
- [ ] `python -m unittest` passes.
- [ ] `coverage report -m` passes with the configured threshold.
- [ ] `ruff check .` passes.
- [ ] `python -m mkdocs build --strict` passes for documentation changes.
- [ ] `python -m build` passes for packaging/install changes.
- [ ] Runtime assets are still included when package layout changes.
- [ ] No secrets or real transport profiles were committed.

---

## Commit message style

Use concise, descriptive commit messages.

Examples:

```text
Add WAF summary to reports
Fix response size range filtering
Refresh ReadTheDocs usage guide
Include transport profile examples in package data
```

Avoid vague messages such as:

```text
fix
updates
misc changes
work
```

---

## Review guidance

When reviewing a contribution, check:

- whether the change matches the intended behavior;
- whether tests prove the new behavior;
- whether docs and examples are accurate;
- whether runtime defaults remain safe;
- whether package data is still included;
- whether the change introduces secret or credential risks;
- whether CI/CD behavior and exit codes remain predictable.

Prefer minimal, targeted fixes over broad rewrites.
