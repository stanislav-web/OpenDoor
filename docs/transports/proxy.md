# 🌐 Proxy transport

Proxy transport routes OpenDoor traffic through a configured proxy.

---

## Permanent proxy

```shell
opendoor --host https://example.com --proxy socks5://127.0.0.1:9050
```

Use `socks5h://` when hostname resolution must happen through the SOCKS proxy:

```shell
opendoor --host https://example.com --proxy socks5h://127.0.0.1:9050
```

`socks5://` keeps the existing SOCKS5 behavior. `socks5h://` is useful for Tor and proxy environments where DNS resolution must not happen locally.

Explicit proxy transport:

```shell
opendoor \
  --host https://example.com \
  --transport proxy \
  --proxy socks5://127.0.0.1:9050
```

---

## Built-in proxy list mode

```shell
opendoor --host https://example.com --proxy-pool
```

---

## Custom proxy list

```shell
opendoor --host https://example.com --proxy-list proxies.txt
```

Example `proxies.txt`:

```text
socks5://127.0.0.1:9050
socks5h://127.0.0.1:9050
http://127.0.0.1:8080
```

---

## Proxy with reports

```shell
opendoor \
  --host https://example.com \
  --transport proxy \
  --proxy socks5://127.0.0.1:9050 \
  --reports json,html
```

---

## Notes

Use proxy transport only where you have permission and where routing behavior is expected.

Proxy credentials and private infrastructure details should not be committed to a public repository.
