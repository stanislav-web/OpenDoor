# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from src.lib.io.arguments import Arguments
from src.lib.io.exceptions import ArgumentsError
from src.core.options.exceptions import OptionsError


class TestArguments(unittest.TestCase):
    """TestArguments class."""

    def test_get_arguments_returns_parsed_options(self):
        """Arguments.get_arguments() should return parsed CLI values."""

        with patch('src.lib.io.arguments.options') as options_mock:
            options_mock.return_value.get_arg_values.return_value = {'host': 'example.com'}
            actual = Arguments.get_arguments()

        self.assertEqual(actual, {'host': 'example.com'})
        options_mock.return_value.get_arg_values.assert_called_once_with()

    def test_get_arguments_wraps_options_error(self):
        """Arguments.get_arguments() should wrap options failures into ArgumentsError."""

        with patch('src.lib.io.arguments.options') as options_mock:
            options_mock.return_value.get_arg_values.side_effect = OptionsError('bad args')
            with self.assertRaises(ArgumentsError) as context:
                Arguments.get_arguments()

        self.assertEqual(str(context.exception), 'str: bad args')

    def test_is_arg_callable_delegates_to_helper(self):
        """Arguments.is_arg_callable() should delegate to helper.is_callable()."""

        with patch('src.lib.io.arguments.helper.is_callable', return_value=True) as callable_mock:
            self.assertTrue(Arguments.is_arg_callable(lambda: None))

        callable_mock.assert_called_once()

    def test_is_arg_callable_returns_false_for_non_callable(self):
        """Arguments.is_arg_callable() should return False for non-callable values."""

        with patch('src.lib.io.arguments.helper.is_callable', return_value=False):
            self.assertFalse(Arguments.is_arg_callable('not-callable'))


if __name__ == '__main__':
    unittest.main()