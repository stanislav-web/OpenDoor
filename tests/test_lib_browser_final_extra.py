# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core import SocketError
from src.lib.browser.browser import Browser
from src.lib.browser.exceptions import BrowserError


class TestBrowserFinalExtra(unittest.TestCase):
    """TestBrowserFinalExtra class."""

    def make_browser(self):
        """Create a Browser instance without running the constructor."""

        return object.__new__(Browser)

    def test_start_request_provider_uses_proxy_branch(self):
        """Browser.__start_request_provider() should use proxy provider when proxy mode is enabled."""

        browser = self.make_browser()
        reader = MagicMock()
        reader.get_proxies.return_value = ['http://127.0.0.1:8080']
        reader.get_user_agents.return_value = ['UA']
        debug = MagicMock()
        config = SimpleNamespace(is_proxy=True, is_ssl=False)

        setattr(browser, '_Browser__reader', reader)
        setattr(browser, '_Browser__debug', debug)
        setattr(browser, '_Browser__config', config)

        with patch('src.lib.browser.browser.request_proxy', return_value='proxy-client') as proxy_factory:
            getattr(browser, '_Browser__start_request_provider')()

        proxy_factory.assert_called_once()
        self.assertEqual(getattr(browser, '_Browser__client'), 'proxy-client')

    def test_start_request_provider_uses_https_branch(self):
        """Browser.__start_request_provider() should use HTTPS provider when SSL is enabled."""

        browser = self.make_browser()
        reader = MagicMock()
        reader.get_user_agents.return_value = ['UA']
        debug = MagicMock()
        config = SimpleNamespace(is_proxy=False, is_ssl=True)

        setattr(browser, '_Browser__reader', reader)
        setattr(browser, '_Browser__debug', debug)
        setattr(browser, '_Browser__config', config)

        with patch('src.lib.browser.browser.request_https', return_value='https-client') as https_factory:
            getattr(browser, '_Browser__start_request_provider')()

        https_factory.assert_called_once()
        self.assertEqual(getattr(browser, '_Browser__client'), 'https-client')

    def test_start_request_provider_uses_http_branch(self):
        """Browser.__start_request_provider() should use HTTP provider when SSL is disabled."""

        browser = self.make_browser()
        reader = MagicMock()
        reader.get_user_agents.return_value = ['UA']
        debug = MagicMock()
        config = SimpleNamespace(is_proxy=False, is_ssl=False)

        setattr(browser, '_Browser__reader', reader)
        setattr(browser, '_Browser__debug', debug)
        setattr(browser, '_Browser__config', config)

        with patch('src.lib.browser.browser.request_http', return_value='http-client') as http_factory:
            getattr(browser, '_Browser__start_request_provider')()

        http_factory.assert_called_once()
        self.assertEqual(getattr(browser, '_Browser__client'), 'http-client')

    def test_add_urls_routes_ignored_and_non_ignored_items(self):
        """Browser._add_urls() should send non-ignored URLs to pool and warn on ignored ones."""

        browser = self.make_browser()
        reader = MagicMock()
        reader.total_lines = 25
        reader.get_ignored_list.return_value = ['admin']

        pool = MagicMock()
        pool.add = MagicMock()
        pool.join = MagicMock()

        setattr(browser, '_Browser__reader', reader)
        setattr(browser, '_Browser__pool', pool)
        setattr(browser, '_Browser__catch_report_data', MagicMock())

        urls = [
            'http://example.com/admin',
            'http://example.com/status',
        ]

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            browser._add_urls(urls)

        pool.add.assert_called_once()
        pool.join.assert_called_once()
        getattr(browser, '_Browser__catch_report_data').assert_any_call('ignored', 'http://example.com/admin')
        warning_mock.assert_called_once()

    def test_done_processes_reports_only_when_queue_is_empty(self):
        """Browser.done() should process reports only when the thread pool is drained."""

        browser = self.make_browser()
        config = SimpleNamespace(reports=['html', 'json'], host='test.local')
        pool = SimpleNamespace(total_items_size=20, workers_size=4, size=0)
        result = {'total': {}, 'items': {'success': ['http://example.com']}}

        setattr(browser, '_Browser__config', config)
        setattr(browser, '_Browser__pool', pool)
        setattr(browser, '_Browser__result', result)

        html_report = MagicMock()
        json_report = MagicMock()

        with patch('src.lib.browser.browser.Reporter.load', side_effect=[html_report, json_report]) as load_mock:
            browser.done()

        self.assertEqual(result['total']['items'], 20)
        self.assertEqual(result['total']['workers'], 4)
        self.assertEqual(load_mock.call_count, 2)
        html_report.process.assert_called_once()
        json_report.process.assert_called_once()

    def test_done_skips_reporting_when_queue_is_not_empty(self):
        """Browser.done() should skip report processing when queue still contains items."""

        browser = self.make_browser()
        config = SimpleNamespace(reports=['html'], host='test.local')
        pool = SimpleNamespace(total_items_size=20, workers_size=4, size=3)
        result = {'total': {}, 'items': {}}

        setattr(browser, '_Browser__config', config)
        setattr(browser, '_Browser__pool', pool)
        setattr(browser, '_Browser__result', result)

        with patch('src.lib.browser.browser.Reporter.load') as load_mock:
            browser.done()

        self.assertEqual(result['total']['items'], 20)
        self.assertEqual(result['total']['workers'], 4)
        load_mock.assert_not_called()

    def test_ping_wraps_socket_errors(self):
        """Browser.ping() should wrap socket failures as BrowserError."""

        browser = self.make_browser()
        config = SimpleNamespace(host='example.com', port=80, DEFAULT_SOCKET_TIMEOUT=5)

        setattr(browser, '_Browser__config', config)

        with patch('src.lib.browser.browser.tpl.info'), \
                patch('src.lib.browser.browser.socket.ping', side_effect=SocketError('boom')):
            with self.assertRaises(BrowserError):
                browser.ping()


if __name__ == '__main__':
    unittest.main()