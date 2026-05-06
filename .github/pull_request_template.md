## Summary

<!-- Describe what this PR changes and why. Keep it focused. -->

## Related issue

<!-- Link the issue if this PR closes or addresses one. Example: Closes #123 -->

## Type of change

<!-- Select all that apply. -->

- [ ] Bug fix
- [ ] Patch / improvement of existing behavior
- [ ] New feature
- [ ] Documentation update
- [ ] Test-only change
- [ ] Refactor without user-facing behavior change
- [ ] Packaging / release / CI change
- [ ] Security hardening

## SemVer impact

<!-- Select the expected release impact. -->

- [ ] Patch: fixes or improves existing behavior without adding a new capability
- [ ] Minor: adds a new user-facing capability while remaining backward compatible
- [ ] Major: changes platform support, removes behavior, or introduces breaking changes
- [ ] No release impact: docs/tests/maintenance only

## User-facing behavior

<!-- Describe CLI flags, output, reports, docs, defaults, or scanner behavior affected by this PR. Write "None" if not applicable. -->

## Verification

<!-- Mark every check that was run. Leave unchecked if not applicable or not run. -->

- [ ] `python -m unittest`
- [ ] `coverage run -m unittest discover -s tests -p "test_*.py"`
- [ ] `coverage report -m`
- [ ] `ruff check .`
- [ ] `python -m mkdocs build --strict`
- [ ] `python -m build`
- [ ] `opendoor --version`
- [ ] `opendoor --help`
- [ ] `python opendoor.py --version`
- [ ] `python opendoor.py --help`

## Tests added or updated

<!-- Describe tests added/updated. If no tests were added, explain why. -->

## Documentation

<!-- Select all that apply. -->

- [ ] README updated
- [ ] docs/ updated
- [ ] CHANGELOG updated
- [ ] No documentation change required

## Security and responsible use

- [ ] This PR does not commit real tokens, cookies, VPN profiles, credentials, private targets, or scan reports
- [ ] Security-sensitive details are not exposed in public logs, docs, examples, tests, or screenshots

## Backward compatibility

<!-- Describe compatibility impact for CLI options, config files, reports, sessions, fingerprints, WAF detection, transports, packaging, and scripts. Write "Compatible" if there is no impact. -->

## Reviewer notes

<!-- Anything the reviewer should focus on: risky files, behavior tradeoffs, migration notes, known limitations, follow-up tasks. -->
