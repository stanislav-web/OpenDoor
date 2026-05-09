# 🌐 VPN transport scans

OpenDoor supports proxy, OpenVPN, and WireGuard transport modes.

Use transport profiles only for authorized workflows.

---


## Cross-platform backend resolution

OpenDoor first searches `PATH`, then known OS-specific locations. Use `--transport-bin` when the VPN backend is installed elsewhere.

macOS OpenVPN example:

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./vpn/profile.ovpn \
  --transport-bin /opt/homebrew/sbin/openvpn
```

Windows OpenVPN example:

```powershell
opendoor `
  --host https://example.com `
  --transport openvpn `
  --transport-profile .\vpn\profile.ovpn `
  --transport-bin "C:\Program Files\OpenVPN\bin\openvpn.exe"
```

When VPN is already connected by OpenVPN Connect, Tunnelblick, WireGuard Desktop, or a corporate VPN agent, do not use `--transport openvpn` or `--transport wireguard`; run OpenDoor in direct mode so it uses the existing OS route.

---

## Proxy transport

```shell
opendoor \
  --host https://example.com \
  --transport proxy \
  --proxy socks5://127.0.0.1:9050
```

---

## OpenVPN transport

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./vpn/profile.ovpn
```

With `auth-user-pass`:

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./vpn/profile.ovpn \
  --openvpn-auth ./vpn/auth.txt
```

---

## WireGuard transport

```shell
opendoor \
  --host https://example.com \
  --transport wireguard \
  --transport-profile ./vpn/profile.conf
```

---

## Healthcheck

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./vpn/profile.ovpn \
  --transport-healthcheck-url https://ifconfig.me
```

---

## Per-target rotation

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

## Secret hygiene

Never commit:

- real OpenVPN profiles;
- WireGuard private keys;
- VPN auth files;
- production proxy credentials;
- customer-specific transport routes.

Use placeholder examples only.
