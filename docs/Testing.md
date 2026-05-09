# 🧪 Testing

OpenDoor uses a lightweight `unittest`-based test suite.

The test suite focuses on deterministic checks for CLI behavior, option parsing, response classification, browser/runtime behavior, reporting, package metadata, sessions, fingerprinting, WAF detection, auto-calibration, and network transport helpers.

---

## 🛠️ Prepare a development environment

Create a virtual environment:

```shell
python3 -m venv .venv
source .venv/bin/activate
```

Install development dependencies:

```shell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
```

Verify the CLI in editable mode if needed:

```shell
python -m pip install -e .
opendoor --version
opendoor --help
```

---

## ✅ Run the full test suite

From the repository root:

```shell
python -m unittest
```

Equivalent explicit discovery command:

```shell
python -m unittest discover -s tests -p "test_*.py"
```

---

## 🎯 Run selected tests

Run a single test module:

```shell
python -m unittest tests.test_core_options
python -m unittest tests.test_lib_package
python -m unittest tests.test_core_network_transport
```

Run a single test class:

```shell
python -m unittest tests.test_lib_package.TestPackage
```

Run a single test method:

```shell
python -m unittest tests.test_lib_package.TestPackage.test_version
```

---

## 📈 Coverage

OpenDoor uses `coverage.py` with `.coveragerc`.

Run coverage:

```shell
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m
```

Generate an HTML report:

```shell
coverage html
```

Open:

```text
htmlcov/index.html
```

The configured coverage threshold is enforced by `.coveragerc`.

---

## 🧹 Lint

OpenDoor uses Ruff as a lightweight lint baseline.

```shell
ruff check .
```

The current lint policy is intentionally conservative for the legacy codebase:

- basic syntax and runtime correctness checks;
- no aggressive mass auto-fix workflow by default;
- small targeted changes are preferred over broad rewrites.

---

## 📚 Documentation build

Documentation is built with MkDocs.

Create a separate documentation virtual environment:

```shell
python3 -m venv .docs-venv
source .docs-venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r docs/requirements.txt
```

Build documentation strictly:

```shell
python -m mkdocs build --strict
```

Serve documentation locally:

```shell
python -m mkdocs serve
```

Open:

```text
http://127.0.0.1:8000/
```

Do not commit local documentation build artifacts such as `.docs-venv/` or `site/`.

---

## 📦 Packaging checks

If you change packaging, metadata, manifests, setup logic, entry points, runtime data files, or release configuration, the unit test suite is not enough.

Run:

```shell
python -m build
```

Verify generated artifacts:

```shell
ls -lh dist/
```

Install the generated wheel in a clean environment:

```shell
python3 -m venv /tmp/opendoor-package-check
source /tmp/opendoor-package-check/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install dist/opendoor-*.whl

opendoor --version
opendoor --help
```

If you are testing from outside the source checkout, use an absolute wheel path:

```shell
python -m pip install /path/to/OpenDoor/dist/opendoor-*.whl
```

---

## 🧾 Runtime asset verification

Packaged installations must include runtime files such as:

```text
opendoor.conf
data/directories.dat
data/subdomains.dat
data/useragents.dat
data/proxies.dat
data/ignored.dat
data/openvpn-profiles/example.ovpn
data/wireguard-profiles/example.conf
```

A simple installed-layout check:

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
    path = root / rel
    print(f"{rel}: exists={path.exists()}")
PY
```

All entries should print:

```text
exists=True
```

---

## 🍺 Homebrew formula checks

When validating the Homebrew formula locally:

```shell
HOMEBREW_NO_INSTALL_FROM_API=1 brew install --build-from-source --verbose opendoor
HOMEBREW_NO_INSTALL_FROM_API=1 brew test opendoor
HOMEBREW_NO_INSTALL_FROM_API=1 brew audit --strict --new --online opendoor
```

A good Homebrew test should not require network access from the formula test block.

---

## 🧪 Release smoke checklist

Before publishing a release manually, run at least:

```shell
python -m unittest
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m
ruff check .
python -m mkdocs build --strict
python -m build
```

Then verify a clean package installation:

```shell
python3 -m venv /tmp/opendoor-release-check
source /tmp/opendoor-release-check/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install /path/to/OpenDoor/dist/opendoor-*.whl

opendoor --version
opendoor --help
```

---

## 🧯 Test guidance

When changing tests:

- prefer deterministic unit tests;
- avoid real network access;
- avoid shelling out unless the behavior is specifically about CLI/package execution;
- mock external processes such as OpenVPN, WireGuard, proxies, and browser/network calls;
- keep tests small and focused;
- do not increase per-test timeouts to hide unstable tests;
- prefer fixing the source of slowness or nondeterminism;
- preserve historical CLI behavior unless the change is intentional.

When a test fails, verify whether the problem is in the test or in the implementation before changing assertions.

---

## 🧭 Useful test areas

| Area | Typical modules |
|---|---|
| CLI options | `tests.test_core_options` |
| Package/version helpers | `tests.test_lib_package` |
| Reports | `tests.test_lib_reporter*` |
| Response classification | `tests.test_core_http_response*` |
| Sniffers | `tests.test_core_http_plugins_response_*` |
| Fingerprinting | `tests.test_lib_browser_fingerprint*` |
| WAF detection | `tests.test_core_http_waf_recognition` |
| Sessions | `tests.test_lib_browser_session*` |
| Network transports | `tests.test_core_network_transport` |
| Filesystem helpers | `tests.test_core_filesystem*` |

Use `python -m unittest <module>` for focused checks while developing.
