# 🧾 Changelog

OpenDoor release history is maintained in the repository changelog, GitHub Releases, and Git tags.

This documentation page does not duplicate the full changelog to avoid stale release notes across multiple files.

---

## 📌 Primary changelog

The canonical changelog is stored in the repository root:

```text
CHANGELOG.md
```

Repository link:

```text
https://github.com/stanislav-web/OpenDoor/blob/master/CHANGELOG.md
```

Use it to review:

- release notes;
- feature additions;
- bug fixes;
- packaging changes;
- documentation changes;
- breaking or behavior-changing updates.

---

## 🏷️ Git tags

Release tags are available on GitHub:

```text
https://github.com/stanislav-web/OpenDoor/tags
```

Tags are useful when you need to:

- download a specific release source archive;
- compare versions;
- build package manager formulae;
- verify release provenance.

---

## 🚀 GitHub Releases

GitHub Releases are available here:

```text
https://github.com/stanislav-web/OpenDoor/releases
```

Use releases for:

- human-readable release summaries;
- packaged source archives;
- release-specific notes;
- distribution references.

---

## 📦 Package manager updates

Depending on your installation method, update OpenDoor with the same package manager that installed it. The `opendoor --update` command is a safe helper that prints update instructions; it does not execute package-manager commands or self-update the scanner.

| Installed with | Update command |
|---|---|
| Homebrew | `brew update && brew upgrade opendoor` |
| pipx | `pipx upgrade opendoor` |
| pip | `python -m pip install --upgrade opendoor` from the same Python environment |
| Docker / GHCR | `docker pull ghcr.io/stanislav-web/opendoor:latest` |
| Arch / BlackArch | `sudo pacman -Syu opendoor` |
| Debian / Kali | `sudo apt update && sudo apt install --only-upgrade opendoor` |
| Source checkout | `git pull --ff-only` |

For details, see [Installation and update](Installation-and-update.md).

---

## 🧪 Before upgrading in automation

If you use OpenDoor in CI/CD, review the changelog before upgrading.

Pay attention to changes related to:

- exit codes;
- `--fail-on-bucket`;
- report formats;
- result buckets;
- response filtering;
- auto-calibration;
- WAF detection;
- sessions;
- transport behavior;
- package layout.

---

## 🧭 Release policy

OpenDoor follows semantic versioning conventions:

| Version part | Meaning |
|---|---|
| Patch | Fixes or improvements to existing behavior |
| Minor | New user-facing capabilities |
| Major | Platform-level or compatibility-impacting changes |

Examples:

```text
1.1.x  Patch updates within the 1.1 line
1.x.0  New feature release
x.0.0   Major platform or compatibility release
```

---

## 🧯 Documentation note

If you find outdated documentation after a release, open an issue or pull request.

Documentation should describe the current supported behavior without duplicating every release note from `CHANGELOG.md`.
