# 🌐 Network transports

OpenDoor supports direct, proxy, OpenVPN, and WireGuard transport modes.

Transport options are useful when you need controlled network routing for authorized scanning workflows. HTTPS targets also use the default Python/OpenSSL TLS policy unless `--tls-legacy` is explicitly enabled for weak-DH compatibility.

---


## Platform model

OpenDoor is cross-platform, but VPN transports depend on OS-level VPN tooling. OpenDoor does not ship drivers, kernel extensions, TUN/TAP devices, Windows services, or a VPN agent. It starts an existing backend when `--transport openvpn` or `--transport wireguard` is selected.

If a platform uses a GUI client or corporate VPN agent instead of a CLI backend, start that client first and keep OpenDoor in `direct` mode. The scanner will use the active system route.

Use `--transport-bin` to point OpenDoor at a backend executable when it is not in `PATH`.

---

## Supported modes

| Mode | Purpose |
|---|---|
| `direct` | Use the default system network path |
| `proxy` | Route requests through a configured proxy |
| `openvpn` | Bring up an OpenVPN profile for the scan |
| `wireguard` | Bring up a WireGuard profile for the scan |

---

## Direct mode

```shell
opendoor --host https://example.com --transport direct
```

This is the default network path.

---


## TLS compatibility

For most HTTPS targets, no TLS option is needed.

When a legacy server fails TLS negotiation with `DH_KEY_TOO_SMALL`, use the explicit compatibility flag:

```shell
opendoor --host https://legacy.example.com --tls-legacy
```

See [TLS compatibility](tls.md) for diagnostic commands and session behavior.

---

## Proxy mode

```shell
opendoor \
  --host https://example.com \
  --transport proxy \
  --proxy socks5://127.0.0.1:9050
```

---

## OpenVPN mode

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn
```

---

## WireGuard mode

```shell
opendoor \
  --host https://example.com \
  --transport wireguard \
  --transport-profile ./profile.conf
```

---

## Profile rotation

For batch scans, OpenDoor can rotate transport profiles per target:

```shell
opendoor \
  --hostlist targets.txt \
  --transport openvpn \
  --transport-profiles vpn-profiles.txt \
  --transport-rotate per-target
```

---

## Healthcheck

Use a healthcheck URL to validate transport connectivity:

```shell
opendoor \
  --host https://example.com \
  --transport openvpn \
  --transport-profile ./profile.ovpn \
  --transport-healthcheck-url https://ifconfig.me
```

---

## Secret hygiene

Never commit real transport profiles or credentials.

Do not commit:

- WireGuard private keys;
- OpenVPN private keys;
- `auth-user-pass` files;
- production proxy credentials;
- customer-specific routing data.

Use placeholder examples only.
