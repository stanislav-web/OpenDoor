# -*- coding: utf-8 -*-

import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.lib.browser.browser import Browser


class TestBrowserFilteredProgress(unittest.TestCase):
    """Filtered progress rendering tests."""

    def make_browser(self, items_size=1, total_items_size=100):
        """
        Build a minimal Browser instance for private helper testing.

        :param int items_size: processed items count
        :param int total_items_size: total items count
        :return: Browser instance
        :rtype: Browser
        """

        browser = object.__new__(Browser)
        setattr(
            browser,
            '_Browser__pool',
            SimpleNamespace(items_size=items_size, total_items_size=total_items_size)
        )
        return browser

    def test_emit_filtered_progress_should_rotate_calibrated_output(self):
        """Filtered progress should rotate in-place instead of emitting persistent lines."""

        browser = self.make_browser(items_size=1, total_items_size=100)
        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=120)):
                result = browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://example.com/missing', '158KB', '200'),
                    {
                        'calibration_score': 0.91,
                        'calibration_reason': 'soft-200-shape',
                    }
                )

        output = stdout.getvalue()

        self.assertTrue(result)
        self.assertTrue(output.startswith('\r'))
        self.assertIn('1.0% [000001/100] - calibrated - 200 - 158KB', output)
        self.assertIn('score=0.91', output)
        self.assertIn('https://example.com/missing', output)
        self.assertNotIn('soft-200-shape', output)
        self.assertNotIn('code,bucket', output)
        self.assertNotIn('\n', output)

    def test_emit_filtered_progress_should_truncate_to_terminal_width(self):
        """Filtered progress should stay one-line to avoid carriage-return wrapping glitches."""

        browser = self.make_browser(items_size=1, total_items_size=100)
        stdout = io.StringIO()
        long_url = 'https://example.com/' + ('very-long-path/' * 20)

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=80)):
                result = browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', long_url, '158KB', '200'),
                    {'calibration_score': 0.91}
                )

        output = stdout.getvalue()
        rendered = output.split('\r')[-1]

        self.assertTrue(result)
        self.assertLessEqual(len(rendered), 79)
        self.assertTrue(rendered.endswith('...'))
        self.assertNotIn('\n', output)

    def test_emit_filtered_progress_should_rotate_every_filtered_item(self):
        """Filtered progress should update the same line for every suppressed response."""

        browser = self.make_browser(items_size=1, total_items_size=100)
        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=140)):
                first = browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://example.com/one', '158KB', '200'),
                    {'calibration_score': 0.91}
                )

                browser._Browser__pool.items_size = 10
                second = browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://example.com/two', '158KB', '200'),
                    {'calibration_score': 0.91}
                )

                browser._Browser__pool.items_size = 26
                third = browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://example.com/three', '158KB', '200'),
                    {'calibration_score': 0.91}
                )

        output = stdout.getvalue()

        self.assertTrue(first)
        self.assertTrue(second)
        self.assertTrue(third)
        self.assertEqual(output.count('\r'), 6)
        self.assertIn('https://example.com/one', output)
        self.assertIn('https://example.com/two', output)
        self.assertIn('https://example.com/three', output)

    def test_clear_filtered_progress_should_clear_active_rotating_line(self):
        """Real findings should be able to clear active filtered progress before stdout output."""

        browser = self.make_browser(items_size=1, total_items_size=100)
        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=120)):
                browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://example.com/one', '158KB', '200'),
                    {'calibration_score': 0.91}
                )
                browser._Browser__clear_filtered_progress()

        output = stdout.getvalue()

        self.assertIn('\r', output)
        self.assertFalse(getattr(browser, '_Browser__filtered_progress_active'))
        self.assertEqual(getattr(browser, '_Browser__filtered_progress_last_length'), 0)


if __name__ == '__main__':
    unittest.main()
