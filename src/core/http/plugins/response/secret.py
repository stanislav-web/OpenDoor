# -*- coding: utf-8 -*-

"""
Passive secret leak response sniffer.

The detector intentionally stores only redacted values in metadata. Never persist
raw secrets, bearer tokens, private keys or credentials in reports.
"""

import base64
import json
import re
import time

from .provider import ResponsePluginProvider


class SecretResponsePlugin(ResponsePluginProvider):
    """Detect likely leaked secrets in HTTP response bodies."""

    DESCRIPTION = 'Secret Leak (detect leaked API keys, JWTs, cloud keys and DB credentials)'
    RESPONSE_INDEX = 'secret'

    def __init__(self, _void):
        """
        ResponsePluginProvider constructor.

        :param mixed void: optional plugin value, unused
        """

        ResponsePluginProvider.__init__(self)


    MAX_BODY_BYTES = 1024 * 1024
    MAX_FINDINGS = 8
    JWT_MAX_PART_BYTES = 8192
    JWT_LONG_LIVED_SECONDS = 30 * 24 * 60 * 60
    TEXTUAL_CONTENT_TYPES = (
        '',
        'text/html',
        'text/plain',
        'text/json',
        'text/javascript',
        'application/json',
        'application/javascript',
        'application/problem+json',
        'application/xml',
        'text/xml',
        'application/xhtml+xml',
        'application/x-www-form-urlencoded',
    )
    BINARY_CONTENT_TYPES = (
        'application/octet-stream',
        'application/zip',
        'application/x-zip-compressed',
        'application/gzip',
        'application/x-gzip',
        'application/pdf',
        'application/vnd.',
        'font/',
        'image/',
        'audio/',
        'video/',
    )

    AWS_ACCESS_KEY_RE = re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b')
    JWT_RE = re.compile(
        r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b'
    )
    PRIVATE_KEY_RE = re.compile(
        r'-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----',
        re.IGNORECASE,
    )
    GOOGLE_API_KEY_RE = re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b')
    GITHUB_TOKEN_RE = re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,255}\b')
    GITHUB_FINE_GRAINED_TOKEN_RE = re.compile(r'\bgithub_pat_[A-Za-z0-9_]{40,255}\b')
    SLACK_TOKEN_RE = re.compile(
        r'\bxox[baprs]-(?:\d-)?(?:\d{8,15}-){1,3}[A-Za-z0-9]{20,}\b'
    )
    STRIPE_KEY_RE = re.compile(r'\b(?:sk|rk)_(?:live|test)_[0-9A-Za-z]{16,}\b')
    SQUARE_TOKEN_RE = re.compile(r'\bsq0(?:csp|scp|atp)-[0-9A-Za-z_-]{20,}\b')
    AUTHORIZATION_BEARER_RE = re.compile(
        r'(?i)\bauthorization\b\s*[:=]\s*[\"\']?bearer\s+([A-Za-z0-9._~+/=-]{20,})'
    )
    DB_URL_RE = re.compile(
        r'\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^:\s/@]{1,80}:[^@\s]{6,}@[^\'"\s<>]+',
        re.IGNORECASE,
    )
    ASSIGNMENT_RE = re.compile(
        r'(?i)\b(?:api[_-]?key|secret[_-]?key|secretkey|access[_-]?key|access[_-]?secret|access[_-]?token|auth[_-]?token|client[_-]?secret|account[_-]?key|accountkey|db[_-]?password|password|pwd)\b'
        r'\s*[:=]\s*[\'"]([^\'"\s]{12,})[\'"]'
    )

    DETECTION_TYPE_JWT = 'jwt'  # nosec B105 - detector type id, not a credential.
    DETECTION_TYPE_GENERIC_ASSIGNMENT = (
        'generic_assignment'  # nosec B105 - detector type id, not a credential.
    )
    DETECTION_TYPE_SLACK_TOKEN = 'slack_token'  # nosec B105 - detector type id, not a credential.
    DETECTION_TYPE_AUTHORIZATION_BEARER = (
        'authorization_bearer'  # nosec B105 - detector type id, not a credential.
    )
    CKEDITOR_ADVANCED_DIALOG_FIELD_NAMES = frozenset((
        'advId',
        'advLangDir',
        'advAccessKey',
        'advName',
        'advLangCode',
        'advTabIndex',
        'advTitle',
        'advContentType',
        'advCSSClasses',
        'advCharset',
        'advStyles',
        'advRel',
    ))
    CAPTURE_GROUP_RULES = (
        DETECTION_TYPE_GENERIC_ASSIGNMENT,
        DETECTION_TYPE_AUTHORIZATION_BEARER,
    )

    SECRET_RULES = (
        ('aws_access_key', AWS_ACCESS_KEY_RE, 95),
        (DETECTION_TYPE_JWT, JWT_RE, 90),
        ('private_key', PRIVATE_KEY_RE, 98),
        ('google_api_key', GOOGLE_API_KEY_RE, 90),
        ('github_token', GITHUB_TOKEN_RE, 95),
        ('github_fine_grained_token', GITHUB_FINE_GRAINED_TOKEN_RE, 95),
        (DETECTION_TYPE_SLACK_TOKEN, SLACK_TOKEN_RE, 95),
        ('stripe_key', STRIPE_KEY_RE, 95),
        ('square_token', SQUARE_TOKEN_RE, 92),
        (DETECTION_TYPE_AUTHORIZATION_BEARER, AUTHORIZATION_BEARER_RE, 88),
        ('database_url', DB_URL_RE, 92),
        (DETECTION_TYPE_GENERIC_ASSIGNMENT, ASSIGNMENT_RE, 70),
    )

    @classmethod
    def process(cls, response):
        """
        Detect secrets and annotate the response object.

        :param response: HTTP response-like object
        :return: secret bucket name when a secret-like value was detected
        :rtype: str|None
        """

        if cls._is_supported_status(response) is not True:
            return None

        if cls._is_textual_response(response) is not True:
            return None

        body = cls._extract_body(response)
        if not body:
            return None

        detection = cls.detect(body)
        if detection is None:
            return None

        try:
            setattr(response, 'opendoor_secret_detection', detection)
        except (AttributeError, TypeError):
            pass

        return cls.RESPONSE_INDEX

    @classmethod
    def detect(cls, text):
        """
        Detect secret-like values in text.

        :param str text: decoded response body
        :return: detection metadata or None
        :rtype: dict|None
        """

        findings = []
        seen = set()

        for secret_type, pattern, confidence in cls.SECRET_RULES:
            for match in pattern.finditer(str(text or '')):
                value = (
                    match.group(1)
                    if secret_type in cls.CAPTURE_GROUP_RULES and match.groups()
                    else match.group(0)
                )
                if cls._is_probable_false_positive(secret_type, value):
                    continue

                key = (secret_type, value)
                if key in seen:
                    continue

                seen.add(key)
                finding = {
                    'type': secret_type,
                    'redacted': cls.redact(value),
                    'confidence': confidence,
                    'position': int(match.start()),
                }

                if secret_type == cls.DETECTION_TYPE_JWT:
                    jwt_claims = cls._extract_jwt_claims_metadata(value)
                    if jwt_claims:
                        finding['jwt_claims'] = jwt_claims

                findings.append(finding)

                if len(findings) >= cls.MAX_FINDINGS:
                    return cls._build_detection(findings)

        if len(findings) <= 0:
            return None

        return cls._build_detection(findings)

    @classmethod
    def _build_detection(cls, findings):
        """
        Build normalized detection metadata.

        :param list findings: detected secret metadata
        :return: detection metadata
        :rtype: dict
        """

        top = max(findings, key=lambda item: item.get('confidence', 0))
        types = sorted({item.get('type') for item in findings if item.get('type')})

        detection = {
            'type': top.get('type'),
            'redacted': top.get('redacted'),
            'confidence': int(top.get('confidence', 0)),
            'count': len(findings),
            'types': types,
            'matches': findings[:cls.MAX_FINDINGS],
        }

        if isinstance(top.get('jwt_claims'), dict) and top.get('jwt_claims'):
            detection['jwt_claims'] = dict(top.get('jwt_claims'))

        return detection

    @classmethod
    def _is_supported_status(cls, response):
        """
        Run only on 200 OK responses.

        :param response: HTTP response-like object
        :return: check result
        :rtype: bool
        """

        return cls._is_response_status_in(response, (200,))

    @classmethod
    def _get_header(cls, response, name):
        """
        Return a response header value using case-insensitive lookup.

        :param response: HTTP response-like object
        :param str name: header name
        :return: header value or None
        """

        return cls._get_response_header(response, name)

    @classmethod
    def _extract_content_type(cls, response):
        """
        Extract normalized Content-Type without parameters.

        :param response: HTTP response-like object
        :return: normalized content type
        :rtype: str
        """

        return cls._extract_response_content_type(response)

    @classmethod
    def _is_textual_response(cls, response):
        """
        Decide whether the response body is safe and useful for secret scanning.

        :param response: HTTP response-like object
        :return: True when response content type can contain textual secrets
        :rtype: bool
        """

        content_type = cls._extract_content_type(response)

        if content_type in cls.TEXTUAL_CONTENT_TYPES:
            return True

        if content_type.endswith(('+json', '+xml')):
            return True

        for item in cls.BINARY_CONTENT_TYPES:
            if content_type.startswith(item):
                return False

        return False

    @classmethod
    def _extract_body(cls, response):
        """
        Decode a bounded response body.

        :param response: HTTP response-like object
        :return: decoded body
        :rtype: str
        """

        return cls._extract_response_body(response, cls.MAX_BODY_BYTES)

    @staticmethod
    def redact(value):
        """
        Redact a secret-like value for reports.

        :param str value: raw detected value
        :return: redacted value
        :rtype: str
        """

        value = str(value or '')
        if len(value) <= 8:
            return '*' * len(value)

        return '{0}****{1}'.format(value[:4], value[-4:])

    @classmethod
    def _is_probable_false_positive(cls, secret_type, value):
        """
        Reduce obvious examples/placeholders.

        :param str secret_type: detected secret type
        :param str value: detected value
        :return: whether value should be ignored
        :rtype: bool
        """

        normalized = str(value or '').lower()

        false_markers = (
            'example',
            'sample',
            'dummy',
            'placeholder',
            'changeme',
            'redacted',
            'masked',
            'your_',
            'insert_',
            '<',
            '>',
            '${',
            '{{',
        )

        if any(marker in normalized for marker in false_markers):
            return True

        if secret_type == cls.DETECTION_TYPE_JWT:
            return cls._looks_like_unsigned_or_placeholder_jwt(value)

        if secret_type == cls.DETECTION_TYPE_SLACK_TOKEN:
            return cls._looks_like_slack_token(value) is not True

        if secret_type == cls.DETECTION_TYPE_GENERIC_ASSIGNMENT:
            if len(set(str(value))) <= 4:
                return True

            if str(value or '') in cls.CKEDITOR_ADVANCED_DIALOG_FIELD_NAMES:
                return True

        return False


    @classmethod
    def _looks_like_slack_token(cls, value):
        """
        Validate the structural shape of a Slack token candidate.

        This secondary check protects XML sitemaps and article URL slugs such as
        ``xoxa-v-priamure-nasli-smesnye-geograficeskie-obieekty`` from being
        promoted to high-confidence secret findings when a broader token-like
        matcher sees the ``xox*`` prefix.

        :param str value: candidate Slack token value
        :return: True when the value has Slack token structure
        :rtype: bool
        """

        parts = str(value or '').split('-')
        if len(parts) < 3:
            return False

        prefix = parts[0].lower()
        if prefix not in ('xoxb', 'xoxa', 'xoxp', 'xoxr', 'xoxs'):
            return False

        token_part = parts[-1]
        if re.fullmatch(r'[A-Za-z0-9]{20,}', token_part) is None:
            return False

        numeric_parts = parts[1:-1]
        if numeric_parts and numeric_parts[0] in ('1', '2'):
            numeric_parts = numeric_parts[1:]

        if not numeric_parts:
            return False

        return all(
            re.fullmatch(r'\d{8,15}', item or '') is not None
            for item in numeric_parts
        )

    @staticmethod
    def _looks_like_unsigned_or_placeholder_jwt(value):
        """
        Reject common unsigned/demo JWTs.

        :param str value: JWT-like value
        :return: whether token is likely not a real secret
        :rtype: bool
        """

        parts = str(value or '').split('.')
        if len(parts) != 3:
            return True

        try:
            header = parts[0] + ('=' * (-len(parts[0]) % 4))
            decoded = base64.urlsafe_b64decode(header.encode('ascii')).decode('utf-8', 'ignore')
            parsed = json.loads(decoded)
        except (TypeError, ValueError, json.JSONDecodeError):
            return False

        return str(parsed.get('alg', '')).lower() == 'none'

    @classmethod
    def _extract_jwt_claims_metadata(cls, value, now=None):
        """
        Extract bounded, non-verifying JWT metadata.

        :param str value: raw JWT-like token
        :param int|float|None now: optional timestamp for deterministic tests
        :return: bounded JWT metadata or empty dict
        :rtype: dict
        """

        parts = str(value or '').split('.')
        if len(parts) != 3:
            return {}

        header = cls._decode_jwt_json_part(parts[0])
        payload = cls._decode_jwt_json_part(parts[1])
        if not header and not payload:
            return {}

        metadata = {}

        for key in ('alg', 'typ', 'kid'):
            if key in header:
                safe_value = cls._bounded_jwt_string(header.get(key), 128)
                if safe_value:
                    metadata[key] = safe_value

        for key in ('iss',):
            if key in payload:
                safe_value = cls._bounded_jwt_string(payload.get(key), 256)
                if safe_value:
                    metadata[key] = safe_value

        if 'aud' in payload:
            audience = cls._bounded_jwt_audience(payload.get('aud'))
            if audience:
                metadata['aud'] = audience

        for key in ('exp', 'nbf', 'iat'):
            numeric_value = cls._jwt_numeric_date(payload.get(key))
            if numeric_value is not None:
                metadata[key] = numeric_value

        risk_flags = cls._jwt_risk_flags(header, payload, now=now)
        if risk_flags:
            metadata['risk_flags'] = risk_flags

        return metadata

    @classmethod
    def _decode_jwt_json_part(cls, part):
        """
        Decode one bounded JWT JSON segment without verification.

        :param str part: base64url encoded JWT segment
        :return: decoded JSON object or empty dict
        :rtype: dict
        """

        value = str(part or '')
        if not value or len(value) > cls.JWT_MAX_PART_BYTES:
            return {}

        try:
            padded = value + ('=' * (-len(value) % 4))
            decoded = base64.urlsafe_b64decode(padded.encode('ascii')).decode(
                'utf-8',
                'ignore',
            )
            parsed = json.loads(decoded)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}

        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _bounded_jwt_string(value, limit):
        """
        Return a bounded JWT metadata string.

        :param mixed value: candidate value
        :param int limit: maximum length
        :return: bounded string or None
        :rtype: str|None
        """

        if not isinstance(value, str):
            return None

        value = value.strip()
        if not value:
            return None

        return value[:limit]

    @classmethod
    def _bounded_jwt_audience(cls, value):
        """
        Return a bounded JWT audience value.

        :param mixed value: JWT aud claim
        :return: bounded audience metadata
        :rtype: str|list|None
        """

        if isinstance(value, str):
            return cls._bounded_jwt_string(value, 128)

        if isinstance(value, list):
            items = []
            for item in value[:5]:
                safe_value = cls._bounded_jwt_string(item, 128)
                if safe_value:
                    items.append(safe_value)

            return items or None

        return None

    @staticmethod
    def _jwt_numeric_date(value):
        """
        Normalize a JWT numeric date value.

        :param mixed value: claim value
        :return: integer timestamp or None
        :rtype: int|None
        """

        if isinstance(value, bool):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _jwt_risk_flags(cls, header, payload, now=None):
        """
        Build conservative JWT metadata risk flags.

        :param dict header: decoded JWT header
        :param dict payload: decoded JWT payload
        :param int|float|None now: optional timestamp for deterministic tests
        :return: sorted risk flag list
        :rtype: list
        """

        flags = []
        current_time = int(time.time() if now is None else now)

        if str(header.get('alg', '')).lower() == 'none':
            flags.append('alg_none')

        exp = cls._jwt_numeric_date(payload.get('exp'))
        nbf = cls._jwt_numeric_date(payload.get('nbf'))
        iat = cls._jwt_numeric_date(payload.get('iat'))

        if exp is None:
            flags.append('missing_exp')
        elif exp < current_time:
            flags.append('expired')

        if nbf is not None and nbf > current_time:
            flags.append('not_yet_valid')

        if exp is not None and iat is not None:
            if exp - iat > cls.JWT_LONG_LIVED_SECONDS:
                flags.append('long_lived')

        return flags
