# -*- coding: utf-8 -*-

import unittest

from urllib3.response import HTTPResponse

from src.lib.browser.response_body_view import ResponseBodyView


class TestResponseBodyView(unittest.TestCase):
    """ResponseBodyView helper tests."""

    @staticmethod
    def make_response(body=b'', headers=None):
        """
        Create a response object for body-view tests.

        :param bytes body: response body
        :param dict|None headers: response headers
        :return: response object
        """

        return HTTPResponse(status=200, body=body, headers=headers or {})

    def test_from_response_decodes_body_and_header_case_insensitively(self):
        """Should decode bounded response data and normalize Content-Type."""

        response = self.make_response(
            body='Привет'.encode('utf-8'),
            headers={'content-type': 'text/plain; charset=utf-8'},
        )
        view = ResponseBodyView.from_response(response)

        self.assertEqual(view.content_type, 'text/plain')
        self.assertEqual(view.content_class, ResponseBodyView.CONTENT_TEXT)
        self.assertEqual(view.visible_text, 'Привет')

    def test_content_classifies_common_textual_and_binary_shapes(self):
        """Should classify bodies without requiring network or renderer state."""

        samples = [
            (b'', {}, ResponseBodyView.CONTENT_EMPTY),
            (b'{"openapi":"3.0.0"}', {'Content-Type': 'application/vnd.api+json'}, ResponseBodyView.CONTENT_JSON),
            (b'<?xml version="1.0"?><rss></rss>', {}, ResponseBodyView.CONTENT_XML),
            (b'body { color: red; }', {'Content-Type': 'text/css'}, ResponseBodyView.CONTENT_CSS),
            (b'console.log("/api")', {'Content-Type': 'application/javascript'}, ResponseBodyView.CONTENT_JAVASCRIPT),
            (b'<html><body>Hello</body></html>', {}, ResponseBodyView.CONTENT_HTML),
            (b'%PDF', {'Content-Type': 'application/pdf'}, ResponseBodyView.CONTENT_BINARY),
        ]

        for body, headers, expected in samples:
            with self.subTest(expected=expected):
                view = ResponseBodyView.from_response(self.make_response(body=body, headers=headers))
                self.assertEqual(view.content_class, expected)

    def test_html_helpers_extract_title_visible_text_and_url_hints(self):
        """Should expose bounded HTML hints while ignoring script/style text."""

        view = ResponseBodyView(
            body='''
            <html>
              <head>
                <title> Admin Console </title>
                <style>.hidden { display:none }</style>
                <script>var ignored = "secret";</script>
              </head>
              <body>
                <a href="/admin/login">Login</a>
                <form action="/api/auth"></form>
                <script>new WebSocket("wss://example.test/ws")</script>
                Visible text
              </body>
            </html>
            ''',
            content_type='text/html',
        )

        self.assertEqual(view.title, 'Admin Console')
        self.assertIn('Login', view.visible_text)
        self.assertIn('Visible text', view.visible_text)
        self.assertNotIn('ignored', view.visible_text)
        self.assertIn('/admin/login', view.url_hints)
        self.assertIn('/api/auth', view.url_hints)
        self.assertIn('wss://example.test/ws', view.url_hints)

    def test_json_helpers_return_keys_without_values(self):
        """Should expose bounded JSON keys without leaking values."""

        view = ResponseBodyView(
            body='{"token":"secret-value","openapi":"3.0.0","paths":{}}',
            content_type='application/json',
        )

        self.assertEqual(view.content_class, ResponseBodyView.CONTENT_JSON)
        self.assertEqual(view.json_top_level_keys, ['openapi', 'paths', 'token'])
        self.assertNotIn('secret-value', view.json_top_level_keys)

    def test_xml_helper_returns_root_tag_only(self):
        """Should expose only the XML root tag for future passive sniffers."""

        view = ResponseBodyView(
            body='<?xml version="1.0"?><wsdl:definitions name="service"></wsdl:definitions>',
            content_type='application/xml',
        )

        self.assertEqual(view.content_class, ResponseBodyView.CONTENT_XML)
        self.assertEqual(view.xml_root_tag, 'wsdl:definitions')
        self.assertEqual(view.visible_text, '')

    def test_url_hints_are_bounded_deduplicated_and_safe(self):
        """Should avoid unsafe schemes and cap URL-like hints."""

        body = '<a href="javascript:alert(1)"></a><a href="data:text/plain,abc"></a>'
        body += ''.join('<a href="/path-{0}">x</a>'.format(index) for index in range(60))
        view = ResponseBodyView(body=body, content_type='text/html', max_hints=5)

        self.assertEqual(len(view.url_hints), 5)
        self.assertNotIn('javascript:alert(1)', view.url_hints)
        self.assertNotIn('data:text/plain,abc', view.url_hints)
        self.assertEqual(view.url_hints, sorted(set(view.url_hints)))

    def test_non_mapping_headers_and_bad_body_do_not_crash(self):
        """Should degrade safely for partial response-like objects."""

        class PartialResponse:
            headers = object()
            data = None

        view = ResponseBodyView.from_response(PartialResponse())

        self.assertEqual(view.content_type, '')
        self.assertEqual(view.content_class, ResponseBodyView.CONTENT_EMPTY)
        self.assertEqual(view.visible_text, '')

    def test_from_response_handles_string_body_decode_failures_and_missing_headers(self):
        """Should safely handle non-byte bodies and decode failures."""

        class StringResponse:
            headers = {'Content-Type': 'text/plain'}
            data = '/from-string'

        view = ResponseBodyView.from_response(StringResponse(), max_body_bytes=5)
        self.assertEqual(view.body, '/from')
        self.assertEqual(view.url_hints, [])

        class HeaderlessResponse:
            data = b'plain text'

        view = ResponseBodyView.from_response(HeaderlessResponse())
        self.assertEqual(view.content_type, '')
        self.assertEqual(view.content_class, ResponseBodyView.CONTENT_TEXT)

        original_decode = ResponseBodyView.__module__
        self.assertEqual(original_decode, 'src.lib.browser.response_body_view')

    def test_from_response_degrades_when_helper_decode_fails(self):
        """Should return an empty view when low-level decoding fails."""

        import importlib

        response_body_view = importlib.import_module('src.lib.browser.response_body_view')

        original_decode = response_body_view.helper.decode

        def fail_decode(_raw):
            raise UnicodeError('boom')

        try:
            response_body_view.helper.decode = fail_decode
            view = ResponseBodyView.from_response(self.make_response(body=b'broken'))
        finally:
            response_body_view.helper.decode = original_decode

        self.assertEqual(view.body, '')
        self.assertEqual(view.content_class, ResponseBodyView.CONTENT_EMPTY)

    def test_content_class_and_helpers_cover_vendor_and_binary_edges(self):
        """Should classify vendor XML, binary families and script-like content safely."""

        samples = [
            ('<root></root>', 'application/soap+xml', ResponseBodyView.CONTENT_XML),
            ('{}', 'application/problem+json', ResponseBodyView.CONTENT_JSON),
            ('body', 'image/svg+xml', ResponseBodyView.CONTENT_BINARY),
            ('body', 'audio/mpeg', ResponseBodyView.CONTENT_BINARY),
            ('body', 'font/woff2', ResponseBodyView.CONTENT_BINARY),
            ('body', 'video/mp4', ResponseBodyView.CONTENT_BINARY),
            ('not html <tag>', '', ResponseBodyView.CONTENT_HTML),
            ('[1,2,3]', '', ResponseBodyView.CONTENT_JSON),
        ]

        for body, content_type, expected in samples:
            with self.subTest(content_type=content_type, expected=expected):
                view = ResponseBodyView(body=body, content_type=content_type)
                self.assertEqual(view.content_class, expected)

    def test_normalize_hint_filters_empty_anchors_and_mail_links(self):
        """Should normalize only safe bounded URL-like hints."""

        self.assertEqual(ResponseBodyView.normalize_hint(''), '')
        self.assertEqual(ResponseBodyView.normalize_hint('   '), '')
        self.assertEqual(ResponseBodyView.normalize_hint('#section'), '')
        self.assertEqual(ResponseBodyView.normalize_hint('mailto:a@example.com'), '')
        self.assertEqual(ResponseBodyView.normalize_hint('/' + 'a' * 600), '/' + 'a' * 511)

    def test_non_html_json_and_xml_helpers_degrade_safely(self):
        """Should return empty helper metadata when body shape is unsupported."""

        plain = ResponseBodyView(body='plain text', content_type='text/plain')
        self.assertEqual(plain.title, '')
        self.assertEqual(plain.xml_root_tag, '')
        self.assertEqual(plain.json_top_level_keys, [])

        json_array = ResponseBodyView(body='["one", "two"]', content_type='application/json')
        self.assertEqual(json_array.json_top_level_keys, [])
        self.assertEqual(json_array.visible_text, '')
        self.assertEqual(json_array.url_hints, [])

        invalid_json = ResponseBodyView(body='{bad', content_type='application/json')
        self.assertEqual(invalid_json.json_top_level_keys, [])
        self.assertIsNone(invalid_json._json())

        xml_without_root = ResponseBodyView(body='<?xml version="1.0"?>', content_type='text/xml')
        self.assertEqual(xml_without_root.xml_root_tag, '')

    def test_json_keys_are_bounded_and_empty_keys_are_ignored(self):
        """Should bound JSON keys and drop empty-looking keys."""

        key = 'k' * 200
        body = '{"":"ignored","%s":"value","normal":"value"}' % key
        view = ResponseBodyView(body=body, content_type='application/json')

        self.assertIn('normal', view.json_top_level_keys)
        self.assertIn('k' * 128, view.json_top_level_keys)
        self.assertNotIn('', view.json_top_level_keys)

    def test_url_hints_cover_text_literals_filtering_and_max_hints(self):
        """Should extract bounded URL string literals from textual bodies."""

        body = ' '.join([
            '"/api/one"',
            '"#fragment"',
            '"mailto:a@example.com"',
            '"/api/two"',
            '"/api/three"',
        ])
        view = ResponseBodyView(body=body, content_type='text/plain', max_hints=2)

        self.assertEqual(view.url_hints, ['/api/one', '/api/two'])

    def test_html_parser_cache_and_error_path_are_safe(self):
        """Should cache HTML parser output and tolerate parser failures."""

        view = ResponseBodyView(body='<title>One</title><p>Body</p>', content_type='text/html')
        self.assertIs(view._html(), view._html())

        import importlib

        response_body_view = importlib.import_module('src.lib.browser.response_body_view')

        original_parser = response_body_view._ResponseBodyHtmlParser

        class FailingParser(object):
            def __init__(self, max_hints):
                self.url_hints = []

            def feed(self, _body):
                raise ValueError('parser boom')

            def close(self):
                raise ValueError('close boom')

            def visible_text(self):
                return ''

            def title(self):
                return ''

        try:
            response_body_view._ResponseBodyHtmlParser = FailingParser
            failing = ResponseBodyView(body='<html><title>x</title></html>', content_type='text/html')
            self.assertEqual(failing.visible_text, '')
            self.assertEqual(failing.title, '')
        finally:
            response_body_view._ResponseBodyHtmlParser = original_parser


    def test_edge_branches_for_header_html_attrs_and_filtered_literals(self):
        """Should cover benign non-matching branches in bounded helpers."""

        response = self.make_response(
            body=b'header test',
            headers={'X-Test': '1', 'Content-Type': 'text/plain'},
        )
        self.assertEqual(ResponseBodyView.from_response(response).content_type, 'text/plain')

        html = ResponseBodyView(
            body='<a class="button" href="/one">One</a>',
            content_type='text/html',
        )
        self.assertEqual(html.url_hints, ['/one'])

        original_normalize = ResponseBodyView.normalize_hint

        def drop_hint(_value):
            return ''

        try:
            ResponseBodyView.normalize_hint = staticmethod(drop_hint)
            view = ResponseBodyView(body='"/filtered"', content_type='text/plain')
            self.assertEqual(view.url_hints, [])
        finally:
            ResponseBodyView.normalize_hint = original_normalize



if __name__ == '__main__':
    unittest.main()
