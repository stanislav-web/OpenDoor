# -*- coding: utf-8 -*-

"""Passive client-exposed endpoint response sniffer."""

import re

from src.lib.browser.response_body_view import ResponseBodyView
from .provider import ResponsePluginProvider


class EndpointResponsePlugin(ResponsePluginProvider):
    """Detect client-exposed API endpoints without active validation."""

    DESCRIPTION = 'Endpoint (detect client-exposed WebSocket, SSE and AJAX endpoints)'
    RESPONSE_INDEX = 'endpoint'
    MAX_FINDINGS = 8
    DEFAULT_STATUSES = (200, 201, 202, 203, 204, 205, 206, 207, 208)

    STATIC_EXTENSIONS = (
        '.avif', '.bmp', '.css', '.eot', '.gif', '.gz', '.ico', '.jpeg', '.jpg',
        '.js', '.json', '.map', '.mp3', '.mp4', '.otf', '.pdf', '.png', '.svg',
        '.tar', '.ttf', '.wasm', '.webm', '.webp', '.woff', '.woff2', '.zip',
    )
    UNSAFE_SCHEMES = (
        'about:', 'blob:', 'data:', 'file:', 'javascript:', 'mailto:', 'tel:',
    )

    WEBSOCKET_CONSTRUCTOR_RE = re.compile(
        r'''(?is)\bnew\s+WebSocket\s*\(\s*(?P<quote>["'])(?P<endpoint>[^"'\s<>]{1,512})(?P=quote)'''
    )
    WEBSOCKET_ASSIGNMENT_RE = re.compile(
        r'''(?is)\b(?:ws|wss|websocket|socket)[\w$-]{0,40}\s*[:=]\s*(?P<quote>["'])(?P<endpoint>wss?://[^"'\s<>]{1,512})(?P=quote)'''
    )
    EVENTSOURCE_CONSTRUCTOR_RE = re.compile(
        r'''(?is)\bnew\s+EventSource\s*\(\s*(?P<quote>["'])(?P<endpoint>[^"'\s<>]{1,512})(?P=quote)'''
    )
    SOCKET_IO_CALL_RE = re.compile(
        r'''(?is)\b(?:io|io\s*\.\s*connect)\s*\(\s*(?P<quote>["'])(?P<endpoint>(?:/|\./|\.\./)[^"'\s<>]{1,512})(?P=quote)'''
    )
    SOCKET_IO_PATH_RE = re.compile(
        r'''(?is)\b(?:io|io\s*\.\s*connect)\s*\(.{0,800}?\bpath\s*:\s*(?P<quote>["'])(?P<endpoint>(?:/|\./|\.\./)[^"'\s<>]{1,512})(?P=quote)'''
    )
    SOCKET_IO_TRANSPORT_RE = re.compile(
        r'''(?is)(?P<quote>["'])(?P<endpoint>/socket\.io/\?EIO=\d+&transport=(?:websocket|polling)[^"'\s<>]{0,256})(?P=quote)'''
    )
    FETCH_RE = re.compile(
        r'''(?is)(?:\b|\.)fetch\s*\(\s*(?P<quote>["'])(?P<endpoint>[^"'\s<>]{1,512})(?P=quote)'''
    )
    XHR_OPEN_RE = re.compile(
        r'''(?is)\.open\s*\(\s*(?P<method_quote>["'])(?P<method>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)(?P=method_quote)\s*,\s*(?P<quote>["'])(?P<endpoint>[^"'\s<>]{1,512})(?P=quote)'''
    )
    AXIOS_RE = re.compile(
        r'''(?is)\baxios\s*\.\s*(?P<method>get|post|put|patch|delete|head|options)\s*\(\s*(?P<quote>["'])(?P<endpoint>[^"'\s<>]{1,512})(?P=quote)'''
    )
    JQUERY_AJAX_URL_RE = re.compile(
        r'''(?is)\$\s*\.\s*ajax\s*\(\s*\{.{0,800}?\burl\s*:\s*(?P<quote>["'])(?P<endpoint>[^"'\s<>]{1,512})(?P=quote)'''
    )
    JQUERY_AJAX_METHOD_RE = re.compile(
        r'''(?is)\b(?:method|type)\s*:\s*(?P<quote>["'])(?P<method>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)(?P=quote)'''
    )

    def __init__(self, _void):
        """
        ResponsePluginProvider constructor.

        :param mixed _void: optional plugin value, unused
        """

        ResponsePluginProvider.__init__(self)

    @classmethod
    def process(cls, response):
        """
        Detect client-exposed endpoint references in a response.

        :param response: HTTP response-like object
        :return: endpoint bucket name when endpoint references are detected
        :rtype: str|None
        """

        if cls._is_supported_status(response) is not True:
            return None

        detection = cls.detect_response(response)
        if detection is None:
            return None

        try:
            setattr(response, 'opendoor_endpoint_detection', detection)
        except (AttributeError, TypeError):
            pass

        return cls.RESPONSE_INDEX

    @classmethod
    def detect_response(cls, response):
        """
        Detect endpoint references from a response object.

        :param response: HTTP response-like object
        :return: detection metadata or None
        :rtype: dict|None
        """

        view = ResponseBodyView.from_response(response)
        findings = []

        if cls._is_event_stream_response(view):
            findings.append(cls._finding(
                endpoint='(current response)',
                endpoint_type='event_stream',
                source='content_type',
                confidence=95,
                method='GET',
            ))

        if cls._is_inspectable_view(view) is not True:
            return cls._build_detection(findings)

        body = view.body
        for matcher, endpoint_type, source, default_method, confidence in cls._pattern_specs():
            for match in matcher.finditer(body):
                method = cls._match_method(match, default_method)
                endpoint = cls._normalize_endpoint(match.group('endpoint'), endpoint_type=endpoint_type)
                if not endpoint:
                    continue
                findings.append(cls._finding(
                    endpoint=endpoint,
                    endpoint_type=endpoint_type,
                    source=source,
                    confidence=confidence,
                    method=method,
                ))
                if len(findings) >= cls.MAX_FINDINGS:
                    return cls._build_detection(findings)

        for match in cls.JQUERY_AJAX_URL_RE.finditer(body):
            endpoint = cls._normalize_endpoint(match.group('endpoint'), endpoint_type='ajax')
            if not endpoint:
                continue
            window = match.group(0)
            method_match = cls.JQUERY_AJAX_METHOD_RE.search(window)
            findings.append(cls._finding(
                endpoint=endpoint,
                endpoint_type='ajax',
                source='jquery_ajax',
                confidence=88,
                method=cls._match_method(method_match, None),
            ))
            if len(findings) >= cls.MAX_FINDINGS:
                return cls._build_detection(findings)

        return cls._build_detection(findings)

    @classmethod
    def detect(cls, text, content_type='text/html'):
        """
        Detect endpoint references from raw text.

        :param str text: response body text
        :param str content_type: response content type
        :return: detection metadata or None
        :rtype: dict|None
        """

        return cls.detect_response(type('Response', (), {
            'status': 200,
            'data': str(text or '').encode('utf-8'),
            'headers': {'Content-Type': content_type},
        })())

    @classmethod
    def _pattern_specs(cls):
        """
        Return deterministic endpoint pattern specs.

        :return: tuple of pattern specs
        :rtype: tuple
        """

        return (
            (cls.WEBSOCKET_CONSTRUCTOR_RE, 'websocket', 'websocket_constructor', None, 95),
            (cls.WEBSOCKET_ASSIGNMENT_RE, 'websocket', 'websocket_url_assignment', None, 82),
            (cls.SOCKET_IO_CALL_RE, 'websocket', 'socket_io_call', None, 92),
            (cls.SOCKET_IO_PATH_RE, 'websocket', 'socket_io_path', None, 92),
            (cls.SOCKET_IO_TRANSPORT_RE, 'websocket', 'socket_io_transport', None, 90),
            (cls.EVENTSOURCE_CONSTRUCTOR_RE, 'sse', 'eventsource_constructor', 'GET', 95),
            (cls.FETCH_RE, 'ajax', 'fetch_call', None, 90),
            (cls.XHR_OPEN_RE, 'ajax', 'xhr_open_call', None, 90),
            (cls.AXIOS_RE, 'ajax', 'axios_call', None, 90),
        )

    @classmethod
    def _build_detection(cls, findings):
        """
        Build bounded detection metadata from endpoint findings.

        :param list findings: raw finding dictionaries
        :return: detection metadata or None
        :rtype: dict|None
        """

        endpoints = []
        seen = set()

        for finding in findings or []:
            if not isinstance(finding, dict):
                continue
            key = (finding.get('type'), finding.get('method'), finding.get('endpoint'))
            if key in seen:
                continue
            seen.add(key)
            endpoints.append(finding)
            if len(endpoints) >= cls.MAX_FINDINGS:
                break

        if len(endpoints) <= 0:
            return None

        types = []
        for endpoint in endpoints:
            endpoint_type = endpoint.get('type')
            if endpoint_type and endpoint_type not in types:
                types.append(endpoint_type)

        confidence = max([int(endpoint.get('confidence', 0) or 0) for endpoint in endpoints])
        primary_type = endpoints[0].get('type') or 'endpoint'

        return {
            'type': primary_type,
            'confidence': confidence,
            'count': len(endpoints),
            'types': types,
            'endpoints': endpoints,
        }

    @classmethod
    def _finding(cls, endpoint, endpoint_type, source, confidence, method=None):
        """
        Build one bounded endpoint finding dictionary.

        :param str endpoint: endpoint reference
        :param str endpoint_type: websocket, sse, ajax or event_stream
        :param str source: source signal name
        :param int confidence: confidence score
        :param str|None method: HTTP method when known
        :return: finding dictionary
        :rtype: dict
        """

        finding = {
            'type': str(endpoint_type),
            'endpoint': str(endpoint)[:ResponseBodyView.MAX_HINT_LENGTH],
            'source': str(source),
            'confidence': int(confidence),
        }
        if method:
            finding['method'] = str(method).upper()
        return finding

    @classmethod
    def _is_supported_status(cls, response):
        """
        Return True for success-like responses only.

        :param response: response-like object
        :return: whether response status is supported
        :rtype: bool
        """

        return cls._is_response_status_in(response, cls.DEFAULT_STATUSES)

    @classmethod
    def _is_event_stream_response(cls, view):
        """
        Return True when the current response is an SSE stream endpoint.

        :param ResponseBodyView view: bounded response view
        :return: whether response is text/event-stream
        :rtype: bool
        """

        return view.content_type == 'text/event-stream'

    @classmethod
    def _is_inspectable_view(cls, view):
        """
        Return True for content classes that may carry client endpoint calls.

        :param ResponseBodyView view: bounded response view
        :return: whether body should be inspected
        :rtype: bool
        """

        return view.content_class in (
            ResponseBodyView.CONTENT_HTML,
            ResponseBodyView.CONTENT_JAVASCRIPT,
            ResponseBodyView.CONTENT_TEXT,
        )

    @classmethod
    def _match_method(cls, match, default=None):
        """
        Extract an HTTP method from a regex match when available.

        :param re.Match|None match: regex match
        :param str|None default: fallback method
        :return: HTTP method or None
        :rtype: str|None
        """

        if match is None:
            return default.upper() if default else None
        try:
            value = match.group('method')
        except (IndexError, AttributeError):
            value = default
        if not value:
            return None
        return str(value).upper()

    @classmethod
    def _normalize_endpoint(cls, value, endpoint_type='ajax'):
        """
        Normalize and filter one endpoint candidate.

        :param str value: raw candidate endpoint
        :param str endpoint_type: endpoint family
        :return: normalized endpoint or empty string
        :rtype: str
        """

        endpoint = ResponseBodyView.normalize_hint(value).strip()
        if not endpoint:
            return ''

        lowered = endpoint.lower()
        if lowered.startswith(cls.UNSAFE_SCHEMES):
            return ''
        if any(token in endpoint for token in ('${', '<%', '{{', '}}')):
            return ''
        if any(char.isspace() for char in endpoint):
            return ''
        if endpoint.startswith(('#', '?')):
            return ''

        if endpoint_type == 'websocket':
            if lowered.startswith(('ws://', 'wss://', '/', './', '../')):
                return endpoint[:ResponseBodyView.MAX_HINT_LENGTH]
            return ''

        if lowered.startswith(('http://', 'https://', '//', 'ws://', 'wss://')):
            return ''

        if not endpoint.startswith(('/', './', '../')) and '/' not in endpoint:
            return ''

        clean_path = endpoint.split('?', 1)[0].split('#', 1)[0].rstrip('/').lower()
        if any(clean_path.endswith(extension) for extension in cls.STATIC_EXTENSIONS):
            return ''

        return endpoint[:ResponseBodyView.MAX_HINT_LENGTH]
