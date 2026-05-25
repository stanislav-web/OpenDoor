# -*- coding: utf-8 -*-

"""
    TLS helpers for OpenDoor request providers.

    Legacy compatibility is opt-in only. The default scanner transport keeps the
    platform/Python OpenSSL policy unchanged.
"""

import re
import ssl


TLS_LEGACY_CIPHERS = 'DEFAULT:!DHE'
TLS_LEGACY_HINT = 'Retry with --tls-legacy or fix server TLS configuration.'


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


def maybe_build_ssl_context(is_tls_legacy):
    """
    Return an SSL context only when legacy TLS compatibility is enabled.

    :param bool is_tls_legacy: Whether the opt-in legacy TLS mode is enabled.
    :return: SSL context or None
    :rtype: ssl.SSLContext | None
    """

    if is_tls_legacy is True:
        return build_legacy_ssl_context()

    return None


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
