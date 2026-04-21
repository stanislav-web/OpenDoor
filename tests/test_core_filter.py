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

        self.assertEqual(Filter.proxy('http://127.0.0.1:8080'), 'http://127.0.0.1:8080')
        self.assertEqual(Filter.proxy('socks5://127.0.0.1:9050'), 'socks5://127.0.0.1:9050')

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

if __name__ == '__main__':
    unittest.main()
