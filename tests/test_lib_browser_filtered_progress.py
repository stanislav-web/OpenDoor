# -*- coding: utf-8 -*-

import io
import logging
import unittest
from threading import RLock
from types import SimpleNamespace
from unittest.mock import patch

from src.core.logger.logger import Logger
from src.lib.browser.browser import Browser


class TestBrowserFilteredProgress(unittest.TestCase):
    """Filtered progress rendering tests."""

    def tearDown(self):
        """Remove shared logger handlers after stdout-capture tests."""

        for name in ('warning', logging.getLogger().name):
            log_instance = Logger.log(name)
            for handler in list(log_instance.handlers):
                log_instance.removeHandler(handler)

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




    def test_add_urls_should_not_glue_ignored_warning_after_filtered_progress(self):
        """_add_urls() should finish rotating progress before ignored-list warnings."""

        browser = self.make_browser(items_size=2047, total_items_size=95062)
        browser._Browser__reader = SimpleNamespace(
            total_lines=95062,
            get_ignored_list=lambda: ['index.php'],
        )
        browser._Browser__deduplicate_scan_url = lambda url: True
        browser._Browser__register_pending_request = lambda url, depth: True
        browser._Browser__catch_report_data = lambda *args, **kwargs: None

        def add_task(_callback, _url, _depth):
            browser._Browser__emit_filtered_progress(
                'calibrated',
                ('success', 'https://localhost/accounts/sellers', '214B', '404'),
                {'calibration_score': 1.0}
            )

        browser._Browser__pool = SimpleNamespace(
            items_size=2047,
            total_items_size=95062,
            add=add_task,
            join=lambda: None,
        )
        stdout = io.StringIO()

        for handler in list(Logger.log('warning').handlers):
            Logger.log('warning').removeHandler(handler)

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=220)):
                browser._add_urls([
                    'https://localhost/accounts/sellers',
                    'https://localhost/index.php',
                ])

        output = stdout.getvalue()

        self.assertIn('https://localhost/accounts/sellers', output)
        self.assertIn('Ignored /index.php', output)
        self.assertNotIn('accounts/sellers[', output)
        self.assertIn('accounts/sellers\n', output)
        self.assertFalse(getattr(browser, '_Browser__filtered_progress_active'))

    def test_ignored_item_warning_should_finish_filtered_progress_line(self):
        """Ignored-item warnings should not glue to active calibrated progress."""

        browser = self.make_browser(items_size=2047, total_items_size=95062)
        browser._Browser__reader = SimpleNamespace(total_lines=95062)
        stdout = io.StringIO()

        for handler in list(Logger.log('warning').handlers):
            Logger.log('warning').removeHandler(handler)

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=220)):
                browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://localhost/accounts/sellers', '214B', '404'),
                    {'calibration_score': 1.0}
                )
                browser._Browser__emit_ignored_item_warning('https://localhost/index.php')

        output = stdout.getvalue()

        self.assertIn('https://localhost/accounts/sellers', output)
        self.assertIn('Ignored /index.php', output)
        self.assertNotIn('accounts/sellers[', output)
        self.assertIn('accounts/sellers\n', output)
        self.assertFalse(getattr(browser, '_Browser__filtered_progress_active'))

    def test_ignored_item_warning_should_use_current_scan_progress(self):
        """Ignored-item warnings should render the current scan counter, not zero."""

        browser = self.make_browser(items_size=47083, total_items_size=95052)
        browser._Browser__reader = SimpleNamespace(total_lines=95052)
        stdout = io.StringIO()

        for handler in list(Logger.log('warning').handlers):
            Logger.log('warning').removeHandler(handler)

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=220)):
                browser._Browser__emit_ignored_item_warning('https://kipkomplekt.ru/error.php')

        output = stdout.getvalue()

        self.assertIn('skip [47083/95052] - Ignored /error.php', output)
        self.assertNotIn('skip [00000/95052]', output)

    def test_add_urls_should_count_streamed_ignored_items_in_progress(self):
        """Ignored dictionary entries should advance the displayed scan position."""

        browser = self.make_browser(items_size=0, total_items_size=3)
        browser._Browser__reader = SimpleNamespace(
            total_lines=3,
            get_ignored_list=lambda: ['index.php'],
        )
        browser._Browser__deduplicate_scan_url = lambda url: True
        browser._Browser__register_pending_request = lambda url, depth: True
        browser._Browser__catch_report_data = lambda *args, **kwargs: None

        browser._Browser__pool = SimpleNamespace(
            items_size=0,
            completed_size=0,
            submitted_size=0,
            total_items_size=3,
            add=lambda *_args, **_kwargs: None,
            join=lambda: None,
        )
        stdout = io.StringIO()

        for handler in list(Logger.log('warning').handlers):
            Logger.log('warning').removeHandler(handler)

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=220)):
                browser._add_urls([
                    'https://localhost/admin',
                    'https://localhost/index.php',
                    'https://localhost/health',
                ])

        output = stdout.getvalue()

        self.assertIn('skip [2/3] - Ignored /index.php', output)
        self.assertNotIn('skip [0/3]', output)

    def test_waf_safe_mode_warning_should_clear_filtered_progress_first(self):
        """WAF activation warning should not glue to a rotating calibration line."""

        browser = self.make_browser(items_size=3523, total_items_size=95067)
        browser._Browser__config = SimpleNamespace(is_waf_safe_mode=True)
        browser._Browser__waf_safe_lock = RLock()
        browser._Browser__waf_safe_active = False
        browser._Browser__waf_safe_vendor = None
        browser._Browser__waf_safe_confidence = None
        browser._Browser__waf_safe_delay = 0.75
        browser._Browser__waf_safe_next_at = 0
        stdout = io.StringIO()

        for handler in list(Logger.log('warning').handlers):
            Logger.log('warning').removeHandler(handler)

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=220)):
                browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://localhost/pers.csp', '3KB', '404'),
                    {'calibration_score': 1.0}
                )
                browser._Browser__activate_waf_safe_mode(
                    {'name': 'DDoS-GUARD', 'confidence': 83},
                    immediate=True
                )

        output = stdout.getvalue()

        self.assertIn('https://localhost/pers.csp', output)
        self.assertIn('WAF safe mode activated: DDoS-GUARD (83%)', output)
        self.assertNotIn('pers.csp[', output)
        self.assertIn('pers.csp\nWAF safe mode activated', output)
        self.assertIn(chr(13), output)
        self.assertFalse(getattr(browser, '_Browser__filtered_progress_active'))

    def test_filtered_progress_should_continue_with_new_url_after_waf_warning(self):
        """Progress rotation should keep updating URLs after a warning line."""

        browser = self.make_browser(items_size=73, total_items_size=95067)
        browser._Browser__config = SimpleNamespace(is_waf_safe_mode=True)
        browser._Browser__waf_safe_lock = RLock()
        browser._Browser__waf_safe_active = False
        browser._Browser__waf_safe_vendor = None
        browser._Browser__waf_safe_confidence = None
        browser._Browser__waf_safe_delay = 0.75
        browser._Browser__waf_safe_next_at = 0
        stdout = io.StringIO()

        for handler in list(Logger.log('warning').handlers):
            Logger.log('warning').removeHandler(handler)

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=180)):
                browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://localhost/pers.csp', '3KB', '404'),
                    {'calibration_score': 1.0}
                )
                browser._Browser__activate_waf_safe_mode(
                    {'name': 'DDoS-GUARD', 'confidence': 83},
                    immediate=True
                )
                browser._Browser__pool.items_size = 74
                browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('success', 'https://localhost/next-page.php', '3KB', '404'),
                    {'calibration_score': 1.0}
                )

        output = stdout.getvalue()
        last_visual_line = output.split('\n')[-1].split('\r')[-1]

        self.assertIn('[000074/95067]', last_visual_line)
        self.assertIn('https://localhost/next-page.php', last_visual_line)
        self.assertNotIn('https://localhost/pers.csp', last_visual_line)
        self.assertTrue(getattr(browser, '_Browser__filtered_progress_active'))


    def test_emit_filtered_progress_should_prefer_request_url_for_redirect_calibration(self):
        """Rotating calibration progress should show scanned URL, not redirect target."""

        browser = self.make_browser(items_size=74, total_items_size=95067)
        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=220)):
                result = browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('redirect', 'https://localhost/', '0B', '301'),
                    {'calibration_score': 1.0},
                    request_url='https://localhost/CMS.h'
                )

        output = stdout.getvalue()
        rendered = output.split('\r')[-1]

        self.assertTrue(result)
        self.assertIn('[000074/95067]', rendered)
        self.assertIn('https://localhost/CMS.h', rendered)
        self.assertNotIn('https://localhost/ ', rendered)

    def test_emit_filtered_progress_should_keep_rendered_url_without_request_url(self):
        """Direct helper usage should remain backward-compatible without request URL."""

        browser = self.make_browser(items_size=74, total_items_size=95067)
        stdout = io.StringIO()

        with patch('sys.stdout', stdout):
            with patch('shutil.get_terminal_size', return_value=SimpleNamespace(columns=220)):
                result = browser._Browser__emit_filtered_progress(
                    'calibrated',
                    ('redirect', 'https://localhost/', '0B', '301'),
                    {'calibration_score': 1.0}
                )

        output = stdout.getvalue()
        rendered = output.split('\r')[-1]

        self.assertTrue(result)
        self.assertIn('[000074/95067]', rendered)
        self.assertIn('https://localhost/', rendered)

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
