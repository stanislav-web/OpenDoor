# -*- coding: utf-8 -*-

"""Small JavaScript cookie-gate response guards."""

import re
from html.parser import HTMLParser

from src.core import helper


class _VisibleTextExtractor(HTMLParser):
    """Extract visible text while ignoring script/style-like blocks."""

    HIDDEN_TAGS = {'script', 'style', 'noscript', 'template'}

    def __init__(self):
        """Initialize the bounded visible text collector."""

        HTMLParser.__init__(self, convert_charrefs=True)
        self._hidden_depth = 0
        self._chunks = []

    def handle_starttag(self, tag, _attrs):
        """Track hidden HTML blocks."""

        if str(tag or '').lower() in self.HIDDEN_TAGS:
            self._hidden_depth += 1

    def handle_endtag(self, tag):
        """Leave hidden HTML blocks."""

        if str(tag or '').lower() in self.HIDDEN_TAGS and self._hidden_depth > 0:
            self._hidden_depth -= 1

    def handle_data(self, data):
        """Collect visible text chunks only."""

        if self._hidden_depth <= 0:
            self._chunks.append(str(data or ''))

    def text(self):
        """Return normalized visible text."""

        return ' '.join(' '.join(self._chunks).split())


COOKIE_GATE_NAVIGATION_MARKERS = (
    'location.reload(',
    'window.location.reload(',
    'document.location.reload(',
    'location.href=',
    'window.location.href=',
    'document.location.href=',
    'location.replace(',
    'window.location.replace(',
    'document.location.replace(',
    'location.assign(',
    'window.location.assign(',
    'document.location.assign(',
    'window.location=',
    'document.location=',
)

KNOWN_COOKIE_GATE_MARKERS = (
    'beget=begetok',
    '__js_p_=',
)

USEFUL_HTML_CONTROLS_RE = re.compile(
    r'<\s*(?:form|input|textarea|select|button|table|main|article|section|pre|code)\b',
    flags=re.IGNORECASE,
)


def match_js_cookie_gate_response(response_object, response_data=None):
    """
    Match JavaScript cookie bootstrap pages emitted as 2xx responses.

    Some hosting frontends return a small 200 HTML page that only sets a
    browser cookie and reloads or navigates to the current URL. Browsers execute
    the script and then receive the real origin response, but raw scanners see
    the bootstrap page as a false positive success. Treat only script-only
    cookie gates as filtered scan noise.

    :param object response_object: raw response object
    :param tuple|None response_data: legacy classified response tuple
    :return: calibration-like metadata when the response should be filtered
    :rtype: dict|None
    """

    if is_js_cookie_gate_response(response_object, response_data) is not True:
        return None

    return {
        'calibration_score': 1.0,
        'calibration_reason': 'js-cookie-reload-challenge',
    }


def is_js_cookie_gate_response(response_object, response_data=None):
    """
    Return True when response body is a script-only JavaScript cookie gate.

    :param object response_object: raw response object
    :param tuple|None response_data: legacy classified response tuple
    :return: whether the response is bootstrap scan noise
    :rtype: bool
    """

    code = extract_response_code(response_object, response_data)
    if code is None or code < 200 or code >= 300:
        return False

    body = response_body_text(response_object)
    if not body:
        return False

    if len(body) > 2048:
        return False

    content_type = str(get_header_value(response_object, 'content-type') or '').lower()
    if content_type and 'html' not in content_type:
        return False

    lowered = body.lower()
    compact = re.sub(r'\s+', '', lowered)

    if 'document.cookie' not in compact:
        return False

    if any(marker in compact for marker in COOKIE_GATE_NAVIGATION_MARKERS) is not True:
        return False

    if has_useful_html_controls(lowered) is True:
        return False

    if visible_text_without_scripts(body):
        return False

    known_cookie_gate = any(marker in compact for marker in KNOWN_COOKIE_GATE_MARKERS)
    if known_cookie_gate is not True and is_script_only_layout(compact) is not True:
        return False

    return True


def is_script_only_layout(compact_body):
    """
    Return True for common script-only cookie-gate HTML layouts.

    :param str compact_body: lower-case whitespace-compacted body
    :return: whether body starts as a script-only bootstrap shell
    :rtype: bool
    """

    compact = str(compact_body or '')
    return compact.startswith((
        '<script',
        '<html><script',
        '<html><head><script',
        '<html><body><script',
        '<html><head></head><body><script',
    ))


def response_body_text(response_object):
    """
    Decode response body defensively for lightweight response guards.

    :param object response_object: raw response object
    :return: decoded response body
    :rtype: str
    """

    try:
        data = response_object.data
    except AttributeError:
        return ''

    if isinstance(data, bytes):
        try:
            return helper.decode(data)
        except (TypeError, UnicodeError):
            return ''

    try:
        return str(data or '')
    except (TypeError, UnicodeError):
        return ''


def extract_response_code(response, response_data=None):
    """
    Resolve numeric HTTP response code from response object or handled response data.

    :param object response: response-like object
    :param tuple|None response_data: legacy classified response tuple
    :return: int | None
    """

    try:
        return int(response.status)
    except (AttributeError, TypeError, ValueError):
        pass

    try:
        return int(response_data[3])
    except (IndexError, TypeError, ValueError):
        return None


def get_header_value(response, header_name):
    """
    Resolve response header value using case-insensitive lookup.

    :param object response: response-like object
    :param str header_name: header name
    :return: str | None
    """

    try:
        headers = response.headers
    except AttributeError:
        return None

    expected = str(header_name).lower()

    try:
        value = headers.get(header_name)
        if value is not None:
            return str(value)
    except AttributeError:
        pass

    try:
        value = headers.get(expected)
        if value is not None:
            return str(value)
    except AttributeError:
        pass

    try:
        for key, value in headers.items():
            if str(key).lower() == expected:
                return str(value)
    except AttributeError:
        return None

    return None


def has_useful_html_controls(body):
    """
    Return True when HTML contains user-facing controls or content containers.

    :param str body: decoded lower-case response body
    :return: whether the page looks like useful content
    :rtype: bool
    """

    return USEFUL_HTML_CONTROLS_RE.search(str(body or '')) is not None


def visible_text_without_scripts(body):
    """
    Extract visible text after removing script/style blocks and tags.

    :param str body: decoded response body
    :return: normalized visible text
    :rtype: str
    """

    parser = _VisibleTextExtractor()
    try:
        parser.feed(str(body or ''))
        parser.close()
    except Exception:
        value = re.sub(r'<[^>]+>', ' ', str(body or ''))
        value = re.sub(r'\s+', ' ', value)
        return value.strip()

    return parser.text()
