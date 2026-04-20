# -*- coding: utf-8 -*-

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

    def test_proxy_accepts_supported_schemes(self):
        """Filter.proxy() should accept supported proxy schemes with a port."""

        self.assertEqual(Filter.proxy('http://127.0.0.1:8080'), 'http://127.0.0.1:8080')
        self.assertEqual(Filter.proxy('socks5://127.0.0.1:9050'), 'socks5://127.0.0.1:9050')
        self.assertEqual(Filter.proxy('socks://127.0.0.1:9050'), 'socks5://127.0.0.1:9050')

if __name__ == '__main__':
    unittest.main()