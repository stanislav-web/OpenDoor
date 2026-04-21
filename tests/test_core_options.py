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

if __name__ == '__main__':
    unittest.main()
