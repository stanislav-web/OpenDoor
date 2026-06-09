# -*- coding: utf-8 -*-

import json
import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response import endpoint
from src.core.http.plugins.response.endpoint import EndpointResponsePlugin


class TestEndpointResponsePlugin(unittest.TestCase):
    """EndpointResponsePlugin test cases."""

    @staticmethod
    def make_response(status=200, body=b'', headers=None):
        """
        Build a urllib3 response for plugin tests.

        :param int status: HTTP status code
        :param bytes body: response body
        :param dict|None headers: response headers
        :return: HTTP response
        :rtype: HTTPResponse
        """

        return HTTPResponse(status=status, body=body, headers=headers or {'Content-Type': 'text/html'})

    def assert_endpoint_detection(self, body, expected_type, headers=None):
        """
        Assert that response body is classified as endpoint.

        :param str body: response body
        :param str expected_type: expected primary endpoint type
        :param dict|None headers: optional response headers
        :return: endpoint detection metadata
        :rtype: dict
        """

        plugin = EndpointResponsePlugin(None)
        response = self.make_response(body=body.encode('utf-8'), headers=headers)

        self.assertEqual(plugin.process(response), 'endpoint')
        detection = getattr(response, 'opendoor_endpoint_detection')
        self.assertEqual(detection['type'], expected_type)
        self.assertGreaterEqual(detection['confidence'], 80)
        self.assertGreaterEqual(detection['count'], 1)
        self.assertIn(expected_type, detection['types'])
        self.assertNotIn(body, json.dumps(detection, sort_keys=True))
        return detection

    def test_response_package_exports_endpoint_plugin_alias(self):
        """Response plugin loader should be able to resolve the endpoint alias."""

        self.assertIs(endpoint, EndpointResponsePlugin)

    def test_detects_websocket_constructor_without_active_connection(self):
        """Should detect explicit WebSocket constructor endpoints only passively."""

        detection = self.assert_endpoint_detection('const ws = new WebSocket("/ws/live");', 'websocket')
        endpoint_finding = detection['endpoints'][0]

        self.assertEqual(endpoint_finding['type'], 'websocket')
        self.assertEqual(endpoint_finding['endpoint'], '/ws/live')
        self.assertEqual(endpoint_finding['source'], 'websocket_constructor')
        self.assertEqual(endpoint_finding['confidence'], 95)

    def test_detects_websocket_url_assignment_when_variable_name_is_specific(self):
        """Should detect stable websocket URL assignments without arbitrary URL scanning."""

        detection = self.assert_endpoint_detection('window.websocketUrl = "wss://api.example.com/socket";', 'websocket')

        self.assertEqual(detection['endpoints'][0]['endpoint'], 'wss://api.example.com/socket')
        self.assertEqual(detection['endpoints'][0]['source'], 'websocket_url_assignment')


    def test_detects_socket_io_endpoint_patterns_as_websocket(self):
        """Should detect Socket.IO client endpoints as websocket-family endpoints."""

        body = '''
            const socket = io('/socket.io');
            const socket2 = io.connect('/realtime');
            const socket3 = io('https://api.example.com', { path: '/custom-socket.io' });
            const socket4 = io({ path: '/events/socket.io' });
            const engineIo = '/socket.io/?EIO=4&transport=websocket';
            const engineIoPolling = '/socket.io/?EIO=4&transport=polling';
        '''

        detection = self.assert_endpoint_detection(body, 'websocket')
        endpoints = {(item.get('source'), item.get('endpoint')) for item in detection['endpoints']}

        self.assertIn(('socket_io_call', '/socket.io'), endpoints)
        self.assertIn(('socket_io_call', '/realtime'), endpoints)
        self.assertIn(('socket_io_path', '/custom-socket.io'), endpoints)
        self.assertIn(('socket_io_path', '/events/socket.io'), endpoints)
        self.assertIn(('socket_io_transport', '/socket.io/?EIO=4&transport=websocket'), endpoints)
        self.assertIn(('socket_io_transport', '/socket.io/?EIO=4&transport=polling'), endpoints)

    def test_rejects_socket_io_false_positives(self):
        """Should avoid Socket.IO docs, CDN and static-asset false positives."""

        negatives = [
            '<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>',
            'Install socket.io from npm before using the client.',
            'const docs = "Socket.IO powers realtime features";',
            'const staticAsset = "/socket.io.js";',
            'const arbitrary = "/socket.io";',
            'const cdn = "//cdn.socket.io/socket.io.js";',
            'const transportOnly = "/socket.io/?transport=websocket";',
            'io("https://api.example.com")',
            'io({ path: "https://api.example.com/socket.io" })',
        ]

        for body in negatives:
            with self.subTest(body=body):
                self.assertIsNone(EndpointResponsePlugin.detect(body))

    def test_detects_sse_constructor_and_event_stream_response(self):
        """Should detect EventSource references and event-stream responses."""

        detection = self.assert_endpoint_detection('const stream = new EventSource("/events");', 'sse')
        self.assertEqual(detection['endpoints'][0]['method'], 'GET')
        self.assertEqual(detection['endpoints'][0]['source'], 'eventsource_constructor')

        response = self.make_response(headers={'Content-Type': 'text/event-stream'}, body=b'data: ok\n\n')
        self.assertEqual(EndpointResponsePlugin(None).process(response), 'endpoint')
        event_stream = response.opendoor_endpoint_detection
        self.assertEqual(event_stream['type'], 'event_stream')
        self.assertEqual(event_stream['endpoints'][0]['endpoint'], '(current response)')
        self.assertEqual(event_stream['endpoints'][0]['source'], 'content_type')

    def test_detects_ajax_call_patterns(self):
        """Should detect explicit browser client API call targets."""

        body = '''
            fetch('/api/users');
            xhr.open('POST', '/api/login');
            axios.patch('/api/profile');
            $.ajax({ method: 'DELETE', url: '/api/session' });
        '''

        detection = self.assert_endpoint_detection(body, 'ajax')
        endpoints = {(item.get('source'), item.get('method'), item.get('endpoint')) for item in detection['endpoints']}

        self.assertIn(('fetch_call', None, '/api/users'), endpoints)
        self.assertIn(('xhr_open_call', 'POST', '/api/login'), endpoints)
        self.assertIn(('axios_call', 'PATCH', '/api/profile'), endpoints)
        self.assertIn(('jquery_ajax', 'DELETE', '/api/session'), endpoints)

    def test_deduplicates_and_bounds_endpoint_findings(self):
        """Should dedupe repeated endpoints and cap findings per response."""

        body = '\n'.join([
            "fetch('/api/repeated');",
            "fetch('/api/repeated');",
        ] + [
            "fetch('/api/item{0}');".format(index)
            for index in range(20)
        ])

        detection = self.assert_endpoint_detection(body, 'ajax')
        self.assertLessEqual(detection['count'], EndpointResponsePlugin.MAX_FINDINGS)
        self.assertEqual(
            len({(item.get('type'), item.get('method'), item.get('endpoint')) for item in detection['endpoints']}),
            detection['count'],
        )

    def test_rejects_common_false_positive_url_literals(self):
        """Should not treat arbitrary URLs and static assets as client API endpoints."""

        negatives = [
            '<a href="/api/users">API documentation link</a>',
            '<script src="/assets/app.js"></script>',
            'const docs = "wss://example.com/socket";',
            'const url = "https://api.example.com/users";',
            'fetch("https://third-party.example/api")',
            'fetch("/assets/app.js")',
            'fetch("/images/logo.png")',
            'fetch("?page=1")',
            'fetch("/api/${id}")',
            'fetch("javascript:alert(1)")',
            'fetch("data:text/plain,hello")',
            'fetch("mailto:admin@example.com")',
            'fetch("#fragment")',
            'fetch("health")',
        ]

        for body in negatives:
            with self.subTest(body=body):
                self.assertIsNone(EndpointResponsePlugin.detect(body))

    def test_ignores_binary_json_xml_and_non_success_responses(self):
        """Should avoid broad endpoint extraction from unsupported response families."""

        plugin = EndpointResponsePlugin(None)
        cases = [
            self.make_response(status=404, body=b'fetch("/api/not-found")'),
            self.make_response(body=b'fetch("/api/from-png")', headers={'Content-Type': 'image/png'}),
            self.make_response(body=b'{"url":"/api/users"}', headers={'Content-Type': 'application/json'}),
            self.make_response(body=b'<root>/api/users</root>', headers={'Content-Type': 'application/xml'}),
        ]

        for response in cases:
            with self.subTest(headers=response.headers, status=response.status):
                self.assertIsNone(plugin.process(response))
                self.assertFalse(hasattr(response, 'opendoor_endpoint_detection'))

    def test_handles_malformed_and_non_mutable_response_objects(self):
        """Should be defensive for malformed response-like objects."""

        class BadStatus:
            status = object()
            data = b'fetch("/api/users")'
            headers = {'Content-Type': 'text/html'}

        class FrozenResponse:
            __slots__ = ('status', 'data', 'headers')

            def __init__(self):
                self.status = 200
                self.data = b'fetch("/api/users")'
                self.headers = {'Content-Type': 'text/html'}

        self.assertIsNone(EndpointResponsePlugin(None).process(BadStatus()))
        self.assertEqual(EndpointResponsePlugin(None).process(FrozenResponse()), 'endpoint')


    def test_covers_endpoint_helper_edge_branches(self):
        """Helper branches should remain deterministic and fully covered."""

        self.assertEqual(EndpointResponsePlugin._match_method(None, 'post'), 'POST')
        self.assertIsNone(EndpointResponsePlugin._match_method(object(), None))

        mixed = EndpointResponsePlugin._build_detection(
            [object()] + [
                {
                    'type': 'ajax',
                    'endpoint': '/api/item{0}'.format(index),
                    'source': 'fetch_call',
                    'confidence': 90,
                }
                for index in range(EndpointResponsePlugin.MAX_FINDINGS + 3)
            ]
        )
        self.assertEqual(mixed['count'], EndpointResponsePlugin.MAX_FINDINGS)

        jquery_static = '$.ajax({ url: "/assets/app.js" });'
        self.assertIsNone(EndpointResponsePlugin.detect(jquery_static))

        jquery_many = '\n'.join([
            '$.ajax({{ url: "/api/jquery{0}" }});'.format(index)
            for index in range(EndpointResponsePlugin.MAX_FINDINGS + 3)
        ])
        jquery_detection = EndpointResponsePlugin.detect(jquery_many)
        self.assertEqual(jquery_detection['count'], EndpointResponsePlugin.MAX_FINDINGS)

        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('blob:https://example.com/id', 'ajax'), '')
        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('api/socket', 'websocket'), '')

    def test_normalize_endpoint_filters_edge_values(self):
        """Endpoint normalization should reject unsafe or noisy candidates."""

        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('/api/users', 'ajax'), '/api/users')
        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('./api/users', 'ajax'), './api/users')
        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('../api/users', 'ajax'), '../api/users')
        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('api/users', 'ajax'), 'api/users')
        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('wss://example.com/ws', 'websocket'), 'wss://example.com/ws')
        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('https://example.com/api', 'ajax'), '')
        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('/assets/app.css', 'ajax'), '')
        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('/api/{{ id }}', 'ajax'), '')
        self.assertEqual(EndpointResponsePlugin._normalize_endpoint('/api/users with spaces', 'ajax'), '')


if __name__ == '__main__':
    unittest.main()
