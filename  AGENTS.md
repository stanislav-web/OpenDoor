# AGENTS.md

## Purpose

This file describes how contributors and coding agents should work with the OpenDoor repository.

OpenDoor is a terminal-based OWASP-oriented web directory and subdomain scanner.
The current repository state is being modernized for the 2026 Python ecosystem while preserving CLI behavior and keeping Linux distribution packaging practical.

---

## Current project goals

The current major line is **5.x.x**.

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

### Container image flow
Prefer:
- `docker build -t opendoor:local .`
- `docker run --rm opendoor:local --version`
- `docker run --rm opendoor:local --help`

Official project images are published to GitHub Container Registry:

```bash
docker pull ghcr.io/stanislav-web/opendoor:latest
```

---

## Required verification steps

Before proposing a release-oriented change, verify at least:

```bash
python -m ruff check .
python -m unittest
coverage erase
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m --precision=2
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

## Regression and impact analysis rules

Before proposing or applying a code change, contributors and coding agents must evaluate the blast radius of the change.

For every non-trivial patch, explicitly check and report:
- which existing flows, CLI flags, report formats, transports, plugins, or packaging paths may be affected;
- whether the change can alter user-visible output, scan behavior, filtering behavior, progress output, reports, or exit codes;
- which existing tests cover the affected behavior;
- which new or updated regression tests are needed to protect the change;
- what manual validation commands should be run after applying the patch.

When the change touches shared runtime paths, common helpers, output rendering, config parsing, session resume, reporting, transport/proxy logic, packaging, or CLI argument handling, assume that unrelated functionality may be affected until proven otherwise.

Do not describe a patch as safe only because targeted tests pass. If full regression coverage was not executed, state clearly what was verified and what remains unverified.

Prefer targeted regression tests that prove:
- the fixed behavior works;
- the previous working behavior remains unchanged;
- adjacent modes still behave correctly.

If a risk cannot be eliminated with deterministic tests, document it in the response and provide a concrete manual check.

---

## CLI/config/session normalization rules

CLI arguments, wizard configuration values, and session resume snapshots must follow one consistent normalization model.

When adding or changing any CLI option that can also appear in `opendoor.conf`, wizard output, or session snapshots:

- keep `argparse` defaults as `None` when the option can be restored from wizard/session state;
- place runtime defaults in `src/lib/browser/config.py`, not in `argparse`, when the default must not overwrite restored state;
- validate direct CLI input in `src/core/options/filter.py`;
- validate wizard/session values again in `BrowserConfig`, because those values may bypass CLI parsing;
- preserve explicit CLI overrides in `Controller.scan_action()` after wizard/session params are restored;
- keep direct launcher and installed entrypoint behavior aligned.

### Explicit override model

Use this precedence for runtime params:

```text
explicit CLI value > session-loaded value > wizard/config value > BrowserConfig runtime default
```

Do not let parser defaults overwrite wizard/session values.

For boolean `store_true` style flags, prefer:

```text
argparse default=None
BrowserConfig default=False
```

This allows the controller to distinguish:

```text
flag omitted         -> do not override restored wizard/session state
flag explicitly set  -> override restored wizard/session state
```

Do not add `--no-*` negation flags in a patch release unless the maintainer explicitly approves the new public CLI semantics.

### Boolean normalization

Boolean-like values from wizard/config/session must be normalized consistently.

Accepted true values:

```text
true, True, 1, yes, on
```

Accepted false values:

```text
false, False, 0, no, off
```

Invalid boolean-like values must fail early with a clear validation error.

### Numeric option normalization

Numeric options must not silently fall back when the user provided an invalid value.

Examples:

```text
--threads 0
--port 0
--delay -1
--recursive-depth 0
```

Invalid explicit values must reach validation and fail early instead of being dropped as falsy values.

If an option has a runtime clamp, keep validation and clamping separate:

```text
invalid range       -> validation error
valid high value    -> documented runtime clamp, if legacy behavior requires it
```

### CSV/list option normalization

CSV/list options must be normalized consistently:

- trim whitespace;
- remove empty tokens unless an empty value has explicit semantics;
- deduplicate while preserving order when duplicate execution would be harmful;
- validate every token;
- keep user-visible order when order affects behavior.

Unknown values must fail early instead of reaching plugin/report/runtime loading.

### Raw request interaction

When a CLI option can also be inferred from `--raw-request`, keep precedence deterministic:

```text
explicit CLI value > raw-request value > runtime default
```

Raw-request-derived values must pass the same validation helpers as direct CLI values.

### Required tests for CLI/config/session changes

For every new or changed CLI/config/session option, add or update tests for:

- normal CLI flow;
- invalid CLI values;
- wizard/config normalization;
- session-load normalization;
- explicit CLI override over wizard state;
- explicit CLI override over session state;
- `BrowserConfig` runtime default;
- `BrowserConfig` validation for values that bypass CLI parsing;
- direct launcher and installed entrypoint behavior when exit code or runtime execution can be affected.

Prefer focused tests in the existing suites:

```text
tests.test_core_options
tests.test_core_filter
tests.test_controller
tests.test_lib_browser_config
```

Add runtime/session-specific tests only when the option affects scan execution, report output, fingerprinting, WAF behavior, transport, or session snapshots.

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
- install variants
- help section
- tests/build section
- documentation links

Do not replace the repository style with an unrelated template.

---

## Test rules

- Use `unittest` as the default test runner.
- Do not suggest `pytest` commands unless explicitly requested by the maintainer.
- Use module-style unittest commands for targeted runs, for example:
  `python -m unittest tests.test_lib_browser_waf_safe_mode`
- Prefer `unittest.mock` over external `mock`.
- Avoid tests that depend on real network, DNS, SSH, or shell environment when deterministic patching is possible.
- When touching old tests, keep their intent unchanged unless the existing behavior is invalid under the new Python baseline.
- When fixing test fragility, prefer precise patches over broad rewrites.
- Keep normal correctness tests and performance measurements separate.
- Prefer extending existing test modules that already cover the affected component or behavior. Do not create new test files only to raise coverage unless there is no suitable existing module, the new behavior represents a distinct subsystem, or the maintainer explicitly approves a new test module.
- Coverage-only tests must still protect meaningful behavior, branch contracts, or regression scenarios. Do not add artificial tests that only execute lines without validating observable behavior.
- When adding coverage for a new feature after its initial test module exists, place additional edge-case coverage into that feature's existing test modules first.

---

## Coverage rule

- Keep the project at the configured `.coveragerc` threshold.
- The current release line uses `fail_under = 99`.
- Do not lower the configured threshold without explicit maintainer approval.
- Prefer small targeted tests that protect current behavior before refactoring.

---

## Code style rules

- Keep code comments and docstrings in English.
- Prefer explicit, readable code over clever shortcuts.
- Make small, reviewable changes.
- Avoid introducing unnecessary dependencies.
- Keep OS-distribution packaging in mind when changing install/build layout.

---

## Ruff rules

Ruff is a required production quality gate.

Required command:

```bash
python -m ruff check .
```

The blocking Ruff baseline is intentionally staged for the legacy codebase.

Current blocking scope:
- syntax and Pyflakes correctness checks;
- undefined names;
- unused imports;
- unused variables;
- basic pycodestyle errors and warnings;
- selected bug-prone patterns through Ruff Bugbear.

Do not globally enable broad modernization rules such as `UP`, `SIM`, `RET`, `ARG`, `PIE`, `C4`, or `RUF` without a dedicated cleanup plan and maintainer approval.

Acceptable ways to handle Ruff findings:
- fix the code when the warning is valid;
- add narrow `per-file-ignores` for intentional legacy or public API patterns;
- add an inline `# noqa: RULE` only when the code is intentionally exceptional;
- split broad cleanup into a separate refactor commit.

Do not globally disable `F401`, `F841`, or core correctness checks without maintainer approval.

---

## Strict Ruff cleanup rules

Strict Ruff rules are useful for targeted cleanup but must not be enabled globally in one step.

Use strict checks only for focused modules or newly refactored areas, for example:

```bash
python -m ruff check \
  src/lib/browser/sniffers \
  tests/test_lib_browser_sniffer_engine.py \
  tests/test_lib_browser_sniffer_runtime.py \
  tests/test_lib_browser_sniffer_architecture_baseline.py \
  --select E,F,W,B,ARG,SIM,RET,RUF,UP
```

For legacy cleanup:
1. choose one module or one rule family;
2. add or preserve tests first;
3. apply small mechanical changes;
4. run full unittest and coverage;
5. keep runtime behavior unchanged unless explicitly approved.

---

## Dead-code cleanup rules

Dead-code detection is advisory first, not an automatic deletion workflow.

Use Ruff for local unused-code issues:
- unused imports;
- unused variables;
- unused arguments when `ARG` is enabled for targeted checks.

Use Vulture or similar project-wide analysis only as advisory because OpenDoor uses dynamic loading for:
- CLI actions;
- response plugins;
- report plugins;
- scanner runtime hooks;
- tests and mocks;
- packaging and entrypoint flows.

Recommended advisory command:

```bash
vulture src tests --min-confidence 65
```

Before removing code reported as unused:
- search for dynamic usage through `getattr`, plugin registries, CLI strings and report loading;
- check package and distribution entrypoints;
- add or update tests if the behavior is still supported;
- remove code in small focused commits;
- do not mix dead-code removal with feature work.

---

## Release/versioning notes

The active major line is **5.0.0**.
Use the changelog to reflect meaningful user-visible changes.

When preparing release-related work:
- keep `VERSION`, `README.md`, and packaging metadata aligned
- verify the package can be built from source
- verify the built package can still expose the `opendoor` CLI entrypoint

---

## Performance verification rules

Performance-sensitive changes must not be merged on intuition alone. The repository now includes a standalone benchmark runner:

```bash
python benchmarks/perf_baseline.py
```

Before a performance refactor capture a baseline and save it:

```bash
python benchmarks/perf_baseline.py --save benchmarks/results/perf-baseline.json
```

Optional larger run for stronger baselines:

```bash
python benchmarks/perf_baseline.py --lines 200000 --repeat 7 --warmup 2 --save benchmarks/results/perf-baseline.large.json
```

After a performance refactor compare the new result against the saved baseline:

```bash
python benchmarks/perf_baseline.py --compare benchmarks/results/perf-baseline.json
```

Or save the post-change snapshot too:

```bash
python benchmarks/perf_baseline.py \
  --compare benchmarks/results/perf-baseline.json \
  --save benchmarks/results/perf-after-refactor.json
```

Important benchmark policy:
- `benchmarks/perf_baseline.py` is not part of the normal unittest discovery suite
- do not convert benchmark timings into brittle pass/fail unit tests
- benchmark numbers should be used for before/after comparison
- performance changes must preserve scanner correctness and existing test coverage

---

Contributors and agents should optimize for:
- stability
- reproducibility
- modern packaging
- minimal surprise for end users
- minimal friction for Linux distribution maintainers
- clear regression-risk reporting
- preserving adjacent functionality when fixing focused bugs
