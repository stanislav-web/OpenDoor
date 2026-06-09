# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development: Stanislav WEB
"""

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit


CRAWL_MAX_BODY_BYTES = 1024 * 1024
CRAWL_MAX_LINKS_PER_RESPONSE = 100
CRAWL_MAX_ENQUEUED_PER_SCAN = 1000

_ALLOWED_HTML_CONTENT_TYPES = ('text/html', 'application/xhtml+xml')
_SKIP_SCHEMES = ('data', 'javascript', 'mailto', 'tel')
_LINK_ATTRIBUTES = {
    'a': ('href',),
    'link': ('href',),
    'script': ('src',),
    'img': ('src',),
    'iframe': ('src',),
}


@dataclass(frozen=True)
class CrawlCandidate(object):

    """Normalized crawl URL candidate extracted from one response body."""

    url: str
    source_url: str
    tag: str
    attribute: str


@dataclass(frozen=True)
class CrawlExtractionResult(object):

    """Bounded crawl extraction result and counters for debug/runtime accounting."""

    candidates: tuple
    discovered: int = 0
    skipped_content_type: int = 0
    skipped_body_size: int = 0
    skipped_invalid: int = 0
    skipped_external: int = 0
    skipped_extension: int = 0
    skipped_duplicate: int = 0
    skipped_limit: int = 0


class CrawlState(object):

    """Bounded in-memory crawl deduplication state."""

    def __init__(self, max_enqueued=CRAWL_MAX_ENQUEUED_PER_SCAN):
        """
        Initialize bounded crawl state.

        :param int max_enqueued: Maximum unique crawl URLs accepted per scan.
        """

        self._max_enqueued = max(0, int(max_enqueued))
        self._seen_keys = set()
        self._enqueued = 0
        self._duplicates = 0
        self._skipped_limit = 0
        self._skipped_extraction = 0
        self._processed = 0

    @property
    def enqueued(self):
        """
        Return accepted crawl URL count.

        :return int: Accepted unique crawl URLs.
        """

        return self._enqueued

    @property
    def processed(self):
        """
        Return processed crawl-owned request count.

        :return int: Processed crawl request count.
        """

        return self._processed

    @property
    def duplicates(self):
        """
        Return duplicate crawl URL count.

        :return int: Duplicate crawl URLs rejected by this state.
        """

        return self._duplicates

    @property
    def skipped(self):
        """
        Return total skipped crawl URL count excluding duplicates.

        :return int: Skipped crawl URL count.
        """

        return self._skipped_extraction + self._skipped_limit

    @property
    def skipped_limit(self):
        """
        Return crawl URL count rejected by the scan-wide cap.

        :return int: Limit-skipped crawl URLs.
        """

        return self._skipped_limit

    def status(self, url):
        """
        Return reservation status without mutating the crawl state.

        :param str url: Normalized crawl URL.
        :return str: One of queued, duplicate, or limit.
        """

        if url in self._seen_keys:
            return 'duplicate'

        if self._enqueued >= self._max_enqueued:
            return 'limit'

        return 'queued'

    def reserve(self, url):
        """
        Reserve a normalized crawl URL before it is queued.

        :param str url: Normalized crawl URL.
        :return str: One of queued, duplicate, or limit.
        """

        status = self.status(url)
        if status == 'duplicate':
            self.skip_duplicate(url)
            return status
        if status == 'limit':
            self.skip_limit()
            return status

        self._seen_keys.add(url)
        self._enqueued += 1
        return status

    def record_extraction_result(self, result):
        """
        Record extraction-level counters that do not reach runtime enqueue dedup.

        :param CrawlExtractionResult result: Per-response crawl extraction result.
        :return None: Always None.
        """

        if result is None:
            return None

        self._duplicates += int(getattr(result, 'skipped_duplicate', 0) or 0)
        self._skipped_extraction += sum([
            int(getattr(result, 'skipped_content_type', 0) or 0),
            int(getattr(result, 'skipped_body_size', 0) or 0),
            int(getattr(result, 'skipped_invalid', 0) or 0),
            int(getattr(result, 'skipped_external', 0) or 0),
            int(getattr(result, 'skipped_extension', 0) or 0),
            int(getattr(result, 'skipped_limit', 0) or 0),
        ])
        return None

    def diagnostics_payload(self):
        """
        Return compact runtime diagnostics counters for terminal output.

        :return dict: Crawl runtime counters.
        """

        pending = max(0, self.enqueued - self.processed)

        return {
            'queued': self.enqueued,
            'processed': self.processed,
            'discovered': self.enqueued,
            'consumed': self.processed,
            'pending': pending,
            'duplicate': self.duplicates,
            'skipped': self.skipped,
        }

    def record_processed(self):
        """
        Record one processed crawl-owned request.

        :return int: Current processed crawl request count.
        """

        self._processed += 1
        return self._processed

    def skip_duplicate(self, url=None):
        """
        Record a duplicate crawl URL without increasing the accepted count.

        :param str | None url: Optional normalized URL to remember as seen.
        :return str: duplicate.
        """

        if url:
            self._seen_keys.add(url)
        self._duplicates += 1
        return 'duplicate'

    def skip_limit(self):
        """
        Record one crawl URL skipped by the scan-wide enqueue cap.

        :return str: limit.
        """

        self._skipped_limit += 1
        return 'limit'

    def close(self):
        """
        Release all crawl runtime state.

        :return None: Always None.
        """

        self._seen_keys.clear()
        self._enqueued = 0
        self._duplicates = 0
        self._skipped_limit = 0
        self._skipped_extraction = 0
        self._processed = 0

    reset = close


class _CrawlHTMLParser(HTMLParser):

    """Small HTML attribute collector for safe one-hop crawl discovery."""

    def __init__(self, max_links):
        """
        Initialize parser.

        :param int max_links: Maximum raw link attributes to collect.
        """

        super().__init__(convert_charrefs=True)
        self._max_links = max(0, int(max_links))
        self.links = []
        self.skipped_limit = 0

    def handle_starttag(self, tag, attrs):
        """
        Collect supported URL-bearing HTML attributes.

        :param str tag: HTML tag name.
        :param list attrs: HTML attributes.
        :return None: Always None.
        """

        if len(self.links) >= self._max_links:
            self.skipped_limit += 1
            return

        normalized_tag = str(tag or '').lower()
        attr_map = {str(name).lower(): value for name, value in attrs if name is not None}

        if normalized_tag == 'form':
            self._collect_form_action(attr_map)
            return

        for attribute in _LINK_ATTRIBUTES.get(normalized_tag, ()):  # pragma: no branch - tiny tuple loop
            self._append_link(normalized_tag, attribute, attr_map.get(attribute))

    def _collect_form_action(self, attr_map):
        """
        Collect safe GET form actions only.

        :param dict attr_map: Lower-cased form attributes.
        :return None: Always None.
        """

        method = str(attr_map.get('method') or 'get').strip().lower()
        if method != 'get':
            return

        self._append_link('form', 'action', attr_map.get('action'))

    def _append_link(self, tag, attribute, raw_url):
        """
        Append a raw link candidate while enforcing the per-response cap.

        :param str tag: Source tag.
        :param str attribute: Source attribute.
        :param str raw_url: Raw URL value.
        :return None: Always None.
        """

        if raw_url is None:
            return

        if len(self.links) >= self._max_links:
            self.skipped_limit += 1
            return

        self.links.append((tag, attribute, str(raw_url)))


def is_crawl_content_type(content_type, body=None):
    """
    Decide whether a response body is eligible for crawl extraction.

    :param str | None content_type: Response Content-Type header value.
    :param bytes | str | None body: Response body preview for empty content type fallback.
    :return bool: True when crawl extraction may parse the body.
    """

    if content_type:
        media_type = str(content_type).split(';', 1)[0].strip().lower()
        return media_type in _ALLOWED_HTML_CONTENT_TYPES

    if body is None:
        return False

    if isinstance(body, str):
        preview = body.lstrip()[:32].lower()
        return preview.startswith('<!doctype html') or preview.startswith('<html') or preview.startswith('<a ')

    preview = bytes(body).lstrip()[:64].lower()
    return preview.startswith(b'<!doctype html') or preview.startswith(b'<html') or preview.startswith(b'<a ')


def normalize_crawl_url(raw_url, source_url, ignore_extensions=None):
    """
    Normalize a discovered URL for same-origin crawl enqueue/dedup.

    :param str raw_url: Raw URL extracted from HTML.
    :param str source_url: Absolute response URL that contained the raw URL.
    :param list | tuple | set | None ignore_extensions: File extensions to skip.
    :return tuple: (normalized_url, skipped_reason). Reason is None when URL is accepted.
    """

    raw_value = str(raw_url or '').strip()
    if not raw_value or raw_value.startswith('#'):
        return None, 'invalid'

    raw_scheme = urlsplit(raw_value).scheme.lower()
    if raw_scheme in _SKIP_SCHEMES:
        return None, 'invalid'

    try:
        absolute_url = urljoin(str(source_url), raw_value)
        source_origin = _origin_tuple(source_url)
        target = urlsplit(absolute_url)
        target_origin = _origin_tuple(absolute_url)
    except (TypeError, ValueError):
        return None, 'invalid'

    if target_origin is None or source_origin is None:
        return None, 'invalid'

    if target_origin != source_origin:
        return None, 'external'

    normalized = _normalized_url(target)
    if _has_ignored_extension(target.path, ignore_extensions):
        return None, 'extension'

    return normalized, None


def extract_crawl_candidates(
        source_url,
        body,
        content_type=None,
        ignore_extensions=None,
        max_body_bytes=CRAWL_MAX_BODY_BYTES,
        max_links_per_response=CRAWL_MAX_LINKS_PER_RESPONSE):
    """
    Extract bounded same-origin crawl candidates from one HTML response body.

    :param str source_url: Absolute response URL.
    :param bytes | str | None body: Response body.
    :param str | None content_type: Response Content-Type header value.
    :param list | tuple | set | None ignore_extensions: File extensions to skip.
    :param int max_body_bytes: Maximum body bytes to parse.
    :param int max_links_per_response: Maximum raw link attributes to collect.
    :return CrawlExtractionResult: Extraction result.
    """

    body_length = len(body or b'')
    if body_length > int(max_body_bytes):
        return CrawlExtractionResult(candidates=(), skipped_body_size=1)

    if not is_crawl_content_type(content_type, body):
        return CrawlExtractionResult(candidates=(), skipped_content_type=1)

    parser = _CrawlHTMLParser(max_links_per_response)
    parser.feed(_decode_body(body))

    candidates = []
    seen_response_urls = set()
    skipped = {
        'invalid': 0,
        'external': 0,
        'extension': 0,
        'duplicate': 0,
    }

    for tag, attribute, raw_url in parser.links:
        normalized_url, reason = normalize_crawl_url(raw_url, source_url, ignore_extensions)
        if reason is not None:
            skipped[reason] += 1
            continue

        if normalized_url in seen_response_urls:
            skipped['duplicate'] += 1
            continue

        seen_response_urls.add(normalized_url)
        candidates.append(CrawlCandidate(
            url=normalized_url,
            source_url=_normalized_url(urlsplit(source_url)),
            tag=tag,
            attribute=attribute,
        ))

    return CrawlExtractionResult(
        candidates=tuple(candidates),
        discovered=len(parser.links),
        skipped_invalid=skipped['invalid'],
        skipped_external=skipped['external'],
        skipped_extension=skipped['extension'],
        skipped_duplicate=skipped['duplicate'],
        skipped_limit=parser.skipped_limit,
    )


def _decode_body(body):
    """
    Decode a response body for HTMLParser.

    :param bytes | str | None body: Response body.
    :return str: Decoded body.
    """

    if body is None:
        return ''

    if isinstance(body, str):
        return body

    return bytes(body).decode('utf-8', errors='replace')


def _origin_tuple(url):
    """
    Return strict same-origin tuple.

    :param str url: Absolute URL.
    :return tuple | None: (scheme, host, port) or None.
    """

    parsed = urlsplit(str(url))
    scheme = parsed.scheme.lower()
    if scheme not in ('http', 'https'):
        return None

    hostname = parsed.hostname
    if not hostname or parsed.username or parsed.password:
        return None

    port = parsed.port or _default_port(scheme)
    return scheme, hostname.lower(), port


def _normalized_url(parsed):
    """
    Render a normalized URL without fragments.

    :param urllib.parse.SplitResult parsed: Parsed URL.
    :return str: Normalized URL.
    """

    scheme = parsed.scheme.lower()
    host = (parsed.hostname or '').lower()
    if ':' in host and not host.startswith('['):
        host = '[{}]'.format(host)

    port = parsed.port
    if port is not None and port != _default_port(scheme):
        netloc = '{}:{}'.format(host, port)
    else:
        netloc = host

    path = parsed.path or '/'
    return urlunsplit((scheme, netloc, path, parsed.query, ''))


def _default_port(scheme):
    """
    Return the default TCP port for an HTTP URL scheme.

    :param str scheme: URL scheme.
    :return int: Default port.
    """

    return 443 if str(scheme).lower() == 'https' else 80


def _has_ignored_extension(path, ignore_extensions):
    """
    Check whether URL path extension is ignored.

    :param str path: URL path.
    :param list | tuple | set | None ignore_extensions: Configured ignored extensions.
    :return bool: True when path extension is ignored.
    """

    if not ignore_extensions:
        return False

    normalized_extensions = {str(item).strip().lower().lstrip('.') for item in ignore_extensions if str(item).strip()}
    if not normalized_extensions or '.' not in str(path):
        return False

    extension = str(path).rsplit('.', 1)[-1].lower()
    return extension in normalized_extensions
