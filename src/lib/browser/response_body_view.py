# -*- coding: utf-8 -*-

"""Bounded response body helpers for passive scanner features."""

import json
import re
from html.parser import HTMLParser

from src.core import helper


class _ResponseBodyHtmlParser(HTMLParser):
    """Collect bounded HTML hints without executing or loading resources."""

    HIDDEN_TAGS = {'script', 'style', 'noscript', 'template'}
    URL_ATTRS = {'action', 'data-endpoint', 'data-href', 'data-url', 'href', 'src'}

    def __init__(self, max_hints):
        """
        Initialize parser state.

        :param int max_hints: maximum collected URL-like hints
        """

        HTMLParser.__init__(self, convert_charrefs=True)
        self.max_hints = int(max_hints)
        self.hidden_depth = 0
        self.title_depth = 0
        self.text_chunks = []
        self.title_chunks = []
        self.url_hints = []

    def handle_starttag(self, tag, attrs):
        """
        Track hidden blocks, title nodes and URL-like attributes.

        :param str tag: HTML start tag
        :param list attrs: parsed attributes
        :return: None
        """

        normalized = str(tag or '').lower()

        if normalized in self.HIDDEN_TAGS:
            self.hidden_depth += 1

        if normalized == 'title':
            self.title_depth += 1

        for name, value in attrs or []:
            attr_name = str(name or '').lower()
            if attr_name in self.URL_ATTRS:
                self._append_hint(value)

    def handle_endtag(self, tag):
        """
        Leave hidden and title blocks.

        :param str tag: HTML end tag
        :return: None
        """

        normalized = str(tag or '').lower()

        if normalized in self.HIDDEN_TAGS and self.hidden_depth > 0:
            self.hidden_depth -= 1

        if normalized == 'title' and self.title_depth > 0:
            self.title_depth -= 1

    def handle_data(self, data):
        """
        Collect visible and title text chunks.

        :param str data: text node data
        :return: None
        """

        value = str(data or '')

        if self.title_depth > 0:
            self.title_chunks.append(value)

        if self.hidden_depth <= 0:
            self.text_chunks.append(value)

    def _append_hint(self, value):
        """
        Append a bounded URL-like hint.

        :param str value: candidate value
        :return: None
        """

        if len(self.url_hints) >= self.max_hints:
            return

        hint = ResponseBodyView.normalize_hint(value)
        if hint:
            self.url_hints.append(hint)

    def visible_text(self):
        """
        Return normalized visible text.

        :return: whitespace-normalized visible text
        :rtype: str
        """

        return ResponseBodyView.normalize_text(' '.join(self.text_chunks))

    def title(self):
        """
        Return normalized title text.

        :return: whitespace-normalized title text
        :rtype: str
        """

        return ResponseBodyView.normalize_text(' '.join(self.title_chunks))


class ResponseBodyView(object):
    """A bounded, dependency-free response body view for passive analysis."""

    MAX_BODY_BYTES = 512 * 1024
    MAX_TEXT_CHARS = 256 * 1024
    MAX_HINTS = 40
    MAX_JSON_KEYS = 40
    MAX_HINT_LENGTH = 512

    CONTENT_HTML = 'html'
    CONTENT_JSON = 'json'
    CONTENT_XML = 'xml'
    CONTENT_JAVASCRIPT = 'javascript'
    CONTENT_CSS = 'css'
    CONTENT_TEXT = 'text'
    CONTENT_BINARY = 'binary'
    CONTENT_EMPTY = 'empty'

    BINARY_CONTENT_TYPES = (
        'application/octet-stream',
        'application/pdf',
        'application/zip',
        'application/gzip',
        'audio/',
        'font/',
        'image/',
        'video/',
    )

    JAVASCRIPT_CONTENT_TYPES = (
        'application/javascript',
        'application/ecmascript',
        'text/javascript',
        'text/ecmascript',
    )

    JSON_CONTENT_TYPES = (
        'application/json',
        'text/json',
    )

    CSS_CONTENT_TYPES = (
        'text/css',
    )

    XML_CONTENT_TYPES = (
        'application/xml',
        'text/xml',
    )

    URL_LITERAL_RE = re.compile(
        r'''(?x)
        (?P<quote>["'])
        (?P<value>
            (?:https?:|wss?:)?//[^"'\s<>]+|
            /[a-z0-9._~!$&'()*+,;=:@%/-]{1,512}
        )
        (?P=quote)
        ''',
        flags=re.IGNORECASE,
    )
    HTML_TAG_RE = re.compile(r'<[^>]+>')
    MULTISPACE_RE = re.compile(r'\s+')
    XML_ROOT_RE = re.compile(r'<\s*([a-z_][\w:.-]*)\b', flags=re.IGNORECASE)

    def __init__(self, body='', content_type='', max_hints=None):
        """
        Create a bounded body view.

        :param str body: decoded response body
        :param str content_type: response Content-Type header
        :param int|None max_hints: maximum URL-like hints to expose
        """

        self.body = str(body or '')[:self.MAX_TEXT_CHARS]
        self.content_type = str(content_type or '').split(';', 1)[0].strip().lower()
        self.max_hints = self.MAX_HINTS if max_hints is None else int(max_hints)
        self._html_parser = None
        self._json_data = None
        self._json_loaded = False

    @classmethod
    def from_response(cls, response_object, max_body_bytes=None):
        """
        Build a body view from an HTTP response-like object.

        :param response_object: urllib3-like response object
        :param int|None max_body_bytes: maximum bytes decoded from response data
        :return: response body view
        :rtype: ResponseBodyView
        """

        limit = cls.MAX_BODY_BYTES if max_body_bytes is None else int(max_body_bytes)
        data = getattr(response_object, 'data', None)

        if isinstance(data, bytes):
            raw = data[:limit]
        elif data is None:
            raw = b''
        else:
            raw = str(data or '').encode('utf-8', errors='replace')[:limit]

        try:
            body = helper.decode(raw)
        except Exception:
            body = ''

        return cls(body=body, content_type=cls.get_header(response_object, 'Content-Type'))

    @staticmethod
    def get_header(response_object, name):
        """
        Return a response header using case-insensitive lookup.

        :param response_object: response-like object
        :param str name: header name
        :return: header value or empty string
        :rtype: str
        """

        headers = getattr(response_object, 'headers', None) or {}
        expected = str(name or '').lower()

        try:
            items = headers.items()
        except AttributeError:
            return ''

        for key, value in items:
            if str(key or '').lower() == expected:
                return str(value or '')

        return ''

    @classmethod
    def normalize_text(cls, value):
        """
        Normalize whitespace in bounded text.

        :param str value: input text
        :return: normalized text
        :rtype: str
        """

        return cls.MULTISPACE_RE.sub(' ', str(value or '')).strip()

    @classmethod
    def normalize_hint(cls, value):
        """
        Normalize a URL-like hint without resolving or validating it.

        :param str value: candidate hint
        :return: bounded hint or empty string
        :rtype: str
        """

        hint = str(value or '').strip()

        if not hint:
            return ''

        if hint.startswith(('javascript:', 'data:', 'mailto:', '#')):
            return ''

        return hint[:cls.MAX_HINT_LENGTH]

    @property
    def is_empty(self):
        """Return True when the bounded body is empty."""

        return len(self.body) <= 0

    @property
    def content_class(self):
        """
        Return a coarse content class for passive sniffers.

        :return: one of html/json/xml/javascript/css/text/binary/empty
        :rtype: str
        """

        if self.is_empty:
            return self.CONTENT_EMPTY

        if self._is_binary_content_type():
            return self.CONTENT_BINARY

        if self._is_content_type(self.JSON_CONTENT_TYPES) or self._looks_like_json():
            return self.CONTENT_JSON

        if self._is_content_type(self.JAVASCRIPT_CONTENT_TYPES):
            return self.CONTENT_JAVASCRIPT

        if self._is_content_type(self.CSS_CONTENT_TYPES):
            return self.CONTENT_CSS

        if self._is_content_type(self.XML_CONTENT_TYPES) or self._looks_like_xml():
            return self.CONTENT_XML

        if self.content_type == 'text/html' or self._looks_like_html():
            return self.CONTENT_HTML

        return self.CONTENT_TEXT

    @property
    def is_textual(self):
        """Return True for response classes that are safe to inspect as text."""

        return self.content_class not in (self.CONTENT_BINARY, self.CONTENT_EMPTY)

    @property
    def visible_text(self):
        """
        Return visible text for HTML or normalized plain text for other textual bodies.

        :return: bounded visible text
        :rtype: str
        """

        if not self.is_textual:
            return ''

        if self.content_class == self.CONTENT_HTML:
            return self._html().visible_text()

        if self.content_class in (self.CONTENT_JSON, self.CONTENT_XML, self.CONTENT_JAVASCRIPT, self.CONTENT_CSS):
            return ''

        return self.normalize_text(self.body)

    @property
    def title(self):
        """
        Return the HTML title when present.

        :return: title text or empty string
        :rtype: str
        """

        if self.content_class != self.CONTENT_HTML:
            return ''

        return self._html().title()

    @property
    def json_top_level_keys(self):
        """
        Return bounded top-level JSON object keys.

        :return: sorted top-level keys
        :rtype: list[str]
        """

        data = self._json()

        if not isinstance(data, dict):
            return []

        keys = []
        for key in data.keys():
            value = str(key or '').strip()
            if value:
                keys.append(value[:128])

        return sorted(keys)[:self.MAX_JSON_KEYS]

    @property
    def xml_root_tag(self):
        """
        Return the first XML-like root tag.

        :return: root tag or empty string
        :rtype: str
        """

        if self.content_class != self.CONTENT_XML:
            return ''

        value = re.sub(r'^\s*<\?xml[^>]*>\s*', '', self.body, flags=re.IGNORECASE)
        match = self.XML_ROOT_RE.search(value)

        if match is None:
            return ''

        return str(match.group(1) or '').lower()

    @property
    def url_hints(self):
        """
        Return bounded URL-like hints from HTML attributes and JS/string literals.

        :return: sorted unique URL-like hints
        :rtype: list[str]
        """

        hints = []

        if self.content_class == self.CONTENT_HTML:
            hints.extend(self._html().url_hints)

        if self.content_class in (self.CONTENT_HTML, self.CONTENT_JAVASCRIPT, self.CONTENT_TEXT):
            for match in self.URL_LITERAL_RE.finditer(self.body):
                hint = self.normalize_hint(match.group('value'))
                if hint:
                    hints.append(hint)
                if len(hints) >= self.max_hints:
                    break

        return sorted(set(hints))[:self.max_hints]

    def _html(self):
        """
        Return a cached HTML parser result.

        :return: parser result
        :rtype: _ResponseBodyHtmlParser
        """

        if self._html_parser is None:
            parser = _ResponseBodyHtmlParser(max_hints=self.max_hints)
            try:
                parser.feed(self.body)
                parser.close()
            except Exception:
                pass
            self._html_parser = parser

        return self._html_parser

    def _json(self):
        """
        Return parsed JSON data or None.

        :return: parsed JSON payload
        """

        if self._json_loaded is True:
            return self._json_data

        self._json_loaded = True
        try:
            self._json_data = json.loads(self.body)
        except Exception:
            self._json_data = None

        return self._json_data

    def _is_content_type(self, expected_types):
        """
        Return True when Content-Type matches an expected family.

        :param tuple[str] expected_types: expected media types
        :return: bool
        """

        if not self.content_type:
            return False

        if self.content_type.endswith('+json') and 'application/json' in expected_types:
            return True

        if self.content_type.endswith('+xml') and 'application/xml' in expected_types:
            return True

        return self.content_type in expected_types

    def _is_binary_content_type(self):
        """
        Return True for known binary content types.

        :return: bool
        """

        for content_type in self.BINARY_CONTENT_TYPES:
            if self.content_type.startswith(content_type):
                return True

        return False

    def _looks_like_html(self):
        """Return True when body has HTML-like structure."""

        value = self.body.lstrip().lower()
        return '<!doctype html' in value[:200] or '<html' in value[:500] or self.HTML_TAG_RE.search(value) is not None

    def _looks_like_json(self):
        """Return True when body looks like a JSON object or array."""

        value = self.body.lstrip()
        return value.startswith(('{', '['))

    def _looks_like_xml(self):
        """Return True when body looks like XML but not HTML."""

        value = self.body.lstrip().lower()
        return value.startswith('<?xml')
