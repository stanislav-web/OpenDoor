# 🔐 OpenVPN transport

OpenVPN transport brings up an OpenVPN profile for the duration of a scan.

Use it only for authorized workflows and local profiles you control.

---


## System backend requirement

OpenDoor does not bundle or install a VPN client. The OpenVPN transport starts the system OpenVPN CLI for the duration of the scan.

Cross-platform behavior:

| OS | Requirement | Notes |
|---|---|---|
| macOS | OpenVPN CLI installed and reachable from `PATH`, or passed with `--transport-bin` | Common Homebrew paths are checked automatically: `/opt/homebrew/sbin/openvpn`, `/usr/local/sbin/openvpn` |
| Linux | `openvpn` package installed, or binary passed with `--transport-bin` | The process usually needs privileges to create TUN/TAP routes |
| Windows | OpenVPN Community client with `openvpn.exe`, or binary passed with `--transport-bin` | Run the terminal as Administrator when the profile needs route/TAP changes |

If you use OpenVPN Connect, OpenVPN GUI, Tunnelblick, a corporate VPN agent, or another OS-level VPN app, start the VPN outside OpenDoor and run OpenDoor with the default `direct` transport. In that mode OpenDoor uses the already active system route.

---

## Explicit executable path

Use `--transport-bin` when the executable is installed but not visible in `PATH`:

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn \
  --transport-bin /opt/homebrew/sbin/openvpn
```

Windows example:

```powershell
opendoor `
  --host https://example.com `
  --transport openvpn `
  --transport-profile .\profile.ovpn `
  --transport-bin "C:\Program Files\OpenVPN\bin\openvpn.exe"
```

---

## Basic usage

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn
```

---

## Username/password auth

For OpenVPN profiles that require `auth-user-pass`, provide an auth file:

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn \
  --openvpn-auth ./auth.txt
```

Example `auth.txt` format:

```text
username
password
```

Do not commit `auth.txt`.

---

## Transport timeout

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn \
  --transport-timeout 60
```

---

## Healthcheck

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn \
  --transport-healthcheck-url https://ifconfig.me
```

---

## Multiple OpenVPN profiles

Create `vpn-profiles.txt`:

```text
./vpn/profile-1.ovpn
./vpn/profile-2.ovpn
./vpn/profile-3.ovpn
```

Run:

```shell
opendoor \
  --hostlist targets.txt \
  --transport openvpn \
  --transport-profiles vpn-profiles.txt \
  --transport-rotate per-target
```

---

## Example profile

Use placeholder examples only.

```text
data/openvpn-profiles/example.ovpn
```

Never commit real OpenVPN profiles, private keys, or auth files.
