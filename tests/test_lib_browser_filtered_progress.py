# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.lib.browser.browser import Browser


class TestBrowserFilteredProgress(unittest.TestCase):
    """Filtered progress heartbeat tests."""

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

    def test_emit_filtered_progress_should_print_first_calibrated_heartbeat(self):
        """First calibrated response should emit a visible heartbeat."""

        browser = self.make_browser(items_size=1, total_items_size=100)

        with patch('src.lib.browser.browser.tpl.info') as info_mock:
            result = browser._Browser__emit_filtered_progress(
                'calibrated',
                ('success', 'https://example.com/missing', '158KB', '200'),
                {
                    'calibration_score': 0.91,
                    'calibration_reason': 'soft-200-shape',
                }
            )

        self.assertTrue(result)
        info_mock.assert_called_once()
        message = info_mock.call_args.kwargs.get('msg')

        self.assertIn('1.0% [000001/100] - calibrated - 200 - 158KB', message)
        self.assertIn('score=0.91', message)
        self.assertNotIn('soft-200-shape', message)
        self.assertIn('https://example.com/missing', message)

    def test_emit_filtered_progress_should_print_every_filtered_item(self):
        """Filtered progress should print every suppressed response in compact form."""

        browser = self.make_browser(items_size=1, total_items_size=100)

        with patch('src.lib.browser.browser.tpl.info') as info_mock:
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

        self.assertTrue(first)
        self.assertTrue(second)
        self.assertTrue(third)
        self.assertEqual(info_mock.call_count, 3)


if __name__ == '__main__':
    unittest.main()
