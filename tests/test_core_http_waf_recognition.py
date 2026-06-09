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

    def test_detect_should_not_classify_reflected_fortinet_path_404_as_fortiweb(self):
        """ResponseProvider should not treat reflected request paths as FortiWeb evidence."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=404,
            headers={
                'Server': 'Apache',
                'Content-Type': 'text/html',
                'Content-Length': '206',
            },
            body=(
                b'<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">'
                b'<html><head><title>404 Not Found</title></head><body>'
                b'<h1>Not Found</h1>'
                b'<p>The requested URL /fortinet was not found on this server.</p>'
                b'</body></html>'
            ),
        )

        self.assertEqual(provider.detect('https://localhost/fortinet', response), 'failed')
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

    def test_should_detect_bunkerweb_from_explicit_block_page_body(self):
        """ResponseProvider should detect BunkerWeb from explicit block-page body markers."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=403,
            headers={
                'Content-Type': 'text/html; charset=utf-8',
                'Content-Length': '512',
            },
            body=(
                b'<html><title>403 | Forbidden</title>'
                b'<div class="caption">Your Client</div><p class="status-text"> Forbidden</p>'
                b'<div class="caption">BunkerWeb</div><p class="status-text">Working</p>'
                b'<a href="https://www.bunkerweb.io/" class="bunker-svg">BunkerWeb</a>'
                b'<path class="bunker-cls-2" d="M0 0" />'
                b'<linearGradient id="bw_error_gradient_29"></linearGradient>'
                b'<footer>This website is protected with&nbsp;<a href="https://www.bunkerweb.io/">BunkerWeb</a></footer>'
                b'</html>'
            ),
        )

        self.assertEqual(provider.detect('https://example.com', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'BunkerWeb')
        self.assertEqual(provider.waf_detection['confidence'], 88)
        self.assertIn('body:bunkerweb', provider.waf_detection['signals'])

    def test_should_not_detect_bunkerweb_markers_on_success_response(self):
        """ResponseProvider should not classify BunkerWeb body markers on normal success pages."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=200,
            headers={
                'Content-Type': 'text/html; charset=utf-8',
                'Content-Length': '128',
            },
            body=b'<html><body>BunkerWeb status page bunkerweb.io</body></html>',
        )

        self.assertEqual(provider.detect('https://example.com', response), 'success')
        self.assertIsNone(provider.waf_detection)

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

    def test_detect_cityhost_secure_page_lock(self):
        """ResponseProvider should detect CityHost secure page lock from exact cookie marker."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=423,
            headers={
                'Server': 'nginx',
                'Set-Cookie': 'cityhost_secure_page=security_page_have_not_pass; Max-Age=43200',
                'X-Powered-By': 'PHP/7.4.33',
                'Content-Type': 'text/html; charset=UTF-8',
            },
            body=b'',
        )

        self.assertEqual(provider.detect('https://example.com/manager/index.php', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'CityHost Secure Page')
        self.assertEqual(provider.waf_detection['confidence'], 88)
        self.assertIn(
            'header:cityhost_secure_page=security_page_have_not_pass',
            provider.waf_detection['signals'],
        )

    def test_plain_423_without_waf_marker_stays_certificate(self):
        """ResponseProvider should keep plain 423 responses in certificate bucket."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=423,
            headers={
                'Server': 'nginx',
                'X-Powered-By': 'PHP/7.4.33',
                'Content-Length': '0',
            },
            body=b'',
        )

        self.assertEqual(provider.detect('https://example.com/locked', response), 'certificate')
        self.assertIsNone(provider.waf_detection)

    def test_cityhost_passed_cookie_does_not_trigger_waf(self):
        """ResponseProvider should avoid broad CityHost cookie false positives."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=200,
            headers={
                'Set-Cookie': 'cityhost_secure_page=security_page_have_pass; Max-Age=43200',
                'Content-Length': '2',
            },
            body=b'ok',
        )

        self.assertEqual(provider.detect('https://example.com/', response), 'success')
        self.assertIsNone(provider.waf_detection)


    def test_detect_sw_js_challenge_page(self):
        """ResponseProvider should classify SW __js_p_ JavaScript challenge as blocked."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=200,
            headers={
                'Server': 'sw',
                'Content-Length': '13602',
                'Cache-Control': 'no-cache',
                'Content-Type': 'text/html; charset=utf-8',
                'Set-Cookie': '__js_p_=30,1800,0,0,0; Path=/',
            },
            body=(
                b'<html><head><meta name="robots" content="noindex, noarchive" />'
                b'<style>.gorizontal-vertikal {position:absolute}</style></head>'
                b'<body><img src="data:image/gif;base64,R0lGODlhQgBCA" />'
                b'<script>function get_jhash(b){return b;}'
                b'document.cookie = "__jhash_=" + get_jhash(30);'
                b'document.cookie = "__jua_=" + encodeURIComponent(navigator.userAgent);'
                b'window.location.href = construct_utm_uri(0);</script></body></html>'
            ),
        )

        self.assertEqual(provider.detect('https://example.com/fail001', response), 'blocked')
        self.assertEqual(provider.waf_detection['name'], 'SW JS Challenge')
        self.assertIn('header:set-cookie: __js_p_=', provider.waf_detection['signals'])
        self.assertIn('body:get_jhash(', provider.waf_detection['signals'])
        self.assertIn('body:document.cookie = "__jua_="', provider.waf_detection['signals'])

    def test_sw_server_without_js_challenge_stays_success(self):
        """ResponseProvider should not classify ordinary server: sw pages as blocked."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=200,
            headers={
                'Server': 'sw',
                'Content-Type': 'text/html; charset=UTF-8',
                'Content-Length': '211297',
            },
            body=b'<html><body>ordinary Bitrix page</body></html>',
        )

        self.assertEqual(provider.detect('https://example.com/currency/', response), 'success')
        self.assertIsNone(provider.waf_detection)

    def test_sw_js_cookie_without_challenge_body_stays_success(self):
        """ResponseProvider should avoid broad __js_p_ cookie false positives."""

        provider = ResponseProvider(self.make_config())
        response = DummyResponse(
            status=200,
            headers={
                'Server': 'sw',
                'Set-Cookie': '__js_p_=30,1800,0,0,0; Path=/',
                'Content-Type': 'text/html; charset=utf-8',
                'Content-Length': '128',
            },
            body=b'<html><body>regular page after security cookie was already set</body></html>',
        )

        self.assertEqual(provider.detect('https://example.com/', response), 'success')
        self.assertIsNone(provider.waf_detection)


    def test_should_detect_wafw00f_inspired_managed_waf_signatures(self):
        """ResponseProvider should detect additional managed WAF vendors from passive block markers."""

        cases = [
            (
                'DDoS-GUARD',
                403,
                {'Server': 'ddos-guard', 'Content-Length': '12'},
                b'DDoS-GUARD protection page',
            ),
            (
                'Google Cloud Armor',
                403,
                {'Server': 'Google Frontend', 'X-Cloud-Trace-Context': 'trace', 'Content-Length': '64'},
                b'Request denied by Cloud Armor policy. Google Cloud Armor blocked this request.',
            ),
            (
                'SafeLine',
                403,
                {'X-SafeLine': '1', 'Content-Length': '64'},
                b'Blocked by SafeLine WAF. Chaitin SafeLine protected this website.',
            ),
            (
                'Tencent Cloud WAF',
                403,
                {'X-QCloud-WAF': '1', 'Content-Length': '64'},
                b'Tencent Cloud WAF: request has been blocked by QCloud WAF.',
            ),
            (
                'Vercel WAF',
                403,
                {'Content-Length': '64'},
                b'Vercel Security Checkpoint. Request blocked by Vercel WAF.',
            ),
            (
                'Wallarm',
                403,
                {'X-Wallarm': 'block', 'Content-Length': '64'},
                b'Blocked by Wallarm. Wallarm blocked suspicious request.',
            ),
            (
                'Wordfence',
                403,
                {'Content-Length': '64'},
                b'This response was generated by Wordfence Security.',
            ),
        ]

        for vendor, status, headers, body in cases:
            with self.subTest(vendor=vendor):
                provider = ResponseProvider(self.make_config())
                response = DummyResponse(
                    status=status,
                    headers=headers,
                    body=body,
                )

                self.assertEqual(provider.detect('https://example.com', response), 'blocked')
                self.assertEqual(provider.waf_detection['name'], vendor)

    def test_should_not_classify_new_passive_vendor_headers_on_success_response(self):
        """ResponseProvider should gate new passive WAF vendor headers behind block-like statuses."""

        cases = [
            ({'Server': 'ddos-guard'}, 'DDoS-GUARD'),
            ({'Server': 'Google Frontend', 'X-Cloud-Trace-Context': 'trace'}, 'Google Cloud Armor'),
            ({'X-SafeLine': '1'}, 'SafeLine'),
            ({'X-QCloud-WAF': '1'}, 'Tencent Cloud WAF'),
            ({'X-Wallarm': 'pass'}, 'Wallarm'),
        ]

        for headers, vendor in cases:
            with self.subTest(vendor=vendor):
                provider = ResponseProvider(self.make_config())
                response_headers = {'Content-Length': '11'}
                response_headers.update(headers)
                response = DummyResponse(
                    status=200,
                    headers=response_headers,
                    body=b'normal page',
                )

                self.assertEqual(provider.detect('https://example.com', response), 'success')
                self.assertIsNone(provider.waf_detection)



    def test_should_detect_xsstrike_audited_unique_waf_signatures(self):
        """ResponseProvider should detect non-conflicting legacy WAF vendors from unique passive markers."""

        cases = [
            (
                'aeSecure',
                403,
                {'aeSecure-Code': 'deny', 'Content-Length': '64'},
                b'<img src="/aesecure_denied.png" alt="Denied">',
            ),
            (
                'Armor Protection',
                403,
                {'Content-Length': '64'},
                b'This request has been blocked by website protection from Armor.',
            ),
            (
                'Baidu Yunjiasu',
                403,
                {'Server': 'yunjiasu-nginx', 'Content-Length': '64'},
                b'Yunjiasu denied this request.',
            ),
            (
                'BlockDoS',
                403,
                {'Server': 'BlockDos.net', 'Content-Length': '64'},
                b'Blocked by BlockDos.net protection.',
            ),
            (
                'Cisco ACE XML Gateway',
                403,
                {'Server': 'ACE XML Gateway', 'Content-Length': '64'},
                b'ACE XML Gateway rejected this request.',
            ),
            (
                'Cloudbric',
                403,
                {'Content-Length': '64'},
                b'Cloudbric: Malicious Code Detected.',
            ),
            (
                'CrawlProtect',
                403,
                {'Content-Length': '64'},
                b'This site is protected by CrawlProtect.',
            ),
            (
                'DenyAll',
                403,
                {'Content-Length': '64'},
                b'Condition Intercepted by DenyAll.',
            ),
            (
                'SEnginx',
                403,
                {'Content-Length': '64'},
                b'SENGINX-ROBOT-MITIGATION challenge page.',
            ),
            (
                'SiteLock TrueShield',
                403,
                {'Content-Length': '64'},
                b'SiteLock Incident ID: abc123 sitelock_shield_logo',
            ),
            (
                'SonicWALL',
                403,
                {'Server': 'SonicWALL', 'Content-Length': '64'},
                b'This request is blocked by the SonicWALL.',
            ),
            (
                'Sophos UTM Web Protection',
                403,
                {'Content-Length': '64'},
                b'Powered by UTM Web Protection.',
            ),
            (
                'Stingray Application Firewall',
                403,
                {'X-Mapping-Session': 'abc', 'Content-Length': '64'},
                b'blocked',
            ),
            (
                'Teros / Citrix Application Firewall',
                403,
                {'Set-Cookie': 'st8id=abc; Path=/', 'Content-Length': '64'},
                b'blocked',
            ),
            (
                'TrafficShield',
                403,
                {'Set-Cookie': 'ASINFO=abc; Path=/', 'Content-Length': '64'},
                b'blocked',
            ),
            (
                'UrlScan',
                403,
                {'Rejected-By-UrlScan': '1', 'Content-Length': '64'},
                b'Rejected-By-UrlScan',
            ),
            (
                'USP Secure Entry Server',
                403,
                {'Server': 'Secure Entry Server', 'Content-Length': '64'},
                b'blocked',
            ),
            (
                'Varnish WAF',
                403,
                {'Content-Length': '64'},
                b'xVarnish-WAF block page.',
            ),
            (
                'WatchGuard',
                403,
                {'Server': 'WatchGuard', 'Content-Length': '64'},
                b'blocked',
            ),
            (
                'Yundun',
                403,
                {'Server': 'YUNDUN', 'Content-Length': '64'},
                b'blocked',
            ),
            (
                'Zenedge',
                403,
                {'Server': 'ZENEDGE', 'Content-Length': '64'},
                b'/zenedge/assets/deny.html',
            ),
        ]

        for vendor, status, headers, body in cases:
            with self.subTest(vendor=vendor):
                provider = ResponseProvider(self.make_config())
                response = DummyResponse(
                    status=status,
                    headers=headers,
                    body=body,
                )

                self.assertEqual(provider.detect('https://example.com', response), 'blocked')
                self.assertEqual(provider.waf_detection['name'], vendor)

    def test_should_gate_xsstrike_audited_passive_waf_headers_on_success_response(self):
        """ResponseProvider should not classify unique passive WAF headers on ordinary successful pages."""

        cases = [
            {'aeSecure-Code': 'pass'},
            {'Server': 'yunjiasu-nginx'},
            {'Server': 'BlockDos.net'},
            {'Server': 'ACE XML Gateway'},
            {'Server': 'SonicWALL'},
            {'X-Mapping-Session': 'abc'},
            {'Set-Cookie': 'st8id=abc; ASINFO=abc'},
            {'Server': 'Secure Entry Server'},
            {'Server': 'WatchGuard'},
            {'Server': 'YUNDUN'},
            {'Server': 'ZENEDGE'},
        ]

        for headers in cases:
            with self.subTest(headers=headers):
                provider = ResponseProvider(self.make_config())
                response_headers = {'Content-Length': '11'}
                response_headers.update(headers)
                response = DummyResponse(
                    status=200,
                    headers=response_headers,
                    body=b'normal page',
                )

                self.assertEqual(provider.detect('https://example.com', response), 'success')
                self.assertIsNone(provider.waf_detection)

    def test_should_not_classify_xsstrike_audited_vendor_names_without_block_evidence(self):
        """ResponseProvider should avoid vendor-name false positives without unique block evidence."""

        cases = [
            b'Cloudbric product comparison page.',
            b'Baidu Yunjiasu marketing content.',
            b'Sophos support article.',
            b'WatchGuard partner page.',
            b'Zenedge migration notes.',
        ]

        for body in cases:
            with self.subTest(body=body):
                provider = ResponseProvider(self.make_config())
                response = DummyResponse(
                    status=200,
                    headers={'Content-Length': str(len(body))},
                    body=body,
                )

                self.assertEqual(provider.detect('https://example.com', response), 'success')
                self.assertIsNone(provider.waf_detection)


if __name__ == '__main__':
    unittest.main()
