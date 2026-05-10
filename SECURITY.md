# Security Policy

OpenDoor is an open-source CLI scanner for authorized web reconnaissance, directory discovery, exposure assessment, fingerprint detection, WAF detection, controlled header-bypass probing, reporting, and transport-based scanning workflows.

Security reports are welcome. Please use coordinated disclosure and do not publish vulnerability details before maintainers have had a reasonable opportunity to investigate and release a fix.

## Supported Versions

OpenDoor follows semantic versioning conventions:

- patch releases fix or improve existing behavior;
- minor releases add user-facing capabilities;
- major releases may include platform-level or compatibility-impacting changes.

Security fixes are normally provided only for the latest stable release line.

| Version                       | Supported | Notes                                                     |
|-------------------------------| --------- |-----------------------------------------------------------|
| 5.15.x                        | ✅        | Current stable release line.                              |
| < 5.15                        | ❌        | Please upgrade to the latest 5.15.x release.              |
| `main` / development branches | ❌ | Development branches are not supported release artifacts. |

When a new minor or major release line becomes current, this table should be updated accordingly.

## Reporting a Vulnerability

Please do **not** report security vulnerabilities through public GitHub issues, public pull requests, public discussions, social media, or release comments.

Preferred reporting channel:

1. Open the repository on GitHub.
2. Go to **Security**.
3. Select **Report a vulnerability** if private vulnerability reporting is enabled.

If private vulnerability reporting is not available, open a minimal public issue asking for a private security contact. Do not include exploit details, vulnerable targets, credentials, tokens, private scan reports, or sensitive logs in that public issue.

## What to Include

Include enough information to reproduce and triage the report safely:

- affected OpenDoor version;
- installation method, for example source checkout, PyPI, Docker, Homebrew, Debian/Kali package, or another package manager;
- operating system and Python version;
- affected command-line options or configuration values;
- clear vulnerability description and expected impact;
- minimal reproduction steps using a local test server, mock target, or explicitly authorized target;
- sanitized logs, stack traces, report snippets, or screenshots;
- whether the issue affects confidentiality, integrity, availability, safe defaults, transport handling, report generation, dependency security, or packaging.

Do not include:

- credentials, bearer tokens, cookies, private keys, OpenVPN/WireGuard secrets, or real proxy secrets;
- private target lists;
- private scan reports from systems you do not own;
- exploit payload collections intended for abuse;
- instructions for unauthorized scanning or bypassing third-party defenses.

## Response Expectations

Maintainers will make a best effort to:

- acknowledge valid private reports within 7 days;
- triage the report and request additional information if needed;
- confirm whether the report is accepted or declined;
- prepare a fix in a private advisory or private branch when appropriate;
- publish a patched release and release notes once the fix is available.

If a report is declined, maintainers should explain the reason when possible. Examples include unsupported versions, duplicate reports, expected behavior, issues that require unauthorized third-party testing, or findings that are outside the project scope.

## Project Scope

In scope:

- vulnerabilities in OpenDoor source code;
- unsafe default behavior that could expose user data or secrets;
- command-line parsing issues with security impact;
- report generation bugs that leak unintended local data;
- unsafe handling of transport profiles, proxy configuration, OpenVPN/WireGuard configuration, headers, cookies, or tokens;
- dependency vulnerabilities that affect OpenDoor runtime behavior;
- packaging, Docker, release, or installation issues with security impact.

Out of scope:

- vulnerabilities in third-party targets scanned with OpenDoor;
- reports based only on running OpenDoor against systems without authorization;
- social engineering;
- denial-of-service testing against public infrastructure;
- brute-force, credential stuffing, or credential theft scenarios;
- issues caused by intentionally unsafe local configuration;
- unsupported versions unless the issue also affects the current supported release line.

## Safe Research Requirements

OpenDoor must be used only against systems you own or have explicit permission to test.

Security research for this project should use local services, controlled lab environments, mock targets, or targets where the reporter has explicit authorization. Reports that require unauthorized scanning of third-party systems will not be accepted.

## Public Disclosure

Please allow maintainers time to investigate and release a fix before publishing vulnerability details publicly.

After a fix is released, maintainers may publish a GitHub Security Advisory, release notes, changelog entries, and mitigation guidance as appropriate.
