# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace

from src.core.http.providers.response import ResponseProvider
from src.core.http.response import Response


class DummyResponse(object):
    def __init__(self, status=200, headers=None, body=b'', redirect=False):
        self.status = status
        self.headers = headers or {}
        self.data = body
        self._redirect = redirect

    def get_redirect_location(self):
        return False if self._redirect is False else self._redirect


class DummyDebug(object):
    def __init__(self, level=0):
        self.level = level

    def debug_response(self, *args, **kwargs):
        return True

    def debug_request_uri(self, *args, **kwargs):
        return True

    def debug_load_sniffer_plugin(self, *args, **kwargs):
        return True


class TestWafRecognition(unittest.TestCase):
    """WAF recognition tests."""

    def make_config(self):
        return SimpleNamespace(
            is_waf_detect=True,
            is_sniff=False,
            sniffers=[],
            scan='directories',
            SUBDOMAINS_SCAN='subdomains',
        )

    def test_detect_anubis_by_strong_header(self):
        """ResponseProvider should detect Anubis from strong response headers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=200,
            headers={
                'Techaro.Lol-Anubis-Cookie-Verification': '1',
                'Content-Length': '0',
            },
            body=b'',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Anubis')
        self.assertEqual(provider.waf_detection['confidence'], 95)

    def test_detect_cloudflare_challenge_from_header(self):
        """ResponseProvider should detect Cloudflare from active challenge headers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'Server': 'cloudflare',
                'CF-Ray': 'abc123',
                'CF-Mitigated': 'challenge',
                'Content-Length': '0',
            },
            body=b'',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Cloudflare')
        self.assertEqual(provider.waf_detection['confidence'], 92)

    def test_detect_cloudflare_cdn_404_as_failed(self):
        """ResponseProvider should not classify passive Cloudflare CDN 404 as blocked."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=404,
            headers={
                'Server': 'cloudflare',
                'CF-Ray': 'abc123',
                'CF-Cache-Status': 'DYNAMIC',
                'Content-Length': '193536',
            },
            body=b'ordinary not found page with Cloudflare Ray ID footer',
        )

        self.assertEqual(provider.detect('https://example.com/missing', response), 'failed')
        self.assertIsNone(provider.waf_detection)

    def test_detect_cloudflare_cdn_301_as_redirect(self):
        """ResponseProvider should not classify passive Cloudflare CDN redirects as blocked."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=301,
            headers={
                'Server': 'cloudflare',
                'CF-Ray': 'abc123',
                'Content-Length': '0',
            },
            redirect='https://example.com/target',
        )

        self.assertEqual(provider.detect('https://example.com/source', response), 'redirect')
        self.assertIsNone(provider.waf_detection)

    def test_detect_cloudflare_rate_limit_from_passive_headers(self):
        """ResponseProvider should still classify Cloudflare 429 as blocked."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=429,
            headers={
                'Server': 'cloudflare',
                'CF-Ray': 'abc123',
                'Content-Length': '0',
            },
            body=b'',
        )

        self.assertEqual(provider.detect('https://example.com/rate-limited', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Cloudflare')

    def test_detect_sucuri_from_header_and_body(self):
        """ResponseProvider should detect Sucuri from vendor markers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-Sucuri-Block': '1',
                'Content-Length': '48',
            },
            body=b'Access denied - Sucuri Website Firewall',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Sucuri')

    def test_detect_akamai_from_header_and_body(self):
        """ResponseProvider should detect Akamai challenge pages."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'Akamai-GRN': '0.0.0000',
                'Content-Length': '64',
            },
            body=b'Access Denied Reference #18. generated by Akamai',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Akamai')

    def test_detect_aws_waf(self):
        """ResponseProvider should detect AWS WAF style blocks."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-Amzn-RequestId': 'req-id',
                'Content-Length': '12',
            },
            body=b'request blocked',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'AWS WAF')

    def test_detect_datadome(self):
        """ResponseProvider should detect DataDome markers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-DataDome': '1',
                'Set-Cookie': 'datadome=abc',
                'Content-Length': '12',
            },
            body=b'Please enable JS',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'DataDome')

    def test_detect_generic_waf_from_strong_generic_header(self):
        """ResponseProvider should fallback to Generic WAF for unmatched strong markers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-Distil-Cs': '1',
                'Content-Length': '0',
            },
            body=b'',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Distil')

    def test_generic_fallback_requires_more_than_single_weak_body_marker(self):
        """ResponseProvider should not classify plain pages from a single weak body marker."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=200,
            headers={'Content-Length': '13'},
            body=b'just a moment',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'success')
        self.assertIsNone(provider.waf_detection)

    def test_handle_keeps_blocked_status_and_exposes_metadata(self):
        """Response.handle() should keep blocked status while exposing WAF metadata."""

        response_handler = Response(self.make_config(), DummyDebug(), tpl=SimpleNamespace())
        response = DummyResponse(
            status=403,
            headers={
                'Server': 'cloudflare',
                'CF-Ray': 'abc123',
                'Content-Length': '25',
            },
            body=b'Checking your browser',
        )

        status, url, size, code = response_handler.handle(
            response,
            'https://example.com/login',
            1,
            1,
            []
        )

        self.assertEqual((status, url, size, code), ('blocked', 'https://example.com/login', '25B', '403'))
        self.assertEqual(response_handler.waf_detection['name'], 'Cloudflare')
        self.assertEqual(response_handler.waf_detection['confidence'], 92)

    def test_detect_skips_waf_signatures_when_waf_detect_is_disabled(self):
        """ResponseProvider.detect() should not classify WAF challenges when waf-detect is disabled."""

        cfg = SimpleNamespace(is_waf_detect=False)
        provider = ResponseProvider(cfg)
        response = DummyResponse(
            status=200,
            headers={
                'Server': 'cloudflare',
                'CF-Ray': 'abc123',
                'Content-Length': '25',
            },
            body=b'Checking your browser before accessing',
        )

        self.assertEqual(provider.detect('https://example.com/login', response), 'success')
        self.assertIsNone(getattr(provider, 'waf_detection', None))

    def test_detect_classifies_waf_when_waf_detect_is_enabled(self):
        """ResponseProvider.detect() should classify vendor-aware WAF challenges only when enabled."""

        cfg = SimpleNamespace(is_waf_detect=True)
        provider = ResponseProvider(cfg)
        response = DummyResponse(
            status=200,
            headers={
                'Server': 'cloudflare',
                'CF-Ray': 'abc123',
                'Content-Length': '25',
            },
            body=b'Checking your browser before accessing',
        )

        self.assertEqual(provider.detect('https://example.com/login', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Cloudflare')

    def test_detect_fortiweb(self):
        """ResponseProvider should detect FortiWeb markers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'Server': 'FortiWeb',
                'Content-Length': '12',
            },
            body=b'FortiWeb Web Application Firewall',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'FortiWeb')

    def test_detect_reblaze(self):
        """ResponseProvider should detect Reblaze markers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-Rbzid': 'abc123',
                'Content-Length': '12',
            },
            body=b'Reblaze Secure Web Gateway',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Reblaze')

    def test_detect_netscaler(self):
        """ResponseProvider should detect NetScaler / Citrix WAF markers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'Set-Cookie': 'NS_Af=xyz',
                'Content-Length': '24',
            },
            body=b'Request denied by NetScaler',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'NetScaler / Citrix WAF')

    def test_detect_apptrana(self):
        """ResponseProvider should detect AppTrana markers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-AppTrana-Trace': '1',
                'Content-Length': '12',
            },
            body=b'AppTrana request blocked',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'AppTrana')

    def test_detect_huawei_cloud_waf(self):
        """ResponseProvider should detect Huawei Cloud WAF markers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-HWWAF-Test': '1',
                'Content-Length': '16',
            },
            body=b'Huawei Cloud WAF',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Huawei Cloud WAF')


    def test_should_detect_360_waf_from_ray_header(self):
        """ResponseProvider should detect 360 WAF explicit block headers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=493,
            headers={
                'WZWS-Ray': 'abc123',
                'Content-Length': '0',
            },
            body=b'',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], '360 WAF')

    def test_should_detect_airlock_from_cookie_and_body(self):
        """ResponseProvider should detect Airlock syntax-block responses."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'Set-Cookie': 'AL-SESS=abc; AL-LB=node1',
                'Content-Length': '128',
            },
            body=b'Server detected a syntax error in your request. Check your request and all parameters.',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'Airlock')

    def test_should_detect_binarysec_from_vendor_header(self):
        """ResponseProvider should detect BinarySec from dedicated headers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-BinarySec-Via': 'edge',
                'Content-Length': '0',
            },
            body=b'',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'BinarySec')

    def test_should_detect_dotdefender_from_denied_header(self):
        """ResponseProvider should detect DotDefender block evidence."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-dotDefender-denied': '1',
                'Content-Length': '32',
            },
            body=b'dotDefender Blocked Your Request',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'DotDefender')

    def test_should_detect_naxsi_from_header_and_body(self):
        """ResponseProvider should detect NAXSI block markers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-Data-Origin': 'naxsi/waf',
                'Content-Length': '64',
            },
            body=b'This Request Has Been Blocked By NAXSI',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'NAXSI')

    def test_should_detect_webknight_from_server_header(self):
        """ResponseProvider should detect WebKnight server signature."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'Server': 'WebKnight/4.6',
                'Content-Length': '0',
            },
            body=b'',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'WebKnight')

    def test_should_ignore_passive_header_gated_vendor_on_success_response(self):
        """ResponseProvider should not classify passive gateway headers on normal success."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=200,
            headers={
                'X-Backside-Transport': 'OK OK',
                'Content-Length': '13',
            },
            body=b'normal page',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'success')
        self.assertIsNone(provider.waf_detection)

    def test_should_ignore_new_passive_vendor_headers_on_success_response(self):
        """ResponseProvider should not classify passive vendor-presence headers on normal success."""

        cases = [
            ({'WZWS-Ray': 'abc123'}, '360 WAF'),
            ({'Set-Cookie': 'AL-SESS=abc; AL-LB=node1'}, 'Airlock'),
            ({'X-Powered-By-Anquanbao': '1'}, 'Anquanbao'),
            ({'X-BinarySec-Via': 'edge'}, 'BinarySec'),
            ({'X-DIS-Request-ID': 'req-1'}, 'DoSArrest'),
            ({'X-Instart-Request-ID': 'req-1'}, 'Instart DX'),
            ({'X-Data-Origin': 'naxsi/waf'}, 'NAXSI'),
            ({'Set-Cookie': 'PLBSID=node1'}, 'Profense'),
            ({'Server': 'WebKnight/4.6'}, 'WebKnight'),
        ]

        for headers, vendor in cases:
            with self.subTest(vendor=vendor):
                provider = ResponseProvider(self.make_config())
                response_headers = {
                    'Content-Length': '11',
                }
                response_headers.update(headers)
                response = DummyResponse(
                    status=200,
                    headers=response_headers,
                    body=b'normal page',
                )

                self.assertEqual(provider.detect('https://example.com', response), 'success')
                self.assertIsNone(provider.waf_detection)

    def test_should_detect_passive_header_gated_vendor_on_blocked_response(self):
        """ResponseProvider should classify passive gateway headers when status is block-like."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'X-Backside-Transport': 'FAIL FAIL',
                'Content-Length': '0',
            },
            body=b'',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'IBM DataPower')

if __name__ == '__main__':
    unittest.main()
