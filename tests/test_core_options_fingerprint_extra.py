# -*- coding: utf-8 -*-

import unittest
from argparse import Namespace
from unittest.mock import MagicMock, patch

from src.core.options import Options


class TestOptionsFingerprintExtra(unittest.TestCase):
    """Extra Options coverage for fingerprint and raw-request branches."""

    def make_options(self, namespace=None):
        """
        Build Options without running __init__.

        :param Namespace namespace: argparse namespace
        :return: Options
        """

        option = Options.__new__(Options)
        setattr(option, '_Options__standalone', ['version', 'update', 'examples', 'docs'])
        setattr(option, 'parser', MagicMock())
        setattr(option, 'args', namespace)
        return option

    def test_init_parses_fingerprint_flag(self):
        """
        Options.__init__() should parse --fingerprint.

        :return: None
        """

        with patch('src.core.options.options.sys.argv', ['opendoor.py', '--host', 'example.com', '--fingerprint']):
            option = Options()

        self.assertTrue(option.args.fingerprint)

    def test_get_arg_values_allows_raw_request_without_host(self):
        """
        Options.get_arg_values() should allow raw-request mode without host.

        :return: None
        """

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=False,
            raw_request='tests/data/request.txt',
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
            fingerprint=True,
        )
        option = self.make_options(namespace)

        filtered = {'raw_request': 'tests/data/request.txt', 'fingerprint': True}
        with patch('src.core.options.options.Filter.filter', return_value=filtered) as filter_mock:
            result = option.get_arg_values()

        self.assertEqual(result, filtered)
        filter_mock.assert_called_once_with({'raw_request': 'tests/data/request.txt', 'fingerprint': True})

    def test_get_arg_values_allows_hostlist_without_host(self):
        """
        Options.get_arg_values() should allow hostlist-only execution.

        :return: None
        """

        namespace = Namespace(
            host='',
            hostlist='targets.txt',
            stdin=False,
            raw_request=None,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        filtered = {'targets': [{'host': 'a.test'}]}
        with patch('src.core.options.options.Filter.filter', return_value=filtered):
            result = option.get_arg_values()

        self.assertEqual(result, filtered)

    def test_get_arg_values_allows_stdin_without_host(self):
        """
        Options.get_arg_values() should allow stdin-only execution.

        :return: None
        """

        namespace = Namespace(
            host='',
            hostlist=None,
            stdin=True,
            raw_request=None,
            version=False,
            update=False,
            examples=False,
            docs=False,
            wizard=None,
        )
        option = self.make_options(namespace)

        filtered = {'targets': [{'host': 'stdin.test'}]}
        with patch('src.core.options.options.Filter.filter', return_value=filtered):
            result = option.get_arg_values()

        self.assertEqual(result, filtered)