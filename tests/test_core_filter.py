# -*- coding: utf-8 -*-

import io
import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.options.filter import Filter
from src.core.options.exceptions import FilterError


class TestFilter(unittest.TestCase):
    """TestFilter class."""

    def test_filter_builds_host_scheme_ssl_and_proxy(self):
        """Filter.filter() should normalize host, scheme, ssl and proxy fields."""

        args = {
            'host': 'example.com',
            'scan': 'subdomains',
            'proxy': 'http://127.0.0.1:8080',
            'debug': 1,
        }

        actual = Filter.filter(args)

        self.assertEqual(actual['host'], 'example.com')
        self.assertEqual(actual['scheme'], 'http://')
        self.assertFalse(actual['ssl'])
        self.assertEqual(actual['scan'], 'subdomains')
        self.assertEqual(actual['proxy'], 'http://127.0.0.1:8080')
        self.assertEqual(actual['debug'], 1)

    def test_filter_rejects_multiple_proxy_sources(self):
        """Filter.filter() should require exactly one proxy source when proxy routing is configured."""

        cases = [
            {'host': 'example.com', 'proxy': 'http://127.0.0.1:8080', 'proxy_list': 'proxies.txt'},
            {'host': 'example.com', 'proxy': 'http://127.0.0.1:8080', 'proxy_pool': True},
            {'host': 'example.com', 'proxy_list': 'proxies.txt', 'proxy_pool': True},
        ]

        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(FilterError) as context:
                    Filter.filter(case)

                self.assertIn('cannot be used together', str(context.exception))

    def test_validate_proxy_options_allows_single_proxy_sources(self):
        """Filter.validate_proxy_options() should allow each proxy source by itself."""

        self.assertIsNone(Filter.validate_proxy_options({'proxy': 'http://127.0.0.1:8080'}))
        self.assertIsNone(Filter.validate_proxy_options({'proxy_list': 'proxies.txt'}))
        self.assertIsNone(Filter.validate_proxy_options({'proxy_pool': True}))

    def test_scheme_defaults_to_http(self):
        """Filter.scheme() should default to HTTP when scheme is missing."""

        self.assertEqual(Filter.scheme('example.com'), 'http://')

    def test_scheme_preserves_https(self):
        """Filter.scheme() should preserve HTTPS."""

        self.assertEqual(Filter.scheme('https://example.com'), 'https://')

    def test_ssl_returns_expected_boolean(self):
        """Filter.ssl() should detect HTTPS."""

        self.assertTrue(Filter.ssl('https://'))
        self.assertFalse(Filter.ssl('http://'))

    def test_host_accepts_plain_hostname(self):
        """Filter.host() should normalize a plain hostname."""

        self.assertEqual(Filter.host('example.com'), 'example.com')

    def test_host_accepts_https_hostname(self):
        """Filter.host() should normalize a hostname with HTTPS scheme."""

        self.assertEqual(Filter.host('https://example.com'), 'example.com')

    def test_host_accepts_ip_address(self):
        """Filter.host() should accept IPv4 hosts."""

        self.assertEqual(Filter.host('192.168.1.10'), '192.168.1.10')

    def test_host_decodes_idna_hostname(self):
        """Filter.host() should try IDNA decode for non-latin hosts."""

        with patch('src.core.options.filter.helper.decode_hostname', return_value='xn--e1afmkfd.xn--p1ai') as decode_mock:
            actual = Filter.host('пример.рф')

        self.assertEqual(actual, 'xn--e1afmkfd.xn--p1ai')
        decode_mock.assert_called_once_with('пример.рф')

    def test_host_raises_for_invalid_hostname(self):
        """Filter.host() should reject invalid hosts after decode attempt."""

        with patch('src.core.options.filter.helper.decode_hostname', return_value='invalid host value'):
            with self.assertRaises(FilterError):
                Filter.host('пример.рф')

    def test_host_raises_for_decode_errors(self):
        """Filter.host() should wrap unicode decode failures."""

        with patch('src.core.options.filter.helper.decode_hostname', side_effect=UnicodeError('bad idna')):
            with self.assertRaises(FilterError):
                Filter.host('пример.рф')

    def test_proxy_accepts_supported_schemes(self):
        """Filter.proxy() should accept supported proxy schemes with a port."""

        supported = [
            'http://127.0.0.1:8080',
            'https://127.0.0.1:8443',
            'socks4://127.0.0.1:9050',
            'socks5://127.0.0.1:9050',
            'socks5h://127.0.0.1:9050',
        ]

        for proxy in supported:
            with self.subTest(proxy=proxy):
                self.assertEqual(Filter.proxy(proxy), proxy)

    def test_proxy_rejects_invalid_proxy_values(self):
        """Filter.proxy() should reject invalid proxy definitions."""

        with self.assertRaises(FilterError):
            Filter.proxy('ftp://127.0.0.1:21')

        with self.assertRaises(FilterError):
            Filter.proxy('http://127.0.0.1')

    def test_scan_falls_back_to_directories_for_unknown_value(self):
        """Filter.scan() should default to directories for unsupported values."""

        self.assertEqual(Filter.scan('unknown'), 'directories')
        self.assertEqual(Filter.scan('directories'), 'directories')
        self.assertEqual(Filter.scan('subdomains'), 'subdomains')

    def test_filter_validates_retries_as_non_negative_integer(self):
        """Filter.filter() should normalize retries and reject unsafe values."""

        self.assertEqual(Filter.filter({'host': 'example.com', 'retries': '0'})['retries'], 0)
        self.assertEqual(Filter.filter({'host': 'example.com', 'retries': '3'})['retries'], 3)

        with self.assertRaises(FilterError):
            Filter.filter({'host': 'example.com', 'retries': '-1'})

        with self.assertRaises(FilterError):
            Filter.filter({'host': 'example.com', 'retries': 'abc'})


    def test_filter_builds_single_target_list_for_host(self):
        """Filter.filter() should expose a single normalized target for --host."""

        actual = Filter.filter({'host': 'https://example.com'})

        self.assertEqual(actual['host'], 'example.com')
        self.assertEqual(actual['scheme'], 'https://')
        self.assertTrue(actual['ssl'])
        self.assertEqual(actual['targets'], [
            {
                'host': 'example.com',
                'scheme': 'https://',
                'ssl': True,
                'source': 'https://example.com',
            }
        ])

    def test_targets_should_read_hostlist_and_deduplicate(self):
        """Filter.targets() should read hostlist entries, ignore blanks/comments and deduplicate them."""

        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as handle:
            handle.write('\n# comment\nexample.com\nhttps://example.com\nexample.com\nsecond.example.com\n')
            filepath = handle.name

        try:
            actual = Filter.targets({'hostlist': filepath})
        finally:
            os.unlink(filepath)

        self.assertEqual(actual, [
            {'host': 'example.com', 'scheme': 'http://', 'ssl': False, 'source': 'example.com'},
            {'host': 'example.com', 'scheme': 'https://', 'ssl': True, 'source': 'https://example.com'},
            {'host': 'second.example.com', 'scheme': 'http://', 'ssl': False, 'source': 'second.example.com'},
        ])

    def test_targets_should_read_from_stdin(self):
        """Filter.targets() should read targets from STDIN."""

        with patch('src.core.options.filter.sys.stdin', io.StringIO('example.com\nsecond.example.com\n')):
            actual = Filter.targets({'stdin': True})

        self.assertEqual(actual, [
            {'host': 'example.com', 'scheme': 'http://', 'ssl': False, 'source': 'example.com'},
            {'host': 'second.example.com', 'scheme': 'http://', 'ssl': False, 'source': 'second.example.com'},
        ])

    def test_targets_should_expand_ipv4_cidr_from_hostlist(self):
        """Filter.targets() should expand IPv4 CIDR entries and deduplicate expanded targets."""

        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as handle:
            handle.write('192.168.1.0/30\n192.168.1.1\nhttps://example.com\n')
            filepath = handle.name

        try:
            actual = Filter.targets({'hostlist': filepath})
        finally:
            os.unlink(filepath)

        self.assertEqual(actual, [
            {'host': '192.168.1.1', 'scheme': 'http://', 'ssl': False, 'source': '192.168.1.1'},
            {'host': '192.168.1.2', 'scheme': 'http://', 'ssl': False, 'source': '192.168.1.2'},
            {'host': 'example.com', 'scheme': 'https://', 'ssl': True, 'source': 'https://example.com'},
        ])

    def test_targets_should_expand_ipv4_range_from_stdin(self):
        """Filter.targets() should expand inclusive IPv4 ranges from STDIN."""

        with patch('src.core.options.filter.sys.stdin', io.StringIO('192.168.1.10-192.168.1.12\n')):
            actual = Filter.targets({'stdin': True})

        self.assertEqual(actual, [
            {'host': '192.168.1.10', 'scheme': 'http://', 'ssl': False, 'source': '192.168.1.10'},
            {'host': '192.168.1.11', 'scheme': 'http://', 'ssl': False, 'source': '192.168.1.11'},
            {'host': '192.168.1.12', 'scheme': 'http://', 'ssl': False, 'source': '192.168.1.12'},
        ])

    def test_targets_should_reject_invalid_ipv4_expansions(self):
        """Filter.targets() should reject malformed CIDR and descending IPv4 ranges."""

        with self.assertRaises(FilterError):
            Filter.targets({'host': '192.168.1.0/33'})

        with self.assertRaises(FilterError):
            Filter.targets({'host': '192.168.1.10-192.168.1.1'})

        with self.assertRaises(FilterError):
            Filter.targets({'host': '999.168.1.1-999.168.1.2'})

    def test_target_expansion_helpers_should_guard_edge_cases(self):
        """Filter expansion helpers should cover IPv4 edge networks and safety limits."""

        self.assertEqual(Filter._expand_ipv4_cidr('192.168.1.9/32'), ['192.168.1.9'])
        self.assertEqual(Filter._expand_ipv4_cidr('192.168.1.10/31'), ['192.168.1.10', '192.168.1.11'])

        with self.assertRaises(FilterError):
            Filter._expand_ipv4_cidr('2001:db8::/126')

        with self.assertRaises(FilterError):
            Filter._expand_ipv4_range('2001:db8::1', '2001:db8::2')

        with self.assertRaises(FilterError):
            Filter._validate_target_expansion_size('empty', 0)

        with self.assertRaises(FilterError):
            Filter._validate_target_expansion_size('huge', Filter.TARGET_EXPANSION_LIMIT + 1)

    def test_targets_should_raise_for_missing_hostlist(self):
        """Filter.targets() should raise a FilterError when hostlist cannot be read."""

        with self.assertRaises(FilterError):
            Filter.targets({'hostlist': '/tmp/definitely-missing-opendoor-targets.txt'})


    def test_status_ranges_accept_exact_codes_and_ranges(self):
        """Filter.status_ranges() should normalize exact codes and inclusive ranges."""

        self.assertEqual(
            Filter.status_ranges('200-299,301,403', key='--include-status'),
            ['200-299', '301', '403']
        )

    def test_status_ranges_reject_invalid_codes(self):
        """Filter.status_ranges() should reject malformed or unsupported HTTP codes."""

        with self.assertRaises(FilterError):
            Filter.status_ranges('99,200', key='--include-status')

        with self.assertRaises(FilterError):
            Filter.status_ranges('500-400', key='--exclude-status')

    def test_integer_ranges_reject_invalid_ranges(self):
        """Filter.integer_ranges() should reject malformed or descending byte ranges."""

        with self.assertRaises(FilterError):
            Filter.integer_ranges('abc', key='--exclude-size-range')

        with self.assertRaises(FilterError):
            Filter.integer_ranges('128-64', key='--exclude-size-range')

    def test_regex_values_validate_patterns(self):
        """Filter.regex_values() should validate regex syntax before runtime."""

        self.assertEqual(Filter.regex_values(['(?i)admin'], key='--match-regex'), ['(?i)admin'])

        with self.assertRaises(FilterError):
            Filter.regex_values(['([unclosed'], key='--match-regex')

    def test_filter_rejects_invalid_response_length_bounds(self):
        """Filter.filter() should reject inverted min/max response length filters."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'min_response_length': 1024,
                'max_response_length': 64,
            })



    def test_filter_normalizes_response_filter_arguments(self):
        """Filter.filter() should normalize all response-filter option families."""

        actual = Filter.filter({
            'host': 'example.com',
            'include_status': '200-201,403',
            'exclude_status': '404,500-501',
            'exclude_size': '0, 12',
            'exclude_size_range': '1-8,10-20',
            'match_regex': ['(?i)admin'],
            'exclude_regex': ['(?i)forbidden'],
            'match_text': [' login ', '   '],
            'exclude_text': 'Not Found',
            'min_response_length': 10,
            'max_response_length': 100,
        })

        self.assertEqual(actual['include_status'], ['200-201', '403'])
        self.assertEqual(actual['exclude_status'], ['404', '500-501'])
        self.assertEqual(actual['exclude_size'], ['0', '12'])
        self.assertEqual(actual['exclude_size_range'], ['1-8', '10-20'])
        self.assertEqual(actual['match_regex'], ['(?i)admin'])
        self.assertEqual(actual['exclude_regex'], ['(?i)forbidden'])
        self.assertEqual(actual['match_text'], ['login'])
        self.assertEqual(actual['exclude_text'], ['Not Found'])
        self.assertEqual(actual['min_response_length'], 10)
        self.assertEqual(actual['max_response_length'], 100)

    def test_filter_keeps_empty_targets_out_of_single_target_projection(self):
        """Filter.filter() should not inject single-host keys when no targets are resolved."""

        with patch('src.core.options.filter.sys.stdin', io.StringIO('')):
            actual = Filter.filter({'stdin': True})

        self.assertNotIn('host', actual)
        self.assertNotIn('scheme', actual)
        self.assertNotIn('ssl', actual)
        self.assertNotIn('targets', actual)

    def test_targets_should_allow_explicit_none_target_cleanup(self):
        """Filter.targets() should ignore None values after cleaning raw target input."""

        with patch.object(Filter, '_read_target_stream', return_value=[None, 'example.com']):
            actual = Filter.targets({'stdin': True})

        self.assertEqual(actual, [
            {'host': 'example.com', 'scheme': 'http://', 'ssl': False, 'source': 'example.com'},
        ])

    def test_integer_and_text_helpers_cover_edge_paths(self):
        """Filter helper normalizers should handle empty and scalar values."""

        self.assertEqual(Filter.integer_values('001,2', key='--exclude-size'), ['1', '2'])
        self.assertEqual(Filter.integer_ranges('0-0', key='--exclude-size-range'), ['0-0'])
        self.assertEqual(Filter.text_values('  abc  '), ['abc'])
        self.assertEqual(Filter.text_values('   '), [])
        self.assertEqual(Filter.non_negative_int('0', key='--min-response-length'), 0)
        with self.assertRaises(FilterError):
            Filter.non_negative_int(None, key='--min-response-length')
        with self.assertRaises(FilterError):
            Filter.non_negative_int('-1', key='--min-response-length')

    def test_status_ranges_reject_upper_out_of_range_code(self):
        """Filter.status_ranges() should reject status codes above 599."""

        with self.assertRaises(FilterError):
            Filter.status_ranges('600', key='--include-status')


    def test_raw_request_should_parse_relative_request_with_scheme(self):
        """Filter.raw_request() should parse relative request files when scheme is provided."""

        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as handle:
            handle.write('POST /admin/login.php HTTP/1.1\nHost: example.com:8443\nUser-Agent: CustomUA\nCookie: sid=abc; theme=dark\nX-Test: 1\n\nusername=admin')
            filepath = handle.name

        try:
            actual = Filter.raw_request(filepath, scheme='https')
        finally:
            os.unlink(filepath)

        self.assertEqual(actual['method'], 'POST')
        self.assertEqual(actual['host'], 'example.com')
        self.assertEqual(actual['scheme'], 'https://')
        self.assertEqual(actual['port'], 8443)
        self.assertEqual(actual['prefix'], 'admin/')
        self.assertEqual(actual['cookies'], ['sid=abc', 'theme=dark'])
        self.assertEqual(actual['headers'], ['User-Agent: CustomUA', 'X-Test: 1'])
        self.assertEqual(actual['body'], 'username=admin')

    def test_filter_should_use_raw_request_target_when_host_not_provided(self):
        """Filter.filter() should resolve target data from raw-request files."""

        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as handle:
            handle.write('GET /api/v1/users HTTP/1.1\nHost: api.example.com\nX-Test: 1\n\n')
            filepath = handle.name

        try:
            actual = Filter.filter({'raw_request': filepath, 'scheme': 'https'})
        finally:
            os.unlink(filepath)

        self.assertEqual(actual['host'], 'api.example.com')
        self.assertEqual(actual['scheme'], 'https://')
        self.assertTrue(actual['ssl'])
        self.assertEqual(actual['method'], 'GET')
        self.assertEqual(actual['prefix'], 'api/v1/')
        self.assertEqual(actual['header'], ['X-Test: 1'])
        self.assertNotIn('port', actual['targets'][0])

    def test_filter_should_merge_raw_request_headers_and_cli_overrides(self):
        """Filter.filter() should merge raw-request values with CLI overrides."""

        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as handle:
            handle.write('POST /admin/login.php HTTP/1.1\nHost: example.com\nUser-Agent: RawUA\nCookie: sid=abc\nX-Test: 1\n\nusername=admin')
            filepath = handle.name

        try:
            actual = Filter.filter({
                'host': 'https://override.local',
                'raw_request': filepath,
                'header': ['User-Agent: CliUA'],
                'cookie': ['session=xyz'],
                'method': 'PUT',
                'prefix': 'forced/',
            })
        finally:
            os.unlink(filepath)

        self.assertEqual(actual['host'], 'override.local')
        self.assertEqual(actual['scheme'], 'https://')
        self.assertEqual(actual['method'], 'PUT')
        self.assertEqual(actual['prefix'], 'forced/')
        self.assertEqual(actual['header'], ['User-Agent: RawUA', 'X-Test: 1', 'User-Agent: CliUA'])
        self.assertEqual(actual['cookie'], ['sid=abc', 'session=xyz'])
        self.assertEqual(actual['request_body'], 'username=admin')

    def test_filter_should_require_scheme_for_relative_raw_request_target(self):
        """Filter.filter() should require --scheme when raw-request uses a relative path as the target source."""

        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as handle:
            handle.write('GET /admin HTTP/1.1\nHost: example.com\n\n')
            filepath = handle.name

        try:
            with self.assertRaises(FilterError):
                Filter.filter({'raw_request': filepath})
        finally:
            os.unlink(filepath)

    def test_filter_should_accept_absolute_raw_request_without_scheme(self):
        """Filter.filter() should infer scheme and host from absolute raw-request URLs."""

        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as handle:
            handle.write('GET https://secure.example.com:9443/api/v2/items HTTP/1.1\nUser-Agent: RawUA\n\n')
            filepath = handle.name

        try:
            actual = Filter.filter({'raw_request': filepath})
        finally:
            os.unlink(filepath)

        self.assertEqual(actual['host'], 'secure.example.com')
        self.assertEqual(actual['scheme'], 'https://')
        self.assertTrue(actual['ssl'])
        self.assertEqual(actual['port'], 9443)
        self.assertEqual(actual['prefix'], 'api/v2/')

    def test_explicit_scheme_handles_blank_and_invalid_values(self):
        """Filter.explicit_scheme() should accept blanks and reject unsupported schemes."""

        self.assertIsNone(Filter.explicit_scheme('   ', key='--scheme'))

        with self.assertRaises(FilterError):
            Filter.explicit_scheme('ftp', key='--scheme')

    def test_raw_request_should_raise_for_missing_file(self):
        """Filter.raw_request() should wrap file read failures."""

        with self.assertRaises(FilterError):
            Filter.raw_request('/tmp/definitely-missing-opendoor-request.txt', scheme='https')

    def test_parse_raw_request_should_reject_empty_payload(self):
        """Filter._parse_raw_request() should reject empty request files."""

        with self.assertRaises(FilterError):
            Filter._parse_raw_request('', scheme='https')

    def test_parse_raw_request_should_reject_invalid_request_line(self):
        """Filter._parse_raw_request() should reject malformed request lines."""

        with self.assertRaises(FilterError):
            Filter._parse_raw_request('BROKEN\nHost: example.com\n\n', scheme='https')

    def test_parse_raw_request_should_reject_invalid_header_lines(self):
        """Filter._parse_raw_request() should reject malformed headers."""

        with self.assertRaises(FilterError):
            Filter._parse_raw_request(
                'GET / HTTP/1.1\nHost: example.com\nBrokenHeader\n\n',
                scheme='https'
            )

        with self.assertRaises(FilterError):
            Filter._parse_raw_request(
                'GET / HTTP/1.1\nHost: example.com\n: empty-key\n\n',
                scheme='https'
            )

    def test_parse_raw_request_should_skip_content_length_and_keep_query_string(self):
        """Filter._parse_raw_request() should ignore Content-Length and preserve query strings."""

        actual = Filter._parse_raw_request(
            'GET https://example.com/api/items?x=1 HTTP/1.1\n'
            'Content-Length: 999\n'
            'X-Test: 1\n\n',
            scheme=None
        )

        self.assertEqual(actual['scheme'], 'https://')
        self.assertEqual(actual['host'], 'example.com')
        self.assertEqual(actual['path'], '/api/items?x=1')
        self.assertEqual(actual['prefix'], 'api/')
        self.assertEqual(actual['headers'], ['X-Test: 1'])

    def test_parse_raw_request_can_remain_unresolved_without_host_and_scheme(self):
        """Filter._parse_raw_request() should keep unresolved target fields when host cannot be inferred."""

        actual = Filter._parse_raw_request('GET /health HTTP/1.1\n\n', scheme=None)

        self.assertIsNone(actual['host'])
        self.assertIsNone(actual['scheme'])
        self.assertEqual(actual['path'], '/health')
        self.assertEqual(actual['prefix'], '')

    def test_filter_should_raise_when_raw_request_cannot_resolve_target(self):
        """Filter.filter() should fail when raw-request exists but target cannot be resolved."""

        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as handle:
            handle.write('GET /admin HTTP/1.1\nX-Test: 1\n\n')
            filepath = handle.name

        try:
            with self.assertRaises(FilterError):
                Filter.filter({
                    'raw_request': filepath,
                    'scheme': 'https',
                })
        finally:
            os.unlink(filepath)

    def test_raw_request_helper_paths_cover_edge_cases(self):
        """Filter raw-request helpers should cover root paths, directory paths and non-digit ports."""

        self.assertEqual(Filter._raw_request_prefix('/'), '')
        self.assertEqual(Filter._raw_request_prefix('/admin/'), 'admin/')
        self.assertEqual(Filter._split_host_and_port('example.com:abc'), ('example.com:abc', None))
        self.assertIsNone(Filter._raw_request_target_source(None, 'https://', 443))

    def test_status_integer_and_csv_helpers_cover_remaining_edge_paths(self):
        """Filter helper validators should reject invalid ranges and normalize CSV list inputs."""

        with self.assertRaises(FilterError):
            Filter.status_ranges('100-600', key='--include-status')

        with self.assertRaises(FilterError):
            Filter.integer_values('1,abc', key='--exclude-size')

        self.assertEqual(Filter._split_csv(None), [])
        self.assertEqual(Filter._split_csv(['1,2', '3']), ['1', '2', '3'])

    def test_filter_rejects_session_load_with_host_sources(self):
        """Filter.filter() should reject session-load mixed with direct target sources."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'session_load': 'session.json',
                'host': 'http://example.com',
            })

    def test_filter_accepts_session_load_only_mode(self):
        """Filter.filter() should normalize session-load mode without target resolution."""

        actual = Filter.filter({
            'session_load': 'session.json',
            'session_autosave_sec': 10,
            'session_autosave_items': 50,
        })

        self.assertTrue(actual['session_load'].endswith('session.json'))
        self.assertEqual(actual['session_autosave_sec'], 10)
        self.assertEqual(actual['session_autosave_items'], 50)

    def test_session_file_and_positive_int_helpers_cover_error_paths(self):
        """Filter session helpers should validate empty paths and non-positive thresholds."""

        with self.assertRaises(FilterError):
            Filter.session_file('   ', key='--session-save')

        with self.assertRaises(FilterError):
            Filter.positive_int(0, key='--session-autosave-sec')

        with self.assertRaises(FilterError):
            Filter.positive_int('x', key='--session-autosave-items')

    def test_session_helpers_reject_invalid_inputs(self):
        """Filter session helper validators should reject empty paths and non-positive thresholds."""

        with self.assertRaises(FilterError):
            Filter.session_file('   ', key='--session-save')

        with self.assertRaises(FilterError):
            Filter.positive_int(0, key='--session-autosave-sec')

        with self.assertRaises(FilterError):
            Filter.positive_int('bad', key='--session-autosave-items')

    def test_bucket_values_should_normalize_ci_fail_on_buckets(self):
        """Filter.bucket_values() should normalize fail-on bucket names."""

        self.assertEqual(
            Filter.bucket_values('success, AUTH,blocked,success', key='--fail-on-bucket'),
            ['success', 'auth', 'blocked']
        )

    def test_bucket_values_should_reject_invalid_ci_fail_on_buckets(self):
        """Filter.bucket_values() should reject malformed bucket names."""

        with self.assertRaises(FilterError):
            Filter.bucket_values('success,403', key='--fail-on-bucket')

        with self.assertRaises(FilterError):
            Filter.bucket_values('success,bad bucket', key='--fail-on-bucket')

    def test_filter_should_normalize_fail_on_bucket_in_normal_flow(self):
        """Filter.filter() should normalize fail-on bucket names in normal scan mode."""

        actual = Filter.filter({
            'host': 'example.com',
            'fail_on_bucket': 'success, blocked,success',
        })

        self.assertEqual(actual['fail_on_bucket'], ['success', 'blocked'])

    def test_filter_should_keep_raw_request_without_headers_unmerged(self):
        """Filter.filter() should skip raw-request header merge when no headers are present."""

        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as handle:
            handle.write('GET https://secure.example.com/api/v1/users HTTP/1.1\n\n')
            filepath = handle.name

        try:
            actual = Filter.filter({'raw_request': filepath})
        finally:
            os.unlink(filepath)

        self.assertEqual(actual['host'], 'secure.example.com')
        self.assertEqual(actual['scheme'], 'https://')
        self.assertNotIn('header', actual)
        self.assertNotIn('cookie', actual)

    def test_filter_header_bypass_profile_should_default_empty_values_to_safe(self):
        """Filter.header_bypass_profile() should normalize blank and null-like values to safe."""

        self.assertEqual(Filter.header_bypass_profile(''), 'safe')
        self.assertEqual(Filter.header_bypass_profile(' null '), 'safe')
        self.assertEqual(Filter.header_bypass_profile(None), 'safe')

    def test_bucket_values_should_ignore_empty_items_and_reject_empty_lists(self):
        """Filter.bucket_values() should skip empty CSV items and reject empty results."""

        self.assertEqual(Filter.bucket_values('success,, blocked,'), ['success', 'blocked'])

        with self.assertRaises(FilterError):
            Filter.bucket_values(' , , ', key='--fail-on-bucket')

    def test_debug_and_session_helpers_should_cover_remaining_error_paths(self):
        """Filter helpers should reject invalid debug levels and missing session paths."""

        with self.assertRaises(FilterError):
            Filter.debug_level(4, key='--debug')

        with self.assertRaises(FilterError):
            Filter.session_file(None, key='--session-file')

    def test_filter_should_reject_transport_profiles_without_rotation_when_profile_exists(self):
        """Filter.filter() should reject profiles lists unless per-target rotation is enabled."""

        with self.assertRaises(FilterError) as ctx:
            Filter.filter({
                'host': 'example.com',
                'transport': 'wireguard',
                'transport_profile': './vpn/nl.conf',
                'transport_profiles': './vpn/profiles.txt',
            })

        self.assertIn('--transport-profiles requires --transport-rotate per-target', str(ctx.exception))

    def test_filter_should_keep_fail_on_bucket_with_session_load(self):
        """Filter.filter() should preserve invocation-level CI policy for session resume."""

        actual = Filter.filter({
            'session_load': '/tmp/session.json',
            'fail_on_bucket': 'blocked,forbidden',
        })

        self.assertEqual(actual['session_load'], '/tmp/session.json')
        self.assertEqual(actual['fail_on_bucket'], ['blocked', 'forbidden'])

    def test_ratio_float_should_accept_valid_calibration_threshold(self):
        """Filter.ratio_float() should accept valid calibration thresholds."""

        self.assertEqual(Filter.ratio_float('0.92', key='--calibration-threshold'), 0.92)
        self.assertEqual(Filter.ratio_float(1, key='--calibration-threshold'), 1.0)

    def test_ratio_float_should_reject_invalid_calibration_threshold(self):
        """Filter.ratio_float() should reject invalid calibration thresholds."""

        with self.assertRaises(FilterError):
            Filter.ratio_float(0, key='--calibration-threshold')

        with self.assertRaises(FilterError):
            Filter.ratio_float(1.1, key='--calibration-threshold')

        with self.assertRaises(FilterError):
            Filter.ratio_float('bad', key='--calibration-threshold')

    def test_filter_should_normalize_auto_calibration_options(self):
        """Filter.filter() should normalize auto-calibration options."""

        actual = Filter.filter({
            'host': 'example.com',
            'auto_calibrate': True,
            'calibration_samples': 7,
            'calibration_threshold': 0.91,
        })

        self.assertTrue(actual['auto_calibrate'])
        self.assertEqual(actual['calibration_samples'], 7)
        self.assertEqual(actual['calibration_threshold'], 0.91)

    def test_filter_should_keep_auto_calibration_options_with_session_load(self):
        """Filter.filter() should preserve invocation-level auto-calibration options for session resume."""

        actual = Filter.filter({
            'session_load': '/tmp/session.json',
            'auto_calibrate': True,
            'calibration_samples': 9,
            'calibration_threshold': 0.93,
        })

        self.assertEqual(actual['session_load'], '/tmp/session.json')
        self.assertTrue(actual['auto_calibrate'])
        self.assertEqual(actual['calibration_samples'], 9)
        self.assertEqual(actual['calibration_threshold'], 0.93)

    def test_filter_should_normalize_transport_options(self):
        """Filter.filter() should normalize network transport options."""

        actual = Filter.filter({
            'host': 'example.com',
            'transport': 'wireguard',
            'transport_profile': './profiles/nl.conf',
            'transport_rotate': 'none',
            'transport_timeout': 15,
            'transport_healthcheck_url': 'https://example.com/ip',
            'transport_bin': 'wg-quick',
        })

        self.assertEqual(actual['transport'], 'wireguard')
        self.assertTrue(actual['transport_profile'].endswith('profiles/nl.conf'))
        self.assertEqual(actual['transport_rotate'], 'none')
        self.assertEqual(actual['transport_timeout'], 15)
        self.assertEqual(actual['transport_bin'], 'wg-quick')
        self.assertEqual(actual['transport_healthcheck_url'], 'https://example.com/ip')

    def test_filter_should_normalize_transport_none_values(self):
        """Filter should normalize empty transport values to defaults."""

        self.assertEqual(Filter.transport(None), 'direct')
        self.assertEqual(Filter.transport('None'), 'direct')
        self.assertEqual(Filter.transport_rotate(None), 'none')
        self.assertIsNone(Filter.optional_text('None'))
        self.assertIsNone(Filter.optional_path('None'))

    def test_filter_should_reject_invalid_transport(self):
        """Filter.filter() should reject unsupported network transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'vpn',
            })

    def test_filter_should_reject_invalid_transport_rotate(self):
        """Filter.filter() should reject unsupported transport rotation mode."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport_rotate': 'per-request',
            })

    def test_filter_should_reject_profile_for_direct_transport(self):
        """Filter.filter() should reject transport profile for direct transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'direct',
                'transport_profile': './vpn/nl.conf',
            })

    def test_filter_should_reject_per_target_rotate_for_direct_transport(self):
        """Filter.filter() should reject per-target rotation for direct transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'direct',
                'transport_rotate': 'per-target',
            })

    def test_filter_should_allow_proxy_layer_with_vpn_transport(self):
        """Filter.filter() should allow existing proxy layer together with VPN transport."""

        actual = Filter.filter({
            'host': 'example.com',
            'proxy': 'http://127.0.0.1:8080',
            'transport': 'openvpn',
            'transport_profile': './vpn/nl.ovpn',
        })

        self.assertEqual(actual['proxy'], 'http://127.0.0.1:8080')
        self.assertEqual(actual['transport'], 'openvpn')
        self.assertTrue(actual['transport_profile'].endswith('vpn/nl.ovpn'))

    def test_filter_should_reject_per_target_rotate_for_proxy_transport(self):
        """Filter.filter() should reject per-target rotation for proxy transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'proxy',
                'transport_rotate': 'per-target',
            })

    def test_filter_should_require_openvpn_profile(self):
        """Filter.filter() should require profile for openvpn transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'openvpn',
            })

    def test_filter_should_reject_conf_profile_for_openvpn(self):
        """Filter.filter() should reject .conf profile for openvpn transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'openvpn',
                'transport_profile': './vpn/nl.conf',
            })

    def test_filter_should_reject_ovpn_profile_for_wireguard(self):
        """Filter.filter() should reject .ovpn profile for wireguard transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'wireguard',
                'transport_profile': './vpn/nl.ovpn',
            })

    def test_filter_should_require_profiles_for_per_target_rotation(self):
        """Filter.filter() should require transport profiles list for per-target rotation."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'wireguard',
                'transport_profile': './vpn/nl.conf',
                'transport_rotate': 'per-target',
            })

    def test_filter_should_accept_profiles_for_per_target_rotation(self):
        """Filter.filter() should accept transport profiles list for per-target rotation."""

        actual = Filter.filter({
            'host': 'example.com',
            'transport': 'wireguard',
            'transport_profiles': './vpn/profiles.txt',
            'transport_rotate': 'per-target',
        })

        self.assertEqual(actual['transport'], 'wireguard')
        self.assertTrue(actual['transport_profiles'].endswith('vpn/profiles.txt'))
        self.assertEqual(actual['transport_rotate'], 'per-target')

    def test_filter_should_reject_profile_and_profiles_combination_for_rotation(self):
        """Filter.filter() should reject single profile when per-target rotation is used."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'wireguard',
                'transport_profile': './vpn/nl.conf',
                'transport_profiles': './vpn/profiles.txt',
                'transport_rotate': 'per-target',
            })

    def test_filter_should_reject_profiles_without_rotation(self):
        """Filter.filter() should reject transport profiles list without per-target rotation."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'wireguard',
                'transport_profiles': './vpn/profiles.txt',
            })

    def test_filter_should_reject_openvpn_auth_for_wireguard(self):
        """Filter.filter() should reject OpenVPN auth for WireGuard transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'wireguard',
                'transport_profile': './vpn/nl.conf',
                'openvpn_auth': './auth.txt',
            })

    def test_filter_should_keep_transport_options_with_session_load(self):
        """Filter.filter() should preserve invocation-level transport options for session resume."""

        actual = Filter.filter({
            'session_load': '/tmp/session.json',
            'transport': 'openvpn',
            'transport_profile': './vpn/nl.ovpn',
            'transport_timeout': 20,
            'transport_healthcheck_url': 'https://example.com/ip',
            'openvpn_auth': './auth.txt',
        })

        self.assertEqual(actual['session_load'], '/tmp/session.json')
        self.assertEqual(actual['transport'], 'openvpn')
        self.assertTrue(actual['transport_profile'].endswith('vpn/nl.ovpn'))
        self.assertEqual(actual['transport_timeout'], 20)
        self.assertEqual(actual['transport_healthcheck_url'], 'https://example.com/ip')
        self.assertTrue(actual['openvpn_auth'].endswith('auth.txt'))

    def test_filter_should_reject_session_load_with_raw_request(self):
        """Filter.filter() should reject session-load mixed with raw request."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'session_load': '/tmp/session.json',
                'raw_request': '/tmp/request.txt',
            })

    def test_filter_should_reject_session_load_with_hostlist_or_stdin(self):
        """Filter.filter() should reject session-load mixed with hostlist or stdin target sources."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'session_load': '/tmp/session.json',
                'hostlist': '/tmp/targets.txt',
            })

        with self.assertRaises(FilterError):
            Filter.filter({
                'session_load': '/tmp/session.json',
                'stdin': True,
            })

    def test_filter_should_keep_transport_profiles_rotation_with_session_load(self):
        """Filter.filter() should preserve per-target transport rotation options for session resume."""

        actual = Filter.filter({
            'session_load': '/tmp/session.json',
            'transport': 'wireguard',
            'transport_profiles': './vpn/profiles.txt',
            'transport_rotate': 'per-target',
            'transport_timeout': 25,
            'transport_healthcheck_url': 'https://example.com/ip',
        })

        self.assertEqual(actual['session_load'], '/tmp/session.json')
        self.assertEqual(actual['transport'], 'wireguard')
        self.assertTrue(actual['transport_profiles'].endswith('vpn/profiles.txt'))
        self.assertEqual(actual['transport_rotate'], 'per-target')
        self.assertEqual(actual['transport_timeout'], 25)
        self.assertEqual(actual['transport_healthcheck_url'], 'https://example.com/ip')

    def test_filter_should_keep_openvpn_auth_with_session_load(self):
        """Filter.filter() should preserve OpenVPN auth option for session resume."""

        actual = Filter.filter({
            'session_load': '/tmp/session.json',
            'transport': 'openvpn',
            'transport_profile': './vpn/nl.ovpn',
            'transport_rotate': 'none',
            'openvpn_auth': './vpn/auth.txt',
        })

        self.assertEqual(actual['transport'], 'openvpn')
        self.assertTrue(actual['transport_profile'].endswith('vpn/nl.ovpn'))
        self.assertEqual(actual['transport_rotate'], 'none')
        self.assertTrue(actual['openvpn_auth'].endswith('vpn/auth.txt'))

    def test_filter_should_normalize_stdin_targets_in_full_filter_flow(self):
        """Filter.filter() should normalize stdin targets in the full filter flow."""

        with patch('src.core.options.filter.sys.stdin', io.StringIO('example.com\nhttps://secure.example.com\n')):
            actual = Filter.filter({
                'stdin': True,
                'reports': 'std',
            })

        self.assertEqual(actual['targets'], [
            {'host': 'example.com', 'scheme': 'http://', 'ssl': False, 'source': 'example.com'},
            {'host': 'secure.example.com', 'scheme': 'https://', 'ssl': True, 'source': 'https://secure.example.com'},
        ])
        self.assertEqual(actual['transport'], 'direct')
        self.assertEqual(actual['transport_rotate'], 'none')

    def test_filter_should_normalize_session_save_and_scan_arguments(self):
        """Filter.filter() should normalize session save and scan options in normal flow."""

        actual = Filter.filter({
            'host': 'example.com',
            'session_save': './sessions/run.json',
            'session_autosave_sec': 15,
            'session_autosave_items': 100,
            'scan': 'subdomains',
        })

        self.assertEqual(actual['scan'], 'subdomains')
        self.assertTrue(actual['session_save'].endswith('sessions/run.json'))
        self.assertEqual(actual['session_autosave_sec'], 15)
        self.assertEqual(actual['session_autosave_items'], 100)

    def test_filter_should_reject_direct_transport_with_profiles_or_auth(self):
        """Filter.filter() should reject profiles and OpenVPN auth for direct transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'direct',
                'transport_profiles': './vpn/profiles.txt',
            })

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'direct',
                'openvpn_auth': './vpn/auth.txt',
            })


    def test_filter_should_require_proxy_source_for_proxy_transport(self):
        """Filter.filter() should reject proxy transport without a proxy source."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'proxy',
            })

    def test_filter_should_reject_transport_profile_for_proxy_transport(self):
        """Filter.filter() should reject VPN profile options for proxy transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'proxy',
                'proxy': 'http://127.0.0.1:8080',
                'transport_profile': './vpn/nl.conf',
            })

    def test_filter_should_accept_proxy_transport_with_proxy_source(self):
        """Filter.filter() should accept proxy transport with explicit proxy source."""

        actual = Filter.filter({
            'host': 'example.com',
            'transport': 'proxy',
            'proxy': 'http://127.0.0.1:8080',
        })

        self.assertEqual(actual['transport'], 'proxy')
        self.assertEqual(actual['proxy'], 'http://127.0.0.1:8080')

    def test_filter_should_reject_proxy_transport_with_openvpn_auth(self):
        """Filter.filter() should reject OpenVPN auth for proxy transport."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'transport': 'proxy',
                'openvpn_auth': './vpn/auth.txt',
            })

    def test_filter_should_accept_valid_transport_profile_extensions(self):
        """Filter.validate_transport_profile_extension() should accept valid VPN profile extensions."""

        self.assertIsNone(
            Filter.validate_transport_profile_extension(
                'openvpn',
                './vpn/nl.ovpn',
                key='--transport-profile'
            )
        )
        self.assertIsNone(
            Filter.validate_transport_profile_extension(
                'wireguard',
                './vpn/nl.conf',
                key='--transport-profile'
            )
        )

    def test_filter_should_allow_registered_non_vpn_transport_without_vpn_profile_rules(self):
        """Filter.validate_transport_options() should allow future registered non-VPN transports."""

        payload = {
            'transport': 'container',
            'transport_profile': './profiles/container.json',
            'transport_rotate': 'none',
        }

        with patch.object(Filter, 'TRANSPORTS', Filter.TRANSPORTS + ('container',)):
            Filter.validate_transport_options(payload)

        self.assertEqual(payload['transport'], 'container')
        self.assertEqual(payload['transport_rotate'], 'none')
        self.assertEqual(payload['transport_profile'], './profiles/container.json')

    def test_filter_optional_helpers_should_cover_empty_and_null_values(self):
        """Filter optional helpers should normalize empty and null-like values."""

        self.assertIsNone(Filter.optional_text(''))
        self.assertIsNone(Filter.optional_text('   '))
        self.assertIsNone(Filter.optional_text('null'))
        self.assertIsNone(Filter.optional_path(None))
        self.assertIsNone(Filter.optional_path('None'))

    def test_filter_transport_rotate_should_normalize_empty_values(self):
        """Filter.transport_rotate() should normalize empty and null-like values to none."""

        self.assertEqual(Filter.transport_rotate(''), 'none')
        self.assertEqual(Filter.transport_rotate('null'), 'none')
        self.assertEqual(Filter.transport_rotate('NONE'), 'none')

    def test_filter_should_reject_transport_bin_for_direct_transport(self):
        """Filter.validate_transport_options() should reject transport_bin in direct mode."""

        with self.assertRaises(Exception) as ctx:
            Filter.filter({
                'host': 'example.com',
                'transport': 'direct',
                'transport_bin': 'openvpn',
            })

        self.assertIn('--transport-bin cannot be used with --transport direct', str(ctx.exception))

    def test_filter_should_reject_transport_bin_for_proxy_transport(self):
        """Filter.validate_transport_options() should reject transport_bin in proxy mode."""

        with self.assertRaises(Exception) as ctx:
            Filter.filter({
                'host': 'example.com',
                'transport': 'proxy',
                'proxy': 'socks5://127.0.0.1:9050',
                'transport_bin': 'openvpn',
            })

        self.assertIn('--transport-bin cannot be used with --transport proxy', str(ctx.exception))

    def test_filter_should_reject_invalid_transport_options_with_session_load(self):
        """Filter.filter() should validate transport options in session-load flow."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'session_load': '/tmp/session.json',
                'transport': 'wireguard',
                'transport_profile': './vpn/nl.ovpn',
            })

        with self.assertRaises(FilterError):
            Filter.filter({
                'session_load': '/tmp/session.json',
                'transport': 'proxy',
                'transport_rotate': 'per-target',
            })

    def test_filter_should_preserve_session_load_debug_fail_bucket_and_transport_bin(self):
        """Filter.filter() should preserve invocation-only flags in session-load flow."""

        actual = Filter.filter({
            'session_load': 'session.json',
            'debug': '2',
            'fail_on_bucket': ' success,blocked ',
            'transport': 'wireguard',
            'transport_profile': './vpn/nl.conf',
            'transport_bin': 'wg-quick',
        })

        self.assertEqual(actual['debug'], 2)
        self.assertEqual(actual['fail_on_bucket'], ['success', 'blocked'])
        self.assertEqual(actual['transport_bin'], 'wg-quick')
        self.assertTrue(actual['transport_profile'].endswith('vpn/nl.conf'))

    def test_filter_helpers_should_cover_empty_bucket_debug_and_session_path_errors(self):
        """Filter helper validators should cover empty bucket and missing value branches."""

        with self.assertRaises(FilterError):
            Filter.bucket_values(' , , ', key='--fail-on-bucket')

        with self.assertRaises(FilterError):
            Filter.debug_level(None, key='--debug')

        with self.assertRaises(FilterError):
            Filter.session_file(None, key='--session-save')

    def test_filter_rejects_extensions_and_ignore_extensions_together(self):
        """Filter.filter() should reject conflicting extension filters."""

        with self.assertRaisesRegex(FilterError, '--extensions and --ignore-extensions cannot be used together'):
            Filter.filter({
                'host': 'example.com',
                'extensions': 'php,json',
                'ignore_extensions': 'asp,jsp',
            })

    def test_filter_allows_single_extension_filter_mode(self):
        """Filter.filter() should allow either extension filter by itself."""

        with_extensions = Filter.filter({
            'host': 'example.com',
            'extensions': 'php,json',
        })
        with_ignore_extensions = Filter.filter({
            'host': 'example.com',
            'ignore_extensions': 'asp,jsp',
        })

        self.assertEqual(with_extensions['extensions'], 'php,json')
        self.assertEqual(with_ignore_extensions['ignore_extensions'], 'asp,jsp')

    def test_filter_should_reject_proxy_transport_profiles(self):
        """Filter.validate_transport_options() should reject profile lists in proxy mode."""

        with self.assertRaises(FilterError) as ctx:
            Filter.filter({
                'host': 'example.com',
                'transport': 'proxy',
                'proxy': 'http://127.0.0.1:8080',
                'transport_profiles': './vpn/profiles.txt',
            })

        self.assertIn('--transport-profiles cannot be used with --transport proxy', str(ctx.exception))


    def test_filter_accepts_diff_mode_with_std_and_json_reports(self):
        """Filter.filter() should normalize diff mode without scan targets."""

        actual = Filter.filter({
            'diff': 'old.sqlite:new.sqlite',
            'reports': 'std,json,json',
            'reports_dir': ['/tmp/reports'],
            'debug': 0,
        })

        self.assertEqual(actual, {
            'diff': 'old.sqlite:new.sqlite',
            'reports': 'std,json',
            'reports_dir': '/tmp/reports',
            'debug': 0,
        })

    def test_filter_rejects_diff_output_reports_outside_std_and_json(self):
        """Filter.filter() should reject unsupported diff output reports."""

        with self.assertRaisesRegex(FilterError, 'supports only'):
            Filter.filter({'diff': 'old.sqlite:new.sqlite', 'reports': 'html'})

    def test_filter_rejects_diff_with_scan_targets(self):
        """Filter.filter() should keep diff mode isolated from scan target options."""

        with self.assertRaisesRegex(FilterError, 'cannot be used together'):
            Filter.filter({'diff': 'old.sqlite:new.sqlite', 'host': 'example.com'})

    def test_diff_reports_requires_at_least_one_supported_report(self):
        """Filter.diff_reports() should reject empty report selections."""

        with self.assertRaisesRegex(FilterError, 'requires at least one report'):
            Filter.diff_reports('')


if __name__ == '__main__':
    unittest.main()
