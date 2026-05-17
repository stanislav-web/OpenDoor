# -*- coding: utf-8 -*-

"""
Passive secret leak response sniffer.

The detector intentionally stores only redacted values in metadata. Never persist
raw secrets, bearer tokens, private keys or credentials in reports.
"""

import base64
import json
import re

from src.core import helper
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
    SLACK_TOKEN_RE = re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}\b')
    STRIPE_KEY_RE = re.compile(r'\b(?:sk|rk)_(?:live|test)_[0-9A-Za-z]{16,}\b')
    DB_URL_RE = re.compile(
        r'\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^:\s/@]{1,80}:[^@\s]{6,}@[^\'"\s<>]+',
        re.IGNORECASE,
    )
    ASSIGNMENT_RE = re.compile(
        r'(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|db[_-]?password|password)\b'
        r'\s*[:=]\s*[\'"]([^\'"\s]{12,})[\'"]'
    )

    DETECTION_TYPE_JWT = 'jwt'  # nosec B105 - detector type id, not a credential.
    DETECTION_TYPE_GENERIC_ASSIGNMENT = (
        'generic_assignment'  # nosec B105 - detector type id, not a credential.
    )

    SECRET_RULES = (
        ('aws_access_key', AWS_ACCESS_KEY_RE, 95),
        (DETECTION_TYPE_JWT, JWT_RE, 90),
        ('private_key', PRIVATE_KEY_RE, 98),
        ('google_api_key', GOOGLE_API_KEY_RE, 90),
        ('github_token', GITHUB_TOKEN_RE, 95),
        ('slack_token', SLACK_TOKEN_RE, 95),
        ('stripe_key', STRIPE_KEY_RE, 95),
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
                    if secret_type == cls.DETECTION_TYPE_GENERIC_ASSIGNMENT and match.groups()
                    else match.group(0)
                )
                if cls._is_probable_false_positive(secret_type, value):
                    continue

                key = (secret_type, value)
                if key in seen:
                    continue

                seen.add(key)
                findings.append({
                    'type': secret_type,
                    'redacted': cls.redact(value),
                    'confidence': confidence,
                    'position': int(match.start()),
                })

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

        return {
            'type': top.get('type'),
            'redacted': top.get('redacted'),
            'confidence': int(top.get('confidence', 0)),
            'count': len(findings),
            'types': types,
            'matches': findings[:cls.MAX_FINDINGS],
        }

    @classmethod
    def _is_supported_status(cls, response):
        """
        Run only on 200 OK responses.

        :param response: HTTP response-like object
        :return: check result
        :rtype: bool
        """

        try:
            return int(getattr(response, 'status', 0)) == 200
        except (TypeError, ValueError):
            return False

    @classmethod
    def _get_header(cls, response, name):
        """
        Return a response header value using case-insensitive lookup.

        :param response: HTTP response-like object
        :param str name: header name
        :return: header value or None
        """

        headers = getattr(response, 'headers', {}) or {}
        if name in headers:
            return headers[name]

        target = str(name).lower()
        for key, value in headers.items():
            if str(key).lower() == target:
                return value

        return None

    @classmethod
    def _extract_content_type(cls, response):
        """
        Extract normalized Content-Type without parameters.

        :param response: HTTP response-like object
        :return: normalized content type
        :rtype: str
        """

        value = cls._get_header(response, 'Content-Type')
        if value is None:
            return ''

        return str(value).split(';', 1)[0].strip().lower()

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

        data = getattr(response, 'data', b'')
        if data is None:
            return ''

        if isinstance(data, bytes):
            data = data[:cls.MAX_BODY_BYTES]
            return helper.decode(data, errors='ignore')

        return str(data)[:cls.MAX_BODY_BYTES]

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

        if secret_type == cls.DETECTION_TYPE_GENERIC_ASSIGNMENT:
            if len(set(str(value))) <= 4:
                return True

        return False

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
