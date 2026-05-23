# -*- coding: utf-8 -*-

"""
    Wordlist source metadata helpers.

    This module classifies the configured scan wordlist as one of:
    bundled, local, or remote. It intentionally does not download remote
    wordlists and does not change scan counters.
"""

from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class WordlistSource:
    """Describe where a scan wordlist comes from.

    :param source_type: Source type: bundled, local, or remote.
    :param value: Original configured source value.
    :param resolved_value: Runtime local file path after source resolution.
    :param scheme: URL scheme when the source is URL-like.
    """

    source_type: str
    value: str | None = None
    resolved_value: str | None = None
    scheme: str | None = None

    BUNDLED = 'bundled'
    LOCAL = 'local'
    REMOTE = 'remote'

    INTERNAL_MARKER = 'internal'
    EXTERNAL_MARKER = 'external'

    REMOTE_SCHEMES = ('http', 'https')

    @classmethod
    def bundled(cls):
        """Build metadata for an OpenDoor bundled wordlist.

        :return: Bundled wordlist source metadata.
        :rtype: WordlistSource
        """

        return cls(source_type=cls.BUNDLED)

    @classmethod
    def local(cls, value, resolved_value=None):
        """Build metadata for a local external wordlist.

        :param str value: Original local path.
        :param str | None resolved_value: Runtime local path.
        :return: Local wordlist source metadata.
        :rtype: WordlistSource
        """

        return cls(
            source_type=cls.LOCAL,
            value=value,
            resolved_value=resolved_value or value,
        )

    @classmethod
    def remote(cls, value, resolved_value=None):
        """Build metadata for a remote HTTP(S) external wordlist.

        :param str value: Original remote URL.
        :param str | None resolved_value: Runtime local path after download.
        :return: Remote wordlist source metadata.
        :rtype: WordlistSource
        """

        parsed = urlsplit(str(value or ''))
        return cls(
            source_type=cls.REMOTE,
            value=value,
            resolved_value=resolved_value,
            scheme=parsed.scheme.lower() or None,
        )

    @classmethod
    def from_value(cls, value, resolved_value=None):
        """Classify a configured wordlist value.

        :param str | None value: Configured wordlist value.
        :param str | None resolved_value: Runtime local path after source resolution.
        :return: Wordlist source metadata.
        :rtype: WordlistSource
        """

        if value is None:
            return cls.bundled()

        parsed = urlsplit(str(value))
        scheme = parsed.scheme.lower()

        if scheme in cls.REMOTE_SCHEMES:
            return cls.remote(value, resolved_value=resolved_value)

        return cls.local(value, resolved_value=resolved_value)

    @classmethod
    def from_scan_params(cls, params, list_name):
        """Resolve source metadata for a banner/list row.

        A custom ``--wordlist`` only applies to the active scan list. Other
        rows still represent bundled OpenDoor lists.

        :param dict | None params: CLI params.
        :param str list_name: Banner list name, e.g. directories or subdomains.
        :return: Wordlist source metadata.
        :rtype: WordlistSource
        """

        params = params or {}

        if params.get('scan') != list_name:
            return cls.bundled()

        return cls.from_value(
            params.get('wordlist'),
            resolved_value=params.get('resolved_wordlist') or params.get('wordlist_resolved_path'),
        )

    @property
    def marker(self):
        """Return user-facing banner marker.

        :return: internal for bundled, external for local/remote.
        :rtype: str
        """

        if self.source_type == self.BUNDLED:
            return self.INTERNAL_MARKER

        return self.EXTERNAL_MARKER

    @property
    def is_bundled(self):
        """Return whether the source is a bundled OpenDoor wordlist.

        :return: True when bundled.
        :rtype: bool
        """

        return self.source_type == self.BUNDLED

    @property
    def is_local(self):
        """Return whether the source is a local external wordlist.

        :return: True when local.
        :rtype: bool
        """

        return self.source_type == self.LOCAL

    @property
    def is_remote(self):
        """Return whether the source is a remote HTTP(S) external wordlist.

        :return: True when remote.
        :rtype: bool
        """

        return self.source_type == self.REMOTE

    @property
    def runtime_path(self):
        """Return the local file path that can be counted/read, if available.

        :return: Runtime local path or None.
        :rtype: str | None
        """

        return self.resolved_value or (self.value if self.is_local else None)
