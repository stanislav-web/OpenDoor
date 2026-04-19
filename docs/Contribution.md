Contribution
============

Thank you for your interest in OpenDoor.

The project is currently maintained with a focus on:
- stability
- reproducible builds
- modern Python packaging
- minimal surprise for end users
- practical packaging for Linux distributions

Getting started
===============

#### Clone the repository
```shell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor/
```

#### Create a development environment
```shell
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

#### Run the baseline checks
```shell
python -m unittest
python -m build
ruff check .
```

Contribution workflow
=====================

Recommended workflow:
1. create a small focused change
2. keep public CLI behavior stable unless intentionally changing it
3. run tests
4. run packaging checks if install/build logic changed
5. update documentation if behavior changed
6. open a pull request

Current change policy
=====================

Currently welcomed contributions:
- packaging modernization
- metadata cleanup
- Python version baseline refresh
- dependency refresh
- build fixes
- documentation improvements
- test stabilization
- safe internal cleanup that does not change scanner behavior

Avoid unless explicitly planned:
- large architectural rewrites
- changing scanner heuristics without tests
- removing public CLI flags
- renaming report formats or sniff plugins
- changing output semantics without changelog updates

Documentation rules
===================

When installation, release, docs, or workflow changes:
- update `README.md`
- update `CHANGELOG.md` when appropriate
- update documentation pages in `docs/`
- update `AGENTS.md` if contributor workflow changes

Code style
==========

- Keep comments and docstrings in English
- Prefer explicit readable code
- Make small reviewable changes
- Avoid unnecessary dependencies
- Keep Linux distribution packaging in mind

Reporting issues
================

Please use the GitHub issue tracker for:
- bugs
- packaging issues
- install/build failures
- regressions
- documentation problems
- feature ideas

Project links
=============

- Repository: https://github.com/stanislav-web/OpenDoor
- Issues: https://github.com/stanislav-web/OpenDoor/issues
- Documentation: https://opendoor.readthedocs.io/
- PyPI: https://pypi.org/project/opendoor/

Maintainer
==========

Primary maintainer:
- `@stanislav-web`

Final note
==========

Please keep changes controlled and incremental.  
The 5.x line is intended to preserve working behavior while modernizing the project around it.
