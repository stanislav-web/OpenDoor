# -*- coding: utf-8 -*-

import sys
import unittest
from argparse import Namespace
from unittest.mock import patch

from src.core.options import Options
from src.core.options.exceptions import FilterError
from src.core.options.filter import Filter


class TestOptionsHeaderBypass(unittest.TestCase):
    """Header injection bypass CLI option tests."""

    def make_options(self, namespace=None):
        """Create an Options instance without calling __init__."""

        option = Options.__new__(Options)
        setattr(option, '_Options__standalone', ['version', 'update', 'examples', 'docs'])
        setattr(option, 'args', namespace)
        return option

    def test_init_should_parse_header_bypass_arguments(self):
        """Options.__init__() should parse all header-bypass flags."""

        argv = [
            'opendoor.py',
            '--host',
            'example.com',
            '--header-bypass',
            '--header-bypass-profile',
            'offensive',
            '--header-bypass-headers',
            'X-Original-URL,X-Forwarded-For',
            '--header-bypass-ips',
            '127.0.0.1,10.0.0.1',
            '--header-bypass-status',
            '401,403-404',
            '--header-bypass-limit',
            '0',
        ]

        with patch.object(sys, 'argv', argv):
            option = Options()

        self.assertTrue(option.args.header_bypass)
        self.assertEqual(option.args.header_bypass_profile, 'offensive')
        self.assertEqual(option.args.header_bypass_headers, 'X-Original-URL,X-Forwarded-For')
        self.assertEqual(option.args.header_bypass_ips, '127.0.0.1,10.0.0.1')
        self.assertEqual(option.args.header_bypass_status, '401,403-404')
        self.assertEqual(option.args.header_bypass_limit, 0)

    def test_get_arg_values_should_preserve_header_bypass_arguments(self):
        """Options.get_arg_values() should pass header-bypass arguments through Filter.filter()."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            header_bypass=True,
            header_bypass_profile='offensive',
            header_bypass_headers='X-Original-URL,X-Forwarded-For',
            header_bypass_ips='127.0.0.1,10.0.0.1',
            header_bypass_status='401,403-404',
            header_bypass_limit=0,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
            raw_request=None,
            session_load=None,
        )
        option = self.make_options(namespace)

        filtered = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'header_bypass': True,
            'header_bypass_profile': 'offensive',
            'header_bypass_headers': ['X-Original-URL', 'X-Forwarded-For'],
            'header_bypass_ips': ['127.0.0.1', '10.0.0.1'],
            'header_bypass_status': ['401', '403-404'],
            'header_bypass_limit': 0,
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({
            'host': 'example.com',
            'header_bypass': True,
            'header_bypass_profile': 'offensive',
            'header_bypass_headers': 'X-Original-URL,X-Forwarded-For',
            'header_bypass_ips': '127.0.0.1,10.0.0.1',
            'header_bypass_status': '401,403-404',
            'header_bypass_limit': 0,
        })

    def test_filter_should_normalize_header_bypass_arguments(self):
        """Filter.filter() should normalize and validate header-bypass arguments."""

        actual = Filter.filter({
            'host': 'example.com',
            'header_bypass': True,
            'header_bypass_profile': 'offensive',
            'header_bypass_headers': ' X-Original-URL, X-Forwarded-For ,x-forwarded-for ',
            'header_bypass_ips': ' 127.0.0.1, localhost,127.0.0.1 ',
            'header_bypass_status': '401,403-404',
            'header_bypass_limit': 0,
        })

        self.assertTrue(actual['header_bypass'])
        self.assertEqual(actual['header_bypass_profile'], 'offensive')
        self.assertEqual(actual['header_bypass_headers'], ['X-Original-URL', 'X-Forwarded-For'])
        self.assertEqual(actual['header_bypass_ips'], ['127.0.0.1', 'localhost'])
        self.assertEqual(actual['header_bypass_status'], ['401', '403-404'])
        self.assertEqual(actual['header_bypass_limit'], 0)
        self.assertEqual(actual['host'], 'example.com')
        self.assertEqual(actual['scheme'], 'http://')
        self.assertFalse(actual['ssl'])

    def test_filter_should_reject_invalid_header_bypass_header_names(self):
        """Filter.filter() should reject invalid header names before runtime."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'header_bypass_headers': 'X-Original-URL,Bad:Header',
            })

    def test_filter_should_reject_header_bypass_response_splitting_values(self):
        """Filter.filter() should reject CRLF values for trusted IP/header values."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'header_bypass_ips': ['127.0.0.1\r\nX-Test: 1'],
            })

    def test_filter_should_reject_invalid_header_bypass_status(self):
        """Filter.filter() should validate status codes used by header bypass."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'header_bypass_status': '99,403',
            })

    def test_filter_should_reject_negative_header_bypass_limit(self):
        """Filter.filter() should allow zero but reject negative probe limits."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'header_bypass_limit': -1,
            })

    def test_filter_should_reject_invalid_header_bypass_profile(self):
        """Filter.filter() should validate header-bypass profile names."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'header_bypass_profile': 'aggressive',
            })

    def test_filter_should_preserve_header_bypass_options_for_session_resume(self):
        """Filter.filter() should allow header-bypass tuning when resuming sessions."""

        actual = Filter.filter({
            'session_load': 'sessions/scan.json',
            'header_bypass': True,
            'header_bypass_profile': 'offensive',
            'header_bypass_headers': 'X-Original-URL,X-Real-IP',
            'header_bypass_ips': '127.0.0.1',
            'header_bypass_status': '401,403',
            'header_bypass_limit': 8,
        })

        self.assertTrue(actual['header_bypass'])
        self.assertEqual(actual['header_bypass_profile'], 'offensive')
        self.assertEqual(actual['header_bypass_headers'], ['X-Original-URL', 'X-Real-IP'])
        self.assertEqual(actual['header_bypass_ips'], ['127.0.0.1'])
        self.assertEqual(actual['header_bypass_status'], ['401', '403'])
        self.assertEqual(actual['header_bypass_limit'], 8)
        self.assertTrue(actual['session_load'].endswith('sessions/scan.json'))

    def test_filter_header_names_should_split_lists_deduplicate_and_keep_first_case(self):
        """Header name validator should split list values and deduplicate case-insensitively."""

        actual = Filter.header_names(
            [' X-Real-IP, x-real-ip ', ' X-Original-URL '],
            key='--header-bypass-headers'
        )

        self.assertEqual(actual, ['X-Real-IP', 'X-Original-URL'])

    def test_filter_header_names_should_reject_empty_values(self):
        """Header name validator should reject empty input after normalization."""

        with self.assertRaises(FilterError):
            Filter.header_names(' , , ', key='--header-bypass-headers')

    def test_filter_header_values_should_split_lists_and_deduplicate(self):
        """Header value validator should split list values and deduplicate exact values."""

        actual = Filter.header_values(
            [' 127.0.0.1, localhost ', '127.0.0.1', ' 10.0.0.1 '],
            key='--header-bypass-ips'
        )

        self.assertEqual(actual, ['127.0.0.1', 'localhost', '10.0.0.1'])

    def test_filter_header_values_should_reject_empty_values(self):
        """Header value validator should reject empty input after normalization."""

        with self.assertRaises(FilterError):
            Filter.header_values([' ', ' , '], key='--header-bypass-ips')

    def test_filter_should_allow_header_bypass_limit_zero_without_header_bypass_flag(self):
        """Filter should preserve zero limit even when the feature flag is not enabled yet."""

        actual = Filter.filter({
            'host': 'example.com',
            'header_bypass_limit': 0,
        })

        self.assertEqual(actual['header_bypass_limit'], 0)
        self.assertEqual(actual['host'], 'example.com')

    def test_filter_should_allow_header_bypass_status_range_boundaries(self):
        """Header bypass status validator should accept valid HTTP status boundaries."""

        actual = Filter.filter({
            'host': 'example.com',
            'header_bypass_status': '100,599,401-403',
        })

        self.assertEqual(actual['header_bypass_status'], ['100', '599', '401-403'])

    def test_filter_should_reject_reversed_header_bypass_status_range(self):
        """Header bypass status validator should reject reversed ranges."""

        with self.assertRaises(FilterError):
            Filter.filter({
                'host': 'example.com',
                'header_bypass_status': '403-401',
            })

    def test_get_arg_values_should_preserve_default_header_bypass_limit(self):
        """Options.get_arg_values() should preserve the default non-zero header bypass limit."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            raw_request=None,
            session_load=None,
            header_bypass=False,
            header_bypass_headers=None,
            header_bypass_ips=None,
            header_bypass_status=None,
            header_bypass_limit=32,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        filtered = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'header_bypass_limit': 32,
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({
            'host': 'example.com',
            'header_bypass_limit': 32,
        })

    def test_get_arg_values_should_wrap_filter_error_as_options_error(self):
        """Options.get_arg_values() should convert FilterError into OptionsError."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            raw_request=None,
            session_load=None,
            header_bypass_headers='Bad:Header',
            header_bypass_limit=32,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        with self.assertRaises(Exception) as context:
            option.get_arg_values()

        self.assertEqual(context.exception.__class__.__name__, 'OptionsError')

if __name__ == '__main__':
    unittest.main()
