# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.lib.browser import cookie_gate


class CookieGateGuardTest(unittest.TestCase):
    """Regression and branch coverage for JavaScript cookie-gate guards."""

    @staticmethod
    def response(body, status=200, headers=None):
        """Build a minimal response-like object."""

        if headers is None:
            headers = {'Content-Type': 'text/html'}
        if isinstance(body, str):
            body = body.encode('utf-8')
        return SimpleNamespace(status=status, headers=headers, data=body)

    def test_should_accept_navigation_marker_variants_without_visible_text(self):
        """Cookie gate guard should cover reload, href, replace and assign navigation variants."""

        markers = [
            'location.reload();',
            'window.location.reload();',
            'document.location.reload();',
            'location.href="/admin";',
            'window.location.href="/admin";',
            'document.location.href="/admin";',
            'location.replace("/admin");',
            'window.location.replace("/admin");',
            'document.location.replace("/admin");',
            'location.assign("/admin");',
            'window.location.assign("/admin");',
            'document.location.assign("/admin");',
            'window.location="/admin";',
            'document.location="/admin";',
        ]

        for marker in markers:
            with self.subTest(marker=marker):
                response = self.response(
                    '<html><body><script>'
                    'document.cookie="bpc=abc;Domain=example.com;Path=/";'
                    f'{marker}'
                    '</script></body></html>'
                )
                self.assertTrue(cookie_gate.is_js_cookie_gate_response(response))
                self.assertEqual(
                    cookie_gate.match_js_cookie_gate_response(response)['calibration_reason'],
                    'js-cookie-reload-challenge',
                )

    def test_should_reject_unknown_cookie_gate_markers_when_layout_is_not_script_only(self):
        """Unknown cookie gates need a script-only shell to avoid suppressing embedded scripts."""

        response = self.response(
            '<html><meta charset="utf-8"><script>'
            'document.cookie="custom=1";location.href="/admin";'
            '</script></html>'
        )

        self.assertFalse(cookie_gate.is_js_cookie_gate_response(response))
        self.assertIsNone(cookie_gate.match_js_cookie_gate_response(response))

    def test_should_allow_known_cookie_gate_markers_even_when_shell_has_metadata(self):
        """Known hosting cookie gates may include small metadata before the bootstrap script."""

        response = self.response(
            '<html><meta charset="utf-8"><script>'
            'document.cookie="beget=begetok";location.href="/admin";'
            '</script></html>'
        )

        self.assertTrue(cookie_gate.is_js_cookie_gate_response(response))

    def test_should_use_response_data_status_when_response_status_is_unavailable(self):
        """Legacy response tuples should remain supported as fallback status source."""

        response = SimpleNamespace(
            headers={'Content-Type': 'text/html'},
            data=(
                '<html><body><script>document.cookie="bpc=1";'
                'document.location.href="/admin";</script></body></html>'
            ).encode('utf-8'),
        )

        self.assertTrue(cookie_gate.is_js_cookie_gate_response(
            response,
            ('success', 'https://example.com/admin', '100B', '200'),
        ))
        self.assertFalse(cookie_gate.is_js_cookie_gate_response(
            response,
            ('success', 'https://example.com/admin', '100B', 'bad'),
        ))
        self.assertFalse(cookie_gate.is_js_cookie_gate_response(response, None))

    def test_response_body_text_should_handle_decode_and_string_errors(self):
        """Body decoding should fail closed for broken response-like objects."""

        with patch('src.lib.browser.cookie_gate.helper.decode', side_effect=UnicodeError('bad')):
            self.assertEqual(cookie_gate.response_body_text(self.response(b'\xff')), '')

        class BrokenString(object):
            def __str__(self):
                raise TypeError('broken str')

        self.assertEqual(cookie_gate.response_body_text(SimpleNamespace(data=BrokenString())), '')
        self.assertEqual(cookie_gate.response_body_text(SimpleNamespace()), '')

    def test_get_header_value_should_handle_case_insensitive_and_broken_headers(self):
        """Header lookup should be case-insensitive and defensive."""

        self.assertEqual(
            cookie_gate.get_header_value(SimpleNamespace(headers={'content-type': 'text/html'}), 'Content-Type'),
            'text/html',
        )
        self.assertIsNone(cookie_gate.get_header_value(SimpleNamespace(), 'Content-Type'))

        class HeaderItemsNoMatch(object):
            def get(self, _name):
                return None

            def items(self):
                return [('Server', 'nginx')]

        self.assertIsNone(cookie_gate.get_header_value(SimpleNamespace(headers=HeaderItemsNoMatch()), 'Content-Type'))

        class BrokenHeaders(object):
            pass

        self.assertIsNone(cookie_gate.get_header_value(SimpleNamespace(headers=BrokenHeaders()), 'Content-Type'))

    def test_visible_text_without_scripts_should_fallback_when_parser_fails(self):
        """Visible text extraction should degrade to tag stripping on parser errors."""

        with patch('src.lib.browser.cookie_gate._VisibleTextExtractor.feed', side_effect=ValueError('bad html')):
            self.assertEqual(cookie_gate.visible_text_without_scripts('<b>Visible</b>'), 'Visible')


if __name__ == '__main__':
    unittest.main()
