# -*- coding: utf-8 -*-

"""
    TLS helpers for OpenDoor request providers.

    Legacy compatibility and client certificate authentication are opt-in only.
    The default scanner transport keeps the platform/Python OpenSSL policy
    unchanged unless a custom target TLS option is supplied.
"""

import os
import re
import ssl
from dataclasses import dataclass


TLS_LEGACY_CIPHERS = 'DEFAULT:!DHE'
TLS_LEGACY_HINT = 'Retry with --tls-legacy or fix server TLS configuration.'


@dataclass(frozen=True)
class TLSClientAuthConfig:
    """Privacy-safe client certificate configuration for target TLS."""

    client_cert: str | None = None
    client_key: str | None = None
    client_key_password_env: str | None = None

    @property
    def is_enabled(self):
        """Return whether client certificate authentication is configured.

        :return: True when a client certificate path is present.
        :rtype: bool
        """

        return bool(self.client_cert)


def build_legacy_ssl_context():
    """
    Build an HTTPS client context for legacy servers with weak DHE parameters.

    The context keeps certificate verification disabled to preserve the existing
    OpenDoor HTTPS behavior, but excludes DHE cipher suites so OpenSSL does not
    negotiate weak DH key exchange with legacy hosts.

    :return: configured SSL context
    :rtype: ssl.SSLContext
    """

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.set_ciphers(TLS_LEGACY_CIPHERS)
    return context


def build_target_ssl_context(
        *,
        tls_legacy=False,
        client_cert=None,
        client_key=None,
        client_key_password_env=None,
):
    """
    Build the target HTTPS SSL context for OpenDoor request providers.

    The default HTTPS path intentionally returns None so urllib3 keeps the
    existing OpenDoor transport behavior. A custom context is created only for
    opt-in TLS compatibility or client certificate authentication.

    :param bool tls_legacy: Whether opt-in legacy TLS compatibility is enabled.
    :param str | None client_cert: Client certificate path or combined PEM path.
    :param str | None client_key: Separate private key path.
    :param str | None client_key_password_env: Environment variable containing
        the encrypted private key password.
    :raise ValueError: when the password environment variable is missing.
    :return: SSL context or None.
    :rtype: ssl.SSLContext | None
    """

    client_auth = TLSClientAuthConfig(
        client_cert=client_cert,
        client_key=client_key,
        client_key_password_env=client_key_password_env,
    )

    if tls_legacy is not True and client_auth.is_enabled is not True:
        return None

    if tls_legacy is True:
        context = build_legacy_ssl_context()
    else:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    if client_auth.is_enabled is True:
        context.load_cert_chain(
            certfile=client_auth.client_cert,
            keyfile=client_auth.client_key,
            password=_resolve_client_key_password(client_auth.client_key_password_env),
        )

    return context


def maybe_build_ssl_context(
        is_tls_legacy,
        client_cert=None,
        client_key=None,
        client_key_password_env=None,
):
    """
    Return an SSL context only when custom target TLS is configured.

    This compatibility wrapper preserves the existing internal helper name while
    request providers migrate to build_target_ssl_context().

    :param bool is_tls_legacy: Whether the opt-in legacy TLS mode is enabled.
    :param str | None client_cert: Client certificate path or combined PEM path.
    :param str | None client_key: Separate private key path.
    :param str | None client_key_password_env: Environment variable containing
        the encrypted private key password.
    :return: SSL context or None.
    :rtype: ssl.SSLContext | None
    """

    return build_target_ssl_context(
        tls_legacy=is_tls_legacy,
        client_cert=client_cert,
        client_key=client_key,
        client_key_password_env=client_key_password_env,
    )


def _resolve_client_key_password(client_key_password_env):
    """Resolve an encrypted-key password from an environment variable.

    :param str | None client_key_password_env: Environment variable name.
    :raise ValueError: when the configured variable is missing.
    :return: Password value or None.
    :rtype: str | None
    """

    if not client_key_password_env:
        return None

    env_name = str(client_key_password_env).strip()
    if not env_name:
        return None

    if env_name not in os.environ:
        raise ValueError('Client key password environment variable `{0}` is not set'.format(env_name))

    return os.environ.get(env_name)


def emit_target_tls_policy(config, tpl):
    """Emit privacy-safe debug output for opt-in target TLS modes.

    :param object config: Runtime configuration object.
    :param object tpl: Terminal/output provider.
    :return: None
    """

    debug = getattr(tpl, 'debug', lambda *args, **kwargs: True)

    if getattr(config, 'is_tls_legacy', False) is True:
        debug(msg='TLS legacy compatibility enabled: ciphers={0}'.format(TLS_LEGACY_CIPHERS))

    if getattr(config, 'is_client_cert_enabled', False) is True:
        debug(msg='TLS client certificate authentication enabled')


def emit_tls_legacy_policy(config, tpl):
    """Emit debug output for opt-in legacy TLS compatibility.

    :param object config: Runtime configuration object.
    :param object tpl: Terminal/output provider.
    :return: None
    """

    emit_target_tls_policy(config, tpl)


def tls_pool_kwargs(ssl_context):
    """Return urllib3 TLS kwargs only when a custom SSL context is available.

    :param ssl.SSLContext | None ssl_context: Optional custom SSL context.
    :return: TLS keyword arguments for urllib3 pool constructors/managers.
    :rtype: dict
    """

    if ssl_context is None:
        return {}

    return {'ssl_context': ssl_context}


def warn_tls_transport_error(config, tpl, error, line_finisher=None):
    """Store and print a compact TLS transport diagnostic when applicable.

    :param object config: Runtime configuration object.
    :param object tpl: Terminal/output provider.
    :param Exception error: Source urllib3/OpenSSL exception.
    :param callable | None line_finisher: Optional callback before terminal warning output.
    :return: Diagnostic message or None when the error is not TLS-specific.
    :rtype: str | None
    """

    message = describe_tls_transport_error(error)
    if not message:
        return None

    setattr(config, 'last_transport_error', message)

    if line_finisher is not None:
        line_finisher()

    tpl.warning(msg=message)
    return message


def _compact_error_message(error):
    """
    Format nested TLS/transport errors without multiline tracebacks.

    :param Exception error: Source exception.
    :return: Compact error message.
    :rtype: str
    """

    message = str(getattr(error, 'reason', None) or error)
    message = re.sub(r'\s+', ' ', message).strip()
    return message


def describe_tls_transport_error(error):
    """
    Convert known TLS failures into actionable scanner diagnostics.

    :param Exception error: urllib3/OpenSSL exception.
    :return: Diagnostic message, or None when the error is not TLS-specific.
    :rtype: str | None
    """

    message = _compact_error_message(error)
    lowered = message.lower()

    name_resolution_markers = (
        'failed to resolve',
        'name or service not known',
        'nodename nor servname provided',
        'temporary failure in name resolution',
        'no address associated with hostname',
        'nameresolutionerror',
    )
    if any(marker in lowered for marker in name_resolution_markers):
        return None

    if 'dh key too small' in lowered or 'dh_key_too_small' in lowered:
        return (
            'TLS handshake failed: DH_KEY_TOO_SMALL. '
            'Server offered weak DHE/DH parameters. {hint}'
        ).format(hint=TLS_LEGACY_HINT)

    if 'ssl' in lowered or 'tls' in lowered:
        max_length = 220
        if len(message) > max_length:
            message = '{0}...'.format(message[:max_length - 3])
        return 'TLS handshake failed: {0}'.format(message)

    return None
