# 🔐 TLS compatibility

OpenDoor uses the default Python/OpenSSL TLS policy unless a compatibility flag is explicitly selected.

For most targets, keep the default behavior. It preserves the operating system and Python runtime security policy and avoids masking weak server-side TLS configuration.

---

## Default TLS mode

```shell
opendoor --host https://example.com
```

Default mode is the recommended mode for normal scans. It does not override OpenSSL cipher selection.

---

## Legacy TLS mode

Use `--tls-legacy` only when a target is reachable in a browser but Python/OpenSSL-based clients fail during TLS negotiation with a weak-DH error.

```shell
opendoor --host https://legacy.example.com --tls-legacy
```

`--tls-legacy` is an opt-in compatibility mode. It excludes DHE cipher suites by using the legacy cipher policy below for OpenDoor HTTP clients:

```text
DEFAULT:!DHE
```

This can help with servers that offer weak Diffie-Hellman parameters such as 1024-bit DHE and trigger OpenSSL errors like:

```text
SSL error: DH_KEY_TOO_SMALL
[SSL: DH_KEY_TOO_SMALL] dh key too small
```

When `--tls-legacy` is enabled, OpenDoor still uses HTTPS and keeps certificate verification behavior aligned with the normal HTTP client path. The flag only changes the TLS cipher negotiation policy used by the scanner.

---

## When to use it

Use `--tls-legacy` when all of these are true:

- the host is in scope and HTTPS is expected;
- the site opens in a browser;
- OpenDoor or another Python/OpenSSL scanner fails before receiving an HTTP status;
- debug output or another TLS check points to `DH_KEY_TOO_SMALL` or weak DHE/DH parameters.

Do not use `--tls-legacy` as a default scan profile. A weak-DH failure is a server-side TLS finding, not a normal network timeout.

---

## Diagnostic workflow

Check the OpenSSL version used by Python:

```shell
python3 -c "import ssl; print(ssl.OPENSSL_VERSION)"
```

Confirm the weak-DH failure with OpenSSL:

```shell
openssl s_client \
  -connect legacy.example.com:443 \
  -servername legacy.example.com \
  -tls1_2 \
  -cipher 'DHE' \
  </dev/null
```

If this reports `dh key too small`, test whether excluding DHE works:

```shell
openssl s_client \
  -connect legacy.example.com:443 \
  -servername legacy.example.com \
  -tls1_2 \
  -cipher 'DEFAULT:!DHE' \
  </dev/null
```

If the second command completes the handshake, scan with:

```shell
opendoor --host https://legacy.example.com --tls-legacy
```

---


## Mutual TLS / client certificate authentication

Use mTLS only for authorized internal or client-certificate protected targets. OpenDoor reads certificate and key files from local disk and sends them only as part of the target HTTPS TLS handshake. It does not generate certificates, intercept TLS, impersonate browser TLS fingerprints, or store certificate/private-key contents in reports, logs, or sessions.

Combined PEM:

```shell
opendoor \
  --host https://internal.example.com \
  --client-cert ./client.pem
```

Separate certificate and key:

```shell
opendoor \
  --host https://internal.example.com \
  --client-cert ./client.crt \
  --client-key ./client.key
```

Encrypted key password through an environment variable reference:

```shell
OPENDOOR_CLIENT_KEY_PASSWORD='...' opendoor \
  --host https://internal.example.com \
  --client-cert ./client.crt \
  --client-key ./client.key \
  --client-key-password-env OPENDOOR_CLIENT_KEY_PASSWORD
```

`--client-key-password-env` stores and resumes only the environment variable name. The resolved password value is never written to session checkpoints, reports, or debug output. Missing files, directories instead of files, unreadable files, `--client-key` without `--client-cert`, and missing password environment variables fail during option/config validation.

mTLS composes with direct HTTPS, HTTP CONNECT proxy HTTPS, SOCKS HTTPS, and `--tls-legacy` when both are explicitly required by the target environment.

## Sessions

`--tls-legacy` and mTLS file paths/environment-variable names are stored in session checkpoints. A resumed scan keeps the same TLS compatibility mode and client certificate configuration that were active when the session was saved. Secret values and certificate/private-key contents are not stored.

```shell
opendoor \
  --host https://legacy.example.com \
  --tls-legacy \
  --session-save legacy.session

opendoor --session-load legacy.session
```

You can also enable legacy TLS compatibility when resuming an older session that was created without the flag:

```shell
opendoor --session-load legacy.session --tls-legacy
```

---

## Server-side fix

The preferred fix is to update the target server TLS configuration instead of relying on client compatibility mode. Typical server-side remediation includes:

- disable SSLv3, TLSv1.0 and TLSv1.1;
- disable RC4, 3DES, MD5 and weak CBC suites;
- disable weak DHE suites or replace DH parameters with at least 2048-bit parameters;
- prefer ECDHE suites for modern TLS negotiation.

After server remediation, run OpenDoor without `--tls-legacy`.
