# -*- coding: utf-8 -*-

"""Shared sniffer result primitives."""


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
