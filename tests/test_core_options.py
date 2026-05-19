# -*- coding: utf-8 -*-

import unittest
from argparse import Namespace
from unittest.mock import MagicMock, patch

from src.core.options import Options
from src.core.options.exceptions import (
    ArgumentParserError,
    FilterError,
    OptionsError,
    ThrowingArgumentParser,
)


class TestOptions(unittest.TestCase):
    """TestOptions class."""

    def make_options(self, namespace=None):
        """Create an Options instance without calling __init__."""

        option = Options.__new__(Options)
        setattr(option, '_Options__standalone', ['version', 'update', 'examples', 'docs'])
        setattr(option, 'parser', MagicMock())
        setattr(option, 'args', namespace)
        return option

    def test_throwing_argument_parser_error_raises_custom_exception(self):
        """ThrowingArgumentParser.error() should raise ArgumentParserError."""

        with self.assertRaises(ArgumentParserError) as context:
            ThrowingArgumentParser.error('bad argument')

        self.assertEqual(str(context.exception), 'bad argument')

    def test_options_error_preserves_message(self):
        """OptionsError should preserve the original message."""

        error = OptionsError('options failed')
        self.assertEqual(str(error), 'options failed')

    def test_filter_error_preserves_message(self):
        """FilterError should preserve the original message."""

        error = FilterError('filter failed')
        self.assertEqual(str(error), 'filter failed')

    def test_init_builds_parser_and_uses_default_wizard_const(self):
        """Options.__init__() should build the parser and keep the wizard default const."""

        with patch('src.core.options.options.sys.argv', ['opendoor.py', '--wizard']):
            option = Options()

        self.assertEqual(option.args.wizard, 'opendoor.conf')
        self.assertTrue(hasattr(option, 'parser'))
        self.assertIsNotNone(option.parser)

    def test_init_wraps_argument_parser_errors(self):
        """Options.__init__() should wrap parser errors into OptionsError."""

        with patch('src.core.options.options.ThrowingArgumentParser.parse_args', side_effect=ArgumentParserError('bad args')):
            with self.assertRaises(OptionsError):
                Options()

    def test_get_arg_values_returns_first_standalone_flag_only(self):
        """Options.get_arg_values() should return only the first enabled standalone flag."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            version=True,
            update=True,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        self.assertEqual(option.get_arg_values(), {'version': True})

    def test_get_arg_values_should_preserve_debug_zero(self):
        """Options.get_arg_values() should keep --debug 0 instead of dropping it as falsy."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
            debug=0,
        )
        option = self.make_options(namespace)

        with patch('src.core.options.options.Filter.filter', return_value={'host': 'example.com', 'debug': 0}) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, {'host': 'example.com', 'debug': 0})
        filter_mock.assert_called_once_with({'host': 'example.com', 'debug': 0})


    def test_get_arg_values_should_keep_explicit_delay_zero(self):
        """Options.get_arg_values() should keep explicit --delay 0 for wizard/session overrides."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
            delay=0.0,
        )
        option = self.make_options(namespace)

        with patch('src.core.options.options.Filter.filter', return_value={'host': 'example.com', 'delay': 0.0}) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, {'host': 'example.com', 'delay': 0.0})
        filter_mock.assert_called_once_with({'host': 'example.com', 'delay': 0.0})

    def test_get_arg_values_should_pass_fractional_delay(self):
        """Options.get_arg_values() should pass fractional --delay values to the filter."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
            delay=0.1,
        )
        option = self.make_options(namespace)

        with patch('src.core.options.options.Filter.filter', return_value={'host': 'example.com', 'delay': 0.1}) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, {'host': 'example.com', 'delay': 0.1})
        filter_mock.assert_called_once_with({'host': 'example.com', 'delay': 0.1})

    def test_get_arg_values_filters_non_standalone_arguments(self):
        """Options.get_arg_values() should pass non-standalone args through Filter.filter()."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            port=8080,
            scan='subdomains',
            proxy='http://127.0.0.1:8080',
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        filtered = {'host': 'example.com', 'scheme': 'http://', 'ssl': False, 'port': 8080, 'scan': 'subdomains'}
        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with(
            {
                'host': 'example.com',
                'port': 8080,
                'scan': 'subdomains',
                'proxy': 'http://127.0.0.1:8080',
            }
        )

    def test_get_arg_values_accepts_wizard_without_host(self):
        """Options.get_arg_values() should allow wizard-only execution without host."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard='opendoor.conf',
        )
        option = self.make_options(namespace)

        with patch('src.core.options.options.Filter.filter', return_value={'wizard': 'opendoor.conf'}) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, {'wizard': 'opendoor.conf'})
        filter_mock.assert_called_once_with({'wizard': 'opendoor.conf'})

    def test_get_arg_values_exits_when_required_input_is_missing(self):
        """Options.get_arg_values() should print help and exit when no actionable input is provided."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)
        option.parser.print_help.return_value = 'help text'

        with self.assertRaises(SystemExit):
            option.get_arg_values()

        option.parser.print_help.assert_called_once_with()

    def test_get_arg_values_wraps_filter_errors(self):
        """Options.get_arg_values() should wrap filter failures into OptionsError."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        with patch('src.core.options.options.Filter.filter', side_effect=FilterError('invalid host')):
            with self.assertRaises(OptionsError):
                option.get_arg_values()

    def test_get_arg_values_wraps_attribute_errors(self):
        """Options.get_arg_values() should wrap invalid args containers into OptionsError."""

        option = self.make_options(namespace={})

        with self.assertRaises(OptionsError):
            option.get_arg_values()


    def test_init_should_parse_tls_legacy_flag(self):
        """Options.__init__() should parse the opt-in TLS legacy flag."""

        with patch('src.core.options.options.sys.argv', [
            'opendoor.py',
            '--host',
            'https://example.com',
            '--tls-legacy',
        ]):
            option = Options()

        self.assertTrue(option.args.tls_legacy)

    def test_get_arg_values_should_pass_tls_legacy_through_filter(self):
        """Options.get_arg_values() should preserve --tls-legacy when enabled."""

        namespace = Namespace(
            host='https://example.com',
            hostlist=None,
            stdin=False,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
            tls_legacy=True,
        )
        option = self.make_options(namespace)

        with patch('src.core.options.options.Filter.filter', return_value={'tls_legacy': True}) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, {'tls_legacy': True})
        self.assertEqual(filter_mock.call_args[0][0]['tls_legacy'], True)

    def test_init_should_parse_recursive_arguments(self):
        """Options.__init__() should parse recursive scan arguments."""

        with patch(
            'src.core.options.options.sys.argv',
            [
                'opendoor.py',
                '--host',
                'example.com',
                '--recursive',
                '--recursive-depth',
                '2',
                '--recursive-status',
                '200,403',
                '--recursive-exclude',
                'jpg,png,css',
            ]
        ):
            option = Options()

        self.assertTrue(option.args.recursive)
        self.assertEqual(option.args.recursive_depth, 2)
        self.assertEqual(option.args.recursive_status, '200,403')
        self.assertEqual(option.args.recursive_exclude, 'jpg,png,css')

    def test_get_arg_values_should_pass_recursive_arguments_through_filter(self):
        """Options.get_arg_values() should preserve recursive arguments."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            recursive=True,
            recursive_depth=2,
            recursive_status='200,403',
            recursive_exclude='jpg,png',
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
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with(
            {
                'host': 'example.com',
                'recursive': True,
                'recursive_depth': 2,
                'recursive_status': '200,403',
                'recursive_exclude': 'jpg,png',
            }
        )

    def test_init_should_parse_multiple_header_arguments(self):
        """Options.__init__() should parse multiple custom request headers."""

        with patch(
            'src.core.options.options.sys.argv',
            [
                'opendoor.py',
                '--host',
                'example.com',
                '--header',
                'Authorization: Bearer test',
                '--header',
                'X-Test: 1',
            ]
        ):
            option = Options()

        self.assertEqual(
            option.args.header,
            ['Authorization: Bearer test', 'X-Test: 1']
        )

    def test_get_arg_values_should_preserve_header_arguments(self):
        """Options.get_arg_values() should preserve custom header arguments."""

        namespace = Namespace(
            host='example.com',
            header=['Authorization: Bearer test', 'X-Test: 1'],
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
            'header': ['Authorization: Bearer test', 'X-Test: 1'],
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with(
            {
                'host': 'example.com',
                'header': ['Authorization: Bearer test', 'X-Test: 1'],
            }
        )

    def test_init_should_parse_multiple_cookie_arguments(self):
        """Options.__init__() should parse multiple custom cookie arguments."""

        with patch(
            'src.core.options.options.sys.argv',
            [
                'opendoor.py',
                '--host',
                'example.com',
                '--cookie',
                'sid=abc123',
                '--cookie',
                'locale=en',
            ]
        ):
            option = Options()

        self.assertEqual(option.args.cookie, ['sid=abc123', 'locale=en'])

    def test_get_arg_values_should_preserve_cookie_arguments(self):
        """Options.get_arg_values() should preserve custom cookie arguments."""

        namespace = Namespace(
            host='example.com',
            cookie=['sid=abc123', 'locale=en'],
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
            'cookie': ['sid=abc123', 'locale=en'],
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with(
            {
                'host': 'example.com',
                'cookie': ['sid=abc123', 'locale=en'],
            }
        )

    def test_init_should_parse_hostlist_argument(self):
        """Options.__init__() should parse --hostlist."""

        with patch(
            'src.core.options.options.sys.argv',
            ['opendoor.py', '--hostlist', 'targets.txt']
        ):
            option = Options()

        self.assertEqual(option.args.hostlist, 'targets.txt')
        self.assertFalse(option.args.stdin)

    def test_init_should_parse_stdin_argument(self):
        """Options.__init__() should parse --stdin."""

        with patch(
            'src.core.options.options.sys.argv',
            ['opendoor.py', '--stdin']
        ):
            option = Options()

        self.assertTrue(option.args.stdin)
        self.assertIsNone(option.args.hostlist)

    def test_init_should_reject_multiple_target_sources(self):
        """Options.__init__() should reject conflicting target sources."""

        with patch(
            'src.core.options.options.sys.argv',
            ['opendoor.py', '--host', 'example.com', '--hostlist', 'targets.txt']
        ):
            with self.assertRaises(OptionsError):
                Options()

    def test_get_arg_values_filters_hostlist_arguments(self):
        """Options.get_arg_values() should pass hostlist through Filter.filter()."""

        namespace = Namespace(
            host='',
            hostlist='targets.txt',
            stdin=False,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        filtered = {'targets': [{'host': 'example.com', 'scheme': 'http://', 'ssl': False}]}
        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({'hostlist': 'targets.txt'})

    def test_get_arg_values_filters_stdin_arguments(self):
        """Options.get_arg_values() should pass stdin through Filter.filter()."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=True,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        filtered = {'targets': [{'host': 'example.com', 'scheme': 'http://', 'ssl': False}]}
        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({'stdin': True})


    def test_init_should_parse_response_filter_arguments(self):
        """Options.__init__() should parse response filter flags without changing legacy UX."""

        with patch(
            'src.core.options.options.sys.argv',
            [
                'opendoor.py',
                '--host', 'example.com',
                '--include-status', '200-299,403',
                '--exclude-status', '404,500-599',
                '--exclude-size', '0,1234',
                '--exclude-size-range', '0-64,1024-2048',
                '--match-text', 'Index of',
                '--exclude-text', 'Not Found',
                '--match-regex', '(?i)admin',
                '--exclude-regex', '(?i)forbidden',
                '--min-response-length', '32',
                '--max-response-length', '4096',
            ]
        ):
            option = Options()

        self.assertEqual(option.args.include_status, '200-299,403')
        self.assertEqual(option.args.exclude_status, '404,500-599')
        self.assertEqual(option.args.exclude_size, '0,1234')
        self.assertEqual(option.args.exclude_size_range, '0-64,1024-2048')
        self.assertEqual(option.args.match_text, ['Index of'])
        self.assertEqual(option.args.exclude_text, ['Not Found'])
        self.assertEqual(option.args.match_regex, ['(?i)admin'])
        self.assertEqual(option.args.exclude_regex, ['(?i)forbidden'])
        self.assertEqual(option.args.min_response_length, 32)
        self.assertEqual(option.args.max_response_length, 4096)

    def test_get_arg_values_should_preserve_response_filter_arguments(self):
        """Options.get_arg_values() should pass response filters through Filter.filter()."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            include_status='200-299,403',
            exclude_status='404,500-599',
            exclude_size='0,1234',
            exclude_size_range='0-64,1024-2048',
            match_text=['Index of'],
            exclude_text=['Not Found'],
            match_regex=['(?i)admin'],
            exclude_regex=['(?i)forbidden'],
            min_response_length=32,
            max_response_length=4096,
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
            'include_status': ['200-299', '403'],
            'exclude_status': ['404', '500-599'],
            'exclude_size': ['0', '1234'],
            'exclude_size_range': ['0-64', '1024-2048'],
            'match_text': ['Index of'],
            'exclude_text': ['Not Found'],
            'match_regex': ['(?i)admin'],
            'exclude_regex': ['(?i)forbidden'],
            'min_response_length': 32,
            'max_response_length': 4096,
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({
            'host': 'example.com',
            'include_status': '200-299,403',
            'exclude_status': '404,500-599',
            'exclude_size': '0,1234',
            'exclude_size_range': '0-64,1024-2048',
            'match_text': ['Index of'],
            'exclude_text': ['Not Found'],
            'match_regex': ['(?i)admin'],
            'exclude_regex': ['(?i)forbidden'],
            'min_response_length': 32,
            'max_response_length': 4096,
        })


    def test_init_should_parse_raw_request_and_scheme(self):
        """Options.__init__() should parse raw-request template arguments."""

        with patch(
            'src.core.options.options.sys.argv',
            ['opendoor.py', '--raw-request', 'request.txt', '--scheme', 'https']
        ):
            option = Options()

        self.assertEqual(option.args.raw_request, 'request.txt')
        self.assertEqual(option.args.scheme, 'https')

    def test_get_arg_values_filters_raw_request_arguments(self):
        """Options.get_arg_values() should pass raw-request arguments through Filter.filter()."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            raw_request='request.txt',
            scheme='https',
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        filtered = {'host': 'example.com', 'scheme': 'https://', 'ssl': True, 'method': 'POST'}
        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({'raw_request': 'request.txt', 'scheme': 'https'})

    def test_get_arg_values_allows_raw_request_without_target_sources(self):
        """Options.get_arg_values() should allow raw-request mode without --host/--hostlist/--stdin."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            raw_request='request.txt',
            scheme='https',
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        filtered = {'raw_request': 'request.txt', 'scheme': 'https://', 'host': 'example.com'}
        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({
            'raw_request': 'request.txt',
            'scheme': 'https',
        })

    def test_get_arg_values_prints_help_when_no_target_or_action_is_selected(self):
        """Options.get_arg_values() should print help and exit when nothing actionable was provided."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            raw_request=None,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        with patch('sys.exit', side_effect=SystemExit) as exit_mock:
            with self.assertRaises(SystemExit):
                option.get_arg_values()

        exit_mock.assert_called_once()

    def test_get_arg_values_keeps_first_enabled_standalone_action(self):
        """Options.get_arg_values() should return the first enabled standalone action only."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            raw_request=None,
            version=False,
            update=True,
            examples=True,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        actual = option.get_arg_values()

        self.assertEqual(actual, {'update': True})

    def test_get_arg_values_prints_help_and_exits_when_nothing_is_selected(self):
        """Options.get_arg_values() should print help and exit when no target or action is selected."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            raw_request=None,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        with patch('sys.exit', side_effect=SystemExit) as exit_mock:
            with self.assertRaises(SystemExit):
                option.get_arg_values()

        option.parser.print_help.assert_called_once()
        exit_mock.assert_called_once()

    def test_get_arg_values_wraps_filter_errors_into_options_error(self):
        """Options.get_arg_values() should wrap filter failures into OptionsError."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        with patch('src.core.options.options.Filter.filter', side_effect=FilterError('bad filter')):
            with self.assertRaises(OptionsError) as context:
                option.get_arg_values()

        self.assertEqual(str(context.exception), 'bad filter')

    def test_get_arg_values_allows_session_load_without_target_sources(self):
        """Options.get_arg_values() should allow session-load mode without host inputs."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            raw_request=None,
            session_load='session.json',
            session_autosave_sec=20,
            session_autosave_items=200,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        filtered = {
            'session_load': '/tmp/session.json',
            'session_autosave_sec': 20,
            'session_autosave_items': 200,
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({
            'session_load': 'session.json',
            'session_autosave_sec': 20,
            'session_autosave_items': 200,
        })

    def test_get_arg_values_returns_docs_as_standalone_action(self):
        """Options.get_arg_values() should return docs as the selected standalone action."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            raw_request=None,
            session_load=None,
            version=False,
            update=False,
            examples=False,
            docs=True,
            wizard=None,
        )
        option = self.make_options(namespace)

        actual = option.get_arg_values()

        self.assertEqual(actual, {'docs': True})

    def test_get_arg_values_keeps_waf_detect_flag(self):
        """Options.get_arg_values() should keep the --waf-detect flag."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            raw_request=None,
            session_load=None,
            waf_detect=True,
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
            'targets': [{'host': 'example.com', 'scheme': 'http://', 'ssl': False, 'source': 'example.com'}],
            'waf_detect': True,
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered):
            actual = option.get_arg_values()

        self.assertTrue(actual['waf_detect'])

    def test_get_arg_values_should_enable_waf_detect_when_waf_safe_mode_is_enabled(self):
        """Options.get_arg_values() should enable waf_detect when waf_safe_mode is enabled."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            raw_request=None,
            session_load=None,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
            waf_safe_mode=True,
        )
        option = self.make_options(namespace)

        filtered = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'waf_safe_mode': True,
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'waf_safe_mode': True,
            'waf_detect': True,
        })
        filter_mock.assert_called_once_with({
            'host': 'example.com',
            'waf_safe_mode': True,
        })

    def test_init_should_parse_fail_on_bucket_argument(self):
        """Options.__init__() should parse CI/CD fail-on bucket argument."""

        with patch(
                'src.core.options.options.sys.argv',
                [
                    'opendoor.py',
                    '--host',
                    'example.com',
                    '--fail-on-bucket',
                    'success,auth,forbidden,blocked',
                ]
        ):
            option = Options()

        self.assertEqual(option.args.fail_on_bucket, 'success,auth,forbidden,blocked')

    def test_get_arg_values_should_pass_fail_on_bucket_through_filter(self):
        """Options.get_arg_values() should pass CI/CD fail-on bucket argument through Filter.filter()."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            raw_request=None,
            session_load=None,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
            fail_on_bucket='success,auth',
        )
        option = self.make_options(namespace)

        filtered = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'fail_on_bucket': ['success', 'auth'],
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({
            'host': 'example.com',
            'fail_on_bucket': 'success,auth',
        })

    def test_init_should_parse_retries_fail_streak_argument(self):
        """Options.__init__() should parse the consecutive max-retry path threshold."""

        with patch(
                'src.core.options.options.sys.argv',
                [
                    'opendoor.py',
                    '--host',
                    'example.com',
                    '--retries-fail-streak',
                    '25',
                ]
        ):
            option = Options()

        self.assertEqual(option.args.retries_fail_streak, 25)

    def test_get_arg_values_should_pass_retries_fail_streak_through_filter(self):
        """Options.get_arg_values() should pass --retries-fail-streak through Filter.filter()."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            raw_request=None,
            session_load=None,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
            retries_fail_streak=25,
        )
        option = self.make_options(namespace)

        filtered = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'retries_fail_streak': 25,
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({
            'host': 'example.com',
            'retries_fail_streak': 25,
        })

    def test_init_should_parse_network_transport_arguments(self):
        """Options.__init__() should parse network transport arguments."""

        with patch(
                'src.core.options.options.sys.argv',
                [
                    'opendoor.py',
                    '--host',
                    'example.com',
                    '--transport',
                    'wireguard',
                    '--transport-profile',
                    './vpn/nl.conf',
                    '--transport-rotate',
                    'none',
                    '--transport-timeout',
                    '15',
                    '--transport-healthcheck-url',
                    'https://example.com/ip',
                ]
        ):
            option = Options()

        self.assertEqual(option.args.transport, 'wireguard')
        self.assertEqual(option.args.transport_profile, './vpn/nl.conf')
        self.assertEqual(option.args.transport_rotate, 'none')
        self.assertEqual(option.args.transport_timeout, 15)
        self.assertEqual(option.args.transport_healthcheck_url, 'https://example.com/ip')

    def test_get_arg_values_should_pass_network_transport_arguments_through_filter(self):
        """Options.get_arg_values() should pass network transport arguments through Filter.filter()."""

        namespace = Namespace(
            host='example.com',
            hostlist=None,
            stdin=False,
            raw_request=None,
            session_load=None,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
            transport='openvpn',
            transport_profile='./vpn/nl.ovpn',
            transport_profiles=None,
            transport_rotate='none',
            transport_timeout=20,
            transport_healthcheck_url='https://example.com/ip',
            transport_bin='openvpn',
            openvpn_auth='./auth.txt',
        )
        option = self.make_options(namespace)

        filtered = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'transport': 'openvpn',
            'transport_profile': '/abs/vpn/nl.ovpn',
            'transport_rotate': 'none',
            'transport_timeout': 20,
            'transport_healthcheck_url': 'https://example.com/ip',
            'transport_bin': 'openvpn',
            'openvpn_auth': '/abs/auth.txt',
        }

        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, filtered)
        filter_mock.assert_called_once_with({
            'host': 'example.com',
            'transport': 'openvpn',
            'transport_profile': './vpn/nl.ovpn',
            'transport_rotate': 'none',
            'transport_timeout': 20,
            'transport_healthcheck_url': 'https://example.com/ip',
            'transport_bin': 'openvpn',
            'openvpn_auth': './auth.txt',
        })

    def test_get_arg_values_allows_diff_without_target(self):
        """Options.get_arg_values() should allow diff mode without scan targets."""

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            raw_request=None,
            session_load=None,
            diff='old.sqlite:new.sqlite',
            reports='std,json',
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        with patch('src.core.options.options.Filter.filter', return_value={'diff': 'old.sqlite:new.sqlite', 'reports': 'std,json'}) as filter_mock:
            actual = option.get_arg_values()

        self.assertEqual(actual, {'diff': 'old.sqlite:new.sqlite', 'reports': 'std,json'})
        filter_mock.assert_called_once_with({'diff': 'old.sqlite:new.sqlite', 'reports': 'std,json'})


if __name__ == '__main__':
    unittest.main()
