# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from urllib3.response import HTTPResponse

from src.core.http.providers.response import ResponseProvider


class BrokenHeaders(object):
    """Headers object that breaks both dict(headers) and headers.items()."""

    def __iter__(self):
        raise TypeError('broken iteration')

    def items(self):
        raise TypeError('broken items')


class DummyResponse(object):
    """Minimal response stub for private ResponseProvider helpers."""

    def __init__(self, status=200, headers=None, body=b'', location=False):
        self.status = status
        self.headers = headers if headers is not None else {}
        self.data = body
        self._location = location

    def get_redirect_location(self):
        return self._location


class TestResponseProviderCoverageExtra(unittest.TestCase):
    """Extra coverage for ResponseProvider edge branches."""

    @staticmethod
    def make_provider(is_waf_detect=False):
        """Create provider with optional WAF detection."""

        return ResponseProvider(SimpleNamespace(is_waf_detect=is_waf_detect))

    @staticmethod
    def make_http_response(status=200, body=b'', headers=None):
        """Create urllib3 HTTPResponse for public detect() tests."""

        return HTTPResponse(status=status, body=body, headers=headers or {})

    def test_collect_header_blob_returns_empty_when_header_container_is_unreadable(self):
        """ResponseProvider should tolerate header containers that break dict() and items()."""

        response = DummyResponse(status=200, headers=BrokenHeaders(), body=b'')
        actual = ResponseProvider._ResponseProvider__collect_header_blob(response)

        self.assertEqual(actual, '')

    def test_collect_body_blob_returns_empty_on_decode_error(self):
        """ResponseProvider should tolerate decode failures."""

        response = DummyResponse(status=200, headers={}, body=b'\xff\xfe\xfd')

        with patch('src.core.http.providers.response.helper.decode', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'bad')):
            actual = ResponseProvider._ResponseProvider__collect_body_blob(response)

        self.assertEqual(actual, '')

    def test_looks_like_blocked_status_returns_false_for_invalid_status(self):
        """ResponseProvider blocked-status helper should tolerate invalid status values."""

        response = DummyResponse(status='not-a-number', headers={}, body=b'')
        actual = ResponseProvider._ResponseProvider__looks_like_blocked_status(response)

        self.assertFalse(actual)

    def test_build_waf_result_uses_default_confidence_when_missing(self):
        """ResponseProvider should default missing WAF confidence to 80."""

        provider = self.make_provider(is_waf_detect=True)

        actual = provider._ResponseProvider__build_waf_result(
            {'name': 'Custom Shield'},
            ['header:x-custom-waf']
        )

        self.assertEqual(
            actual,
            {
                'name': 'Custom Shield',
                'confidence': 80,
                'signals': ['header:x-custom-waf']
            }
        )

    def test_detect_returns_certificate_for_ssl_required_status(self):
        """ResponseProvider.detect() should classify certificate-required statuses."""

        provider = self.make_provider(is_waf_detect=False)
        response = self.make_http_response(status=496, body=b'', headers={})

        self.assertEqual(provider.detect('https://example.com', response), 'certificate')

    def test_detect_returns_auth_for_auth_status(self):
        """ResponseProvider.detect() should classify auth-required statuses."""

        provider = self.make_provider(is_waf_detect=False)
        response = self.make_http_response(status=401, body=b'', headers={})

        self.assertEqual(provider.detect('https://example.com', response), 'auth')

    def test_detect_returns_bad_for_bad_request_status(self):
        """ResponseProvider.detect() should classify bad-request statuses."""

        provider = self.make_provider(is_waf_detect=False)
        response = self.make_http_response(status=400, body=b'', headers={})

        self.assertEqual(provider.detect('https://example.com', response), 'bad')

    def test_detect_raises_for_unknown_status(self):
        """ResponseProvider.detect() should raise on unsupported statuses."""

        provider = self.make_provider(is_waf_detect=False)
        response = self.make_http_response(status=777, body=b'', headers={})

        with self.assertRaises(Exception) as context:
            provider.detect('https://example.com', response)

        self.assertIn('Unknown response status', str(context.exception))

    def test_detect_waf_matches_score_only_header_branch(self):
        """ResponseProvider should match vendor signatures from non-strong header markers via score threshold."""

        provider = self.make_provider(is_waf_detect=True)
        response = DummyResponse(
            status=200,
            headers={'X-Score-Header': '1'},
            body=b''
        )

        custom_signatures = [
            {
                'name': 'ScoreHeaderWAF',
                'header_markers': ['x-score-header'],
                'body_markers': [],
            }
        ]

        with patch.object(ResponseProvider, 'DEFAULT_WAF_SIGNATURES', custom_signatures):
            actual = provider._ResponseProvider__detect_waf(response)

        self.assertEqual(actual['name'], 'ScoreHeaderWAF')
        self.assertEqual(actual['confidence'], 80)

    def test_detect_waf_matches_blocked_status_body_only_branch(self):
        """ResponseProvider should match body-only vendor markers on blocked-like statuses."""

        provider = self.make_provider(is_waf_detect=True)
        response = DummyResponse(
            status=403,
            headers={},
            body=b'alpha beta'
        )

        custom_signatures = [
            {
                'name': 'BodyOnlyShield',
                'header_markers': [],
                'body_markers': ['alpha', 'beta'],
            }
        ]

        with patch.object(ResponseProvider, 'DEFAULT_WAF_SIGNATURES', custom_signatures):
            actual = provider._ResponseProvider__detect_waf(response)

        self.assertEqual(actual['name'], 'BodyOnlyShield')
        self.assertEqual(actual['confidence'], 80)

    def test_detect_waf_matches_generic_body_fallback_on_blocked_status(self):
        """ResponseProvider should fallback to Generic WAF for blocked responses with multiple generic body markers."""

        provider = self.make_provider(is_waf_detect=True)
        response = DummyResponse(
            status=403,
            headers={},
            body=b'checking your browser proof-of-work'
        )

        with patch.object(ResponseProvider, 'DEFAULT_WAF_SIGNATURES', []):
            actual = provider._ResponseProvider__detect_waf(response)

        self.assertEqual(actual['name'], 'Generic WAF')
        self.assertEqual(actual['confidence'], 78)

    def test_detect_waf_returns_none_when_no_vendor_or_generic_markers_match(self):
        """ResponseProvider should return no WAF match for ordinary responses."""

        provider = self.make_provider(is_waf_detect=True)
        response = DummyResponse(
            status=200,
            headers={'Server': 'nginx'},
            body=b'hello world'
        )

        actual = provider._ResponseProvider__detect_waf(response)

        self.assertIsNone(actual)

    def test_get_redirect_url_builds_relative_location_without_leading_slash(self):
        """ResponseProvider should normalize relative redirect locations without a leading slash."""

        response = DummyResponse(status=302, headers={}, body=b'', location='admin')
        actual = ResponseProvider._get_redirect_url('http://example.com/base', response)

        self.assertEqual(actual, 'http://example.com/admin')

    def test_detect_continues_to_next_plugin_when_previous_returns_none(self):
        """ResponseProvider.detect() should continue iterating plugins until one returns a status."""

        provider = self.make_provider(is_waf_detect=False)

        first = unittest.mock.MagicMock()
        first.process.return_value = None

        second = unittest.mock.MagicMock()
        second.process.return_value = 'success'

        provider._response_plugins.extend([first, second])

        response = self.make_http_response(status=200, body=b'', headers={})
        actual = provider.detect('https://example.com', response)

        self.assertEqual(actual, 'success')
        first.process.assert_called_once_with(response)
        second.process.assert_called_once_with(response)

    def test_base_handle_returns_none(self):
        """Base ResponseProvider.handle() should remain a no-op and return None."""

        provider = self.make_provider(is_waf_detect=False)
        response = DummyResponse(status=200, headers={}, body=b'')

        actual = provider.handle(response, 'https://example.com', 1, 1, [])

        self.assertIsNone(actual)

    def test_is_redirect_returns_failed_when_location_is_none(self):
        """ResponseProvider redirect helper should fail when redirect location is None."""

        response = DummyResponse(status=302, headers={}, body=b'', location=None)

        actual = ResponseProvider._ResponseProvider__is_redirect(
            response,
            'https://example.com/start'
        )

        self.assertEqual(actual, 'failed')

    def test_collect_header_blob_returns_empty_when_response_has_no_headers_attribute(self):
        """ResponseProvider should tolerate responses without a headers attribute."""

        response = SimpleNamespace(data=b'hello')

        actual = ResponseProvider._ResponseProvider__collect_header_blob(response)

        self.assertEqual(actual, '')

    def test_detect_waf_matches_blocked_status_header_and_body_branch(self):
        """ResponseProvider should use blocked-status header+body matching when score branch is bypassed."""

        provider = self.make_provider(is_waf_detect=True)
        response = DummyResponse(
            status=403,
            headers={'X-Edge-Shield': '1'},
            body=b'please wait'
        )

        custom_signatures = [
            {
                'name': 'HeaderBodyShield',
                'header_markers': ['x-edge-shield'],
                'body_markers': ['please wait'],
            }
        ]

        with patch.object(ResponseProvider, 'DEFAULT_WAF_SIGNATURES', custom_signatures), \
                patch.object(ResponseProvider, '_ResponseProvider__score_detection', return_value=0):
            actual = provider._ResponseProvider__detect_waf(response)

        self.assertEqual(actual['name'], 'HeaderBodyShield')
        self.assertEqual(actual['confidence'], 80)

    def test_detect_waf_matches_generic_header_fallback(self):
        """ResponseProvider should fallback to Generic WAF when only generic header markers match."""

        provider = self.make_provider(is_waf_detect=True)
        response = DummyResponse(
            status=200,
            headers={'X-Distil-Cs': '1'},
            body=b'hello'
        )

        with patch.object(ResponseProvider, 'DEFAULT_WAF_SIGNATURES', []):
            actual = provider._ResponseProvider__detect_waf(response)

        self.assertEqual(actual['name'], 'Generic WAF')
        self.assertEqual(actual['confidence'], 80)