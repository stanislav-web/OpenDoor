# -*- coding: utf-8 -*-

"""Shared sniffer result primitives."""

PASSIVE_FINDING_SEVERITIES = ('info', 'low', 'medium', 'high', 'critical')
PASSIVE_FINDING_CONFIDENCES = ('low', 'medium', 'high')
PASSIVE_FINDING_DEFAULT_REASON = 'unspecified'
PASSIVE_FINDING_MAX_STRING_LENGTH = 240
PASSIVE_FINDING_MAX_LIST_ITEMS = 10
PASSIVE_FINDING_MAX_DICT_ITEMS = 20
PASSIVE_FINDING_MAX_DEPTH = 2
PASSIVE_FINDING_REDACTED_VALUE = '[redacted]'

_SEVERITY_ALIASES = {
    'notice': 'info',
    'warning': 'medium',
    'warn': 'medium',
    'error': 'high',
    'fatal': 'critical',
}

_CONFIDENCE_ALIASES = {
    'weak': 'low',
    'strong': 'high',
    'certain': 'high',
}

_SAFE_EVIDENCE_KEYS = {
    'cookie_name',
    'cookie_names',
    'header_name',
    'header_names',
}

_SENSITIVE_EVIDENCE_KEY_PARTS = (
    'authorization',
    'cookie',
    'jwt',
    'passwd',
    'password',
    'private_key',
    'secret',
    'session',
    'token',
)


def normalize_passive_severity(value):
    """
    Normalize passive finding severity.

    Unknown values intentionally fall back to ``info`` so new passive checks do
    not accidentally overstate risk.

    :param str | None value: raw severity
    :return: normalized severity
    :rtype: str
    """

    severity = str(value or '').strip().lower()
    severity = _SEVERITY_ALIASES.get(severity, severity)

    if severity in PASSIVE_FINDING_SEVERITIES:
        return severity

    return 'info'


def normalize_passive_confidence(value):
    """
    Normalize passive finding confidence.

    Unknown values fall back to ``medium`` because confidence describes signal
    quality, not vulnerability impact.

    :param str | None value: raw confidence
    :return: normalized confidence
    :rtype: str
    """

    confidence = str(value or '').strip().lower()
    confidence = _CONFIDENCE_ALIASES.get(confidence, confidence)

    if confidence in PASSIVE_FINDING_CONFIDENCES:
        return confidence

    return 'medium'


def bounded_passive_evidence(evidence, max_string_length=PASSIVE_FINDING_MAX_STRING_LENGTH,
                             max_list_items=PASSIVE_FINDING_MAX_LIST_ITEMS,
                             max_dict_items=PASSIVE_FINDING_MAX_DICT_ITEMS,
                             max_depth=PASSIVE_FINDING_MAX_DEPTH):
    """
    Return redacted and bounded evidence for passive findings.

    The passive contract accepts dictionaries only. Non-dict inputs are ignored
    to avoid accidental body dumps or unstructured sensitive values.

    :param dict | None evidence: raw evidence
    :param int max_string_length: maximum string value length
    :param int max_list_items: maximum list/tuple item count
    :param int max_dict_items: maximum dict item count
    :param int max_depth: maximum nested structure depth
    :return: safe evidence dictionary
    :rtype: dict
    """

    if not isinstance(evidence, dict):
        return {}

    return _bound_passive_mapping(
        evidence,
        max_string_length=max_string_length,
        max_list_items=max_list_items,
        max_dict_items=max_dict_items,
        max_depth=max_depth,
        depth=0,
    )


def passive_finding_source(signal, request_method=None, status=None):
    """
    Build normalized source metadata for passive findings.

    :param str signal: source signal identifier
    :param str | None request_method: request method
    :param str | int | None status: response status
    :return: source metadata
    :rtype: dict
    """

    source = {'signal': _truncate_passive_string(signal)}

    if request_method is not None:
        source['request_method'] = str(request_method).strip().upper()
    if status is not None:
        source['status'] = int(status) if str(status).isdigit() else str(status)

    return source


class PassiveFinding:
    """Normalized passive finding contract for future sniffer metadata."""

    __slots__ = (
        'bucket',
        'confidence',
        'evidence',
        'reason',
        'severity',
        'source',
        'type',
        'url',
    )

    def __init__(self, bucket, finding_type, url, severity='info', reason=None,
                 confidence='medium', evidence=None, source=None):
        """
        Create a normalized passive finding.

        :param str bucket: report bucket name
        :param str finding_type: finding type inside the bucket
        :param str url: source URL
        :param str severity: normalized or alias severity
        :param str | None reason: stable reason identifier
        :param str confidence: normalized or alias confidence
        :param dict | None evidence: bounded/redacted evidence
        :param dict | None source: source metadata
        """

        self.bucket = _truncate_passive_string(bucket)
        self.type = _truncate_passive_string(finding_type)
        self.url = _truncate_passive_string(url)
        self.severity = normalize_passive_severity(severity)
        self.reason = _normalize_passive_reason(reason)
        self.confidence = normalize_passive_confidence(confidence)
        self.evidence = bounded_passive_evidence(evidence)
        self.source = bounded_passive_evidence(source)

    def to_dict(self):
        """
        Return the public passive finding dictionary shape.

        :return: passive finding contract dictionary
        :rtype: dict
        """

        return {
            'bucket': self.bucket,
            'type': self.type,
            'url': self.url,
            'severity': self.severity,
            'reason': self.reason,
            'confidence': self.confidence,
            'evidence': dict(self.evidence),
            'source': dict(self.source),
        }


def _bound_passive_mapping(mapping, max_string_length, max_list_items, max_dict_items, max_depth, depth):
    """Return a bounded dict copy."""

    safe = {}

    for key, value in list(mapping.items())[:max_dict_items]:
        if value is None:
            continue

        safe_key = _truncate_passive_string(key, max_string_length=max_string_length)
        if _is_sensitive_passive_key(safe_key):
            safe[safe_key] = PASSIVE_FINDING_REDACTED_VALUE
            continue

        safe[safe_key] = _bound_passive_value(
            value,
            max_string_length=max_string_length,
            max_list_items=max_list_items,
            max_dict_items=max_dict_items,
            max_depth=max_depth,
            depth=depth,
        )

    return safe


def _bound_passive_value(value, max_string_length, max_list_items, max_dict_items, max_depth, depth):
    """Return one bounded evidence value."""

    if isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, dict):
        if depth >= max_depth:
            return {}
        return _bound_passive_mapping(
            value,
            max_string_length=max_string_length,
            max_list_items=max_list_items,
            max_dict_items=max_dict_items,
            max_depth=max_depth,
            depth=depth + 1,
        )

    if isinstance(value, (list, tuple)):
        return [
            _bound_passive_value(
                item,
                max_string_length=max_string_length,
                max_list_items=max_list_items,
                max_dict_items=max_dict_items,
                max_depth=max_depth,
                depth=depth + 1,
            )
            for item in list(value)[:max_list_items]
        ]

    return _truncate_passive_string(value, max_string_length=max_string_length)


def _truncate_passive_string(value, max_string_length=PASSIVE_FINDING_MAX_STRING_LENGTH):
    """Return a bounded string value."""

    text = str(value or '').strip()
    if len(text) <= max_string_length:
        return text

    return text[:max_string_length - 3] + '...'


def _normalize_passive_reason(value):
    """Return a stable passive finding reason identifier."""

    reason = str(value or '').strip().lower().replace('-', '_').replace(' ', '_')
    reason = ''.join(char for char in reason if char.isalnum() or char == '_')

    return reason or PASSIVE_FINDING_DEFAULT_REASON


def _is_sensitive_passive_key(key):
    """Return True when an evidence key should never expose its value."""

    normalized = str(key or '').strip().lower().replace('-', '_').replace(' ', '_')
    if normalized in _SAFE_EVIDENCE_KEYS:
        return False

    return any(part in normalized for part in _SENSITIVE_EVIDENCE_KEY_PARTS)



class SnifferResult:
    """One independent sniffer finding."""

    __slots__ = (
        'bucket',
        'code',
        'evidence_key',
        'metadata',
        'size',
        'suppress_normal',
        'url',
    )

    def __init__(self, bucket, url, code=None, size=None, metadata=None, suppress_normal=False,
                 evidence_key=None):
        """
        Create one independent sniffer finding.

        :param str bucket: report bucket name
        :param str url: finding URL
        :param str | int | None code: HTTP status code
        :param str | int | None size: normalized response size
        :param dict | None metadata: report metadata
        :param bool suppress_normal: suppress base success reporting when True
        :param str | None evidence_key: optional dedupe evidence key
        """

        self.bucket = bucket
        self.url = url
        self.code = None if code is None else str(code)
        self.size = None if size is None else str(size)
        self.metadata = dict(metadata or {})
        self.suppress_normal = True is suppress_normal
        self.evidence_key = evidence_key

    def dedupe_key(self):
        """
        Build a stable bucket-local dedupe key.

        :return: tuple
        """

        evidence = self.evidence_key
        if evidence is None:
            evidence = self.metadata.get('evidence_key') or self.metadata.get('evidence') or '-'

        return self.bucket, self.url, str(evidence)


class SnifferDecision:
    """Multi-sniffer decision for one response."""

    __slots__ = ('findings', 'suppress_normal', 'suppress_reasons')

    def __init__(self):
        """Create an empty sniffer decision."""

        self.findings = []
        self.suppress_normal = False
        self.suppress_reasons = []

    def add(self, result):
        """
        Add one sniffer result.

        :param SnifferResult result: sniffer result to add
        :return: SnifferDecision
        """

        self.findings.append(result)

        if True is result.suppress_normal:
            self.suppress_normal = True
            reason = result.metadata.get('suppress_reason') or result.bucket
            self.suppress_reasons.append(reason)

        return self

    def extend(self, results):
        """
        Add several sniffer results.

        :param iterable results: sniffer results
        :return: SnifferDecision
        """

        for result in results or []:
            self.add(result)

        return self
