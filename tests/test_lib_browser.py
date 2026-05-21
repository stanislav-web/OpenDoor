# -*- coding: utf-8 -*-

import os
import threading
import unittest
from configparser import RawConfigParser
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.core import filesystem, helper, SocketError, ResponseError, HttpRequestError
from src.core.http.response import Response
from src.lib import BrowserError, ReporterError, browser
from src.lib.browser.browser import Browser
from src.lib.browser.calibration import Calibration
from src.lib.browser.config import Config
from src.lib.browser.debug import Debug
from src.lib.browser.threadpool import ThreadPool
from src.lib.reader.reader import Reader, ReaderError
from src.lib.reporter import Reporter
from src.lib.tpl.tpl import Tpl


class TestBrowser(unittest.TestCase):
    """TestBrowser class."""

    THREADS = 1

    @property
    def configuration(self):
        """Load the test configuration file."""

        test_config = filesystem.getabsname(os.path.join('tests', 'data', 'setup-scan.cfg'))
        config = RawConfigParser()
        config.read(test_config)
        return config

    def setUp(self):
        """Prepare thread pool for each test."""

        self.pool = ThreadPool(num_threads=self.THREADS, total_items=10, timeout=0)
        Reporter.external_directory = None

    def tearDown(self):
        """Cleanup thread pool after each test."""

        Reporter.external_directory = None
        del self.pool

    def browser_configuration(self, params):
        """Build browser configuration object."""

        return Config(params)

    def browser_init(self, params):
        """Initialize browser instance."""

        return browser(params)

    def make_browser(self):
        """Create a browser instance without running __init__."""

        br = browser.__new__(browser)
        setattr(br, '_Browser__result',
                {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()})
        setattr(br, '_Browser__visited_recursive', set())
        setattr(br, '_Browser__queued_recursive', set())
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'scan': 'directories',
            'recursive': False,
            'recursive_depth': 1,
            'recursive_status': '200,301,302,307,308,403',
            'recursive_exclude': 'jpg,jpeg,png,gif,svg,css,js,ico,woff,woff2,ttf,map,pdf,zip,gz,tar',
        }))
        return br

    def test_init(self):
        """Browser.__init__() should initialize all internal collaborators."""

        br = self.browser_init({'host': 'test.local', 'port': 80})
        self.assertIs(getattr(br, '_Browser__client'), None)
        self.assertIsInstance(getattr(br, '_Browser__config'), Config)
        self.assertIsInstance(getattr(br, '_Browser__debug'), Debug)
        self.assertIsInstance(getattr(br, '_Browser__result'), dict)
        self.assertIsInstance(getattr(br, '_Browser__reader'), Reader)
        self.assertIsInstance(getattr(br, '_Browser__pool'), ThreadPool)
        self.assertIsInstance(getattr(br, '_Browser__response'), Response)

    def test_init_exception(self):
        """Browser.__init__() should wrap reader/response setup errors into BrowserError."""

        with self.assertRaises(BrowserError):
            self.browser_init({'host': 'test.local', 'port': 80, 'wordlist': '/wrong'})

    def test_init_sets_external_report_directory(self):
        """Browser.__init__() should set Reporter.external_directory for external report paths."""

        with patch('src.lib.browser.browser.Config') as config_cls, \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader') as reader_cls, \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool') as pool_cls, \
                patch('src.lib.browser.browser.response', return_value=MagicMock()):

            cfg = SimpleNamespace(
                scan='directories',
                DEFAULT_SCAN='directories',
                proxy_list=None,
                is_random_list=False,
                is_extension_filter=False,
                is_ignore_extension_filter=False,
                is_external_wordlist=False,
                wordlist='',
                is_standalone_proxy=False,
                is_external_proxy_list=False,
                prefix='',
                is_external_reports_dir=True,
                reports_dir='/custom/reports',
                extensions=[],
                ignore_extensions=[],
                threads=1,
                delay=0,
            )
            config_cls.return_value = cfg

            reader = MagicMock()
            reader.total_lines = 5
            reader_cls.return_value = reader
            pool_cls.return_value = MagicMock()

            browser({'host': 'test.local', 'port': 80})

        self.assertEqual(Reporter.external_directory, '/custom/reports')

    def test_init_applies_ignore_extension_filter_on_default_scan(self):
        """Browser.__init__() should build ignore_extensionlist when ignore-extension mode is enabled."""

        with patch('src.lib.browser.browser.Config') as config_cls, \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader') as reader_cls, \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()):

            cfg = SimpleNamespace(
                scan='directories',
                DEFAULT_SCAN='directories',
                proxy_list=None,
                is_random_list=False,
                is_extension_filter=False,
                is_ignore_extension_filter=True,
                is_external_wordlist=False,
                wordlist='',
                is_standalone_proxy=False,
                is_external_proxy_list=False,
                prefix='',
                is_external_reports_dir=False,
                reports_dir='',
                extensions=[],
                ignore_extensions=['jpg', 'png'],
                threads=1,
                delay=0,
            )
            config_cls.return_value = cfg

            reader = MagicMock()
            reader.total_lines = 5
            reader_cls.return_value = reader

            browser({'host': 'test.local', 'port': 80})

        reader.filter_by_ignore_extension.assert_called_once_with(
            target='directories',
            output='ignore_extensionlist',
            extensions=['jpg', 'png'],
        )
        reader.filter_by_extension.assert_not_called()

    def test_init_skips_filtering_for_non_default_scan(self):
        """Browser.__init__() should skip extension filtering for non-default scans."""

        with patch('src.lib.browser.browser.Config') as config_cls, \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader') as reader_cls, \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()):

            cfg = SimpleNamespace(
                scan='subdomains',
                DEFAULT_SCAN='directories',
                proxy_list=None,
                is_random_list=False,
                is_extension_filter=True,
                is_ignore_extension_filter=True,
                is_external_wordlist=False,
                wordlist='',
                is_standalone_proxy=False,
                is_external_proxy_list=False,
                prefix='',
                is_external_reports_dir=False,
                reports_dir='',
                extensions=['php'],
                ignore_extensions=['jpg'],
                threads=1,
                delay=0,
            )
            config_cls.return_value = cfg

            reader = MagicMock()
            reader.total_lines = 5
            reader_cls.return_value = reader

            browser({'host': 'test.local', 'port': 80})

        reader.filter_by_extension.assert_not_called()
        reader.filter_by_ignore_extension.assert_not_called()

    def test_init_wraps_response_factory_error(self):
        """Browser.__init__() should wrap response factory failures into BrowserError."""

        with patch('src.lib.browser.browser.Config') as config_cls, \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader') as reader_cls, \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', side_effect=ResponseError('boom')):

            cfg = SimpleNamespace(
                scan='directories',
                DEFAULT_SCAN='directories',
                proxy_list=None,
                is_random_list=False,
                is_extension_filter=False,
                is_ignore_extension_filter=False,
                is_external_wordlist=False,
                wordlist='',
                is_standalone_proxy=False,
                is_external_proxy_list=False,
                prefix='',
                is_external_reports_dir=False,
                reports_dir='',
                extensions=[],
                ignore_extensions=[],
                threads=1,
                delay=0,
            )
            config_cls.return_value = cfg

            reader = MagicMock()
            reader.total_lines = 5
            reader_cls.return_value = reader

            with self.assertRaises(BrowserError):
                browser({'host': 'test.local', 'port': 80})

    def test_ping(self):
        """Browser.ping() should check socket connectivity and resolve host IP."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({'reports': 'std', 'host': 'example.com', 'port': 80}))

        with patch('src.lib.browser.browser.socket.ping', return_value=None) as mock_ping, \
                patch('src.lib.browser.browser.socket.get_ips_addresses', return_value='[127.0.0.1]') as mock_ips, \
                patch('src.lib.browser.browser.socket.get_ip_address', return_value='127.0.0.1') as mock_ip:
            self.assertIs(br.ping(), None)
            mock_ping.assert_called_once()
            mock_ips.assert_called_once_with('example.com')
            mock_ip.assert_not_called()

    def test_ping_wraps_socket_errors(self):
        """Browser.ping() should wrap socket failures into BrowserError."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({'reports': 'std', 'host': 'example.com', 'port': 80}))

        with patch('src.lib.browser.browser.socket.ping', side_effect=SocketError('offline')):
            with self.assertRaises(BrowserError):
                br.ping()

    def test_ping_debugs_preflight_failure_details(self):
        """Browser.ping() should print actionable debug details for preflight failures."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({'reports': 'std', 'host': 'example.com', 'port': 80}))
        setattr(br, '_Browser__debug', SimpleNamespace(is_scan_debug=lambda: True))

        with patch('src.lib.browser.browser.socket.ping', side_effect=SocketError('offline details')), \
                patch('src.lib.browser.browser.tpl.debug') as debug_mock:
            with self.assertRaises(BrowserError):
                br.ping()

        messages = [call.kwargs.get('msg', '') for call in debug_mock.call_args_list]
        self.assertTrue(any('Connection preflight: scheme=' in message for message in messages))
        self.assertTrue(any('Connection preflight failed: offline details' in message for message in messages))

    def test_ping_proxy_mode_checks_proxy_without_direct_target_preflight(self):
        """Browser.ping() should probe explicit proxy endpoint instead of target in proxy mode."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'target.local',
            'port': 443,
            'ssl': True,
            'proxy': 'http://user:pass@127.0.0.1:8080',
            'timeout': 5,
        }))
        setattr(br, '_Browser__debug', SimpleNamespace(is_scan_debug=lambda: True))

        with patch('src.lib.browser.browser.socket.ping', return_value=None) as ping_mock, \
                patch('src.lib.browser.browser.tpl.info') as info_mock, \
                patch('src.lib.browser.browser.tpl.debug') as debug_mock:
            self.assertIsNone(br.ping())

        ping_mock.assert_called_once_with('127.0.0.1', 8080, 5.0)
        self.assertTrue(any(
            'Direct target preflight skipped' in call.kwargs.get('msg', '')
            for call in info_mock.call_args_list
        ))
        self.assertTrue(any(
            'proxy=http://user:*****@127.0.0.1:8080' in call.kwargs.get('msg', '')
            for call in debug_mock.call_args_list
        ))

    def test_ping_proxy_mode_wraps_proxy_preflight_error(self):
        """Browser.ping() should report proxy preflight failures with masked credentials."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'target.local',
            'port': 443,
            'ssl': True,
            'proxy': 'http://user:pass@127.0.0.1:8080',
            'timeout': 5,
        }))
        setattr(br, '_Browser__debug', SimpleNamespace(is_scan_debug=lambda: True))

        with patch('src.lib.browser.browser.socket.ping', side_effect=SocketError('offline')), \
                patch('src.lib.browser.browser.tpl.debug') as debug_mock:
            with self.assertRaises(BrowserError) as context:
                br.ping()

        self.assertIn('Proxy preflight failed for http://user:*****@127.0.0.1:8080', str(context.exception))
        self.assertNotIn('pass', str(context.exception))
        self.assertTrue(any(
            'Proxy preflight failed for http://user:*****@127.0.0.1:8080' in call.kwargs.get('msg', '')
            for call in debug_mock.call_args_list
        ))

    def test_mask_proxy_url_should_preserve_plain_proxy_without_credentials(self):
        """Browser should not rewrite proxy URLs when no credentials are present."""

        mask_proxy_url = getattr(Browser, '_Browser__mask_proxy_url')

        self.assertEqual(mask_proxy_url('http://proxy.local:8080'), 'http://proxy.local:8080')

    def test_mask_proxy_url_should_mask_ipv6_and_password_only_credentials(self):
        """Browser should mask proxy credentials for IPv6 and password-only URLs."""

        mask_proxy_url = getattr(Browser, '_Browser__mask_proxy_url')

        self.assertEqual(mask_proxy_url('http://user:pass@[::1]:8080'), 'http://user:*****@[::1]:8080')
        self.assertEqual(mask_proxy_url('http://:pass@proxy.local:8080'), 'http://*****@proxy.local:8080')
        self.assertEqual(mask_proxy_url('http://user:pass@proxy.local'), 'http://user:*****@proxy.local')

    def test_proxy_endpoint_should_resolve_default_proxy_ports(self):
        """Browser should resolve default proxy ports for schemes with omitted ports."""

        proxy_endpoint = getattr(Browser, '_Browser__proxy_endpoint')

        self.assertEqual(proxy_endpoint('http://user:pass@proxy.local'), ('proxy.local', 80, 'http://user:*****@proxy.local'))
        self.assertEqual(proxy_endpoint('https://user:pass@proxy.local'), ('proxy.local', 443, 'https://user:*****@proxy.local'))
        self.assertEqual(proxy_endpoint('socks5h://user:pass@proxy.local'), ('proxy.local', 80, 'socks5h://user:*****@proxy.local'))

    def test_proxy_endpoint_should_reject_invalid_proxy_urls_without_leaking_passwords(self):
        """Browser should reject invalid proxy URLs while keeping credentials masked."""

        proxy_endpoint = getattr(Browser, '_Browser__proxy_endpoint')

        with self.assertRaises(BrowserError) as invalid_port_context:
            proxy_endpoint('http://user:pass@proxy.local:bad')

        self.assertIn('http://user:*****@proxy.local', str(invalid_port_context.exception))
        self.assertNotIn('pass', str(invalid_port_context.exception))

        with self.assertRaises(BrowserError) as missing_host_context:
            proxy_endpoint('http://user:pass@:8080')

        self.assertIn('proxy host and port are required', str(missing_host_context.exception))
        self.assertNotIn('pass', str(missing_host_context.exception))

    def test_mask_proxy_url_fallback_should_mask_malformed_proxy_credentials(self):
        """Browser should mask credentials even when URL parsing fails."""

        mask_proxy_url = getattr(Browser, '_Browser__mask_proxy_url')

        with patch('src.lib.browser.browser.urlsplit', side_effect=ValueError('bad proxy url')):
            self.assertEqual(
                mask_proxy_url('http://user:pass@proxy.local:8080'),
                'http://user:*****@proxy.local:8080',
            )
            self.assertEqual(
                mask_proxy_url('http://:pass@proxy.local:8080'),
                'http://*****@proxy.local:8080',
            )
            self.assertEqual(mask_proxy_url('not-a-proxy-url'), 'not-a-proxy-url')

    def test_proxy_endpoint_should_reject_parse_errors_without_leaking_passwords(self):
        """Browser should keep proxy parse errors masked in preflight diagnostics."""

        proxy_endpoint = getattr(Browser, '_Browser__proxy_endpoint')

        with patch('src.lib.browser.browser.urlsplit', side_effect=ValueError('bad proxy url')):
            with self.assertRaises(BrowserError) as context:
                proxy_endpoint('http://user:pass@proxy.local:8080')

        self.assertIn('Invalid proxy URL http://user:*****@proxy.local:8080', str(context.exception))
        self.assertIn('bad proxy url', str(context.exception))
        self.assertNotIn('pass', str(context.exception))

    def test_proxy_endpoint_should_reject_unknown_scheme_without_default_port(self):
        """Browser should reject proxy schemes without an explicit or default port."""

        proxy_endpoint = getattr(Browser, '_Browser__proxy_endpoint')

        with self.assertRaises(BrowserError) as context:
            proxy_endpoint('ftp://user:pass@proxy.local')

        self.assertIn('proxy host and port are required', str(context.exception))
        self.assertIn('ftp://user:*****@proxy.local', str(context.exception))
        self.assertNotIn('pass', str(context.exception))

    def test_ping_proxy_mode_wraps_proxy_preflight_error_without_debug_output(self):
        """Browser.ping() should wrap proxy preflight failures when debug output is disabled."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'target.local',
            'port': 443,
            'ssl': True,
            'proxy': 'http://user:pass@127.0.0.1:8080',
            'timeout': 5,
            'debug': -1,
        }))
        setattr(br, '_Browser__debug', SimpleNamespace(is_scan_debug=lambda: False))

        with patch('src.lib.browser.browser.socket.ping', side_effect=SocketError('offline')), \
                patch('src.lib.browser.browser.tpl.debug') as debug_mock:
            with self.assertRaises(BrowserError) as context:
                br.ping()

        self.assertIn('Proxy preflight failed for http://user:*****@127.0.0.1:8080', str(context.exception))
        self.assertNotIn('pass', str(context.exception))
        debug_mock.assert_not_called()

    def test_ping_proxy_pool_mode_skips_direct_target_preflight(self):
        """Browser.ping() should skip direct target preflight for proxy pools."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'target.local',
            'port': 443,
            'ssl': True,
            'proxy_pool': True,
            'timeout': 5,
        }))
        setattr(br, '_Browser__debug', SimpleNamespace(is_scan_debug=lambda: True))

        with patch('src.lib.browser.browser.socket.ping') as ping_mock, \
                patch('src.lib.browser.browser.tpl.info') as info_mock:
            self.assertIsNone(br.ping())

        ping_mock.assert_not_called()
        self.assertTrue(any(
            'Direct target preflight skipped' in call.kwargs.get('msg', '')
            for call in info_mock.call_args_list
        ))

    def test_ping_proxy_mode_checks_proxy_without_debug_output(self):
        """Browser.ping() should support proxy preflight when scan debug is disabled."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'target.local',
            'port': 443,
            'ssl': True,
            'proxy': 'http://user:pass@127.0.0.1:8080',
            'timeout': 5,
            'debug': -1,
        }))
        setattr(br, '_Browser__debug', SimpleNamespace(is_scan_debug=lambda: False))

        with patch('src.lib.browser.browser.socket.ping', return_value=None) as ping_mock, \
                patch('src.lib.browser.browser.tpl.debug') as debug_mock:
            self.assertIsNone(br.ping())

        ping_mock.assert_called_once_with('127.0.0.1', 8080, 5.0)
        debug_mock.assert_not_called()

    def test_start_request_provider_uses_proxy_client(self):
        """Browser should choose proxy request provider when proxy mode is enabled."""

        br = self.make_browser()
        config = SimpleNamespace(is_proxy=True, is_ssl=False)
        reader = MagicMock()
        reader.get_proxies.return_value = ['http://proxy:8080']
        reader.get_user_agents.return_value = ['UA']

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__debug', MagicMock())

        with patch('src.lib.browser.browser.request_proxy', return_value='proxy-client') as proxy_mock:
            br._Browser__start_request_provider()

        self.assertEqual(getattr(br, '_Browser__client'), 'proxy-client')
        proxy_mock.assert_called_once()

    def test_start_request_provider_uses_https_client(self):
        """Browser should choose HTTPS request provider when SSL mode is enabled."""

        br = self.make_browser()
        config = SimpleNamespace(is_proxy=False, is_ssl=True)
        reader = MagicMock()
        reader.get_user_agents.return_value = ['UA']

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__debug', MagicMock())

        with patch('src.lib.browser.browser.request_https', return_value='https-client') as https_mock:
            br._Browser__start_request_provider()

        self.assertEqual(getattr(br, '_Browser__client'), 'https-client')
        https_mock.assert_called_once()

    def test_start_request_provider_uses_http_client(self):
        """Browser should choose HTTP request provider for plain HTTP scans."""

        br = self.make_browser()
        config = SimpleNamespace(is_proxy=False, is_ssl=False)
        reader = MagicMock()
        reader.get_user_agents.return_value = ['UA']

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__debug', MagicMock())

        with patch('src.lib.browser.browser.request_http', return_value='http-client') as http_mock:
            br._Browser__start_request_provider()

        self.assertEqual(getattr(br, '_Browser__client'), 'http-client')
        http_mock.assert_called_once()

    def test_http_request_records_ignored_when_response_handler_returns_none(self):
        """Browser.__http_request() should classify handled None as ignored."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = 'response'
        pool = SimpleNamespace(items_size=1, total_items_size=10)
        reader = MagicMock()
        reader.get_ignored_list.return_value = ['admin']
        response_handler = MagicMock()
        response_handler.handle.return_value = None

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__response', response_handler)

        br._Browser__http_request('http://example.com/admin')

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['ignored'], 1)
        self.assertEqual(result['items']['ignored'], ['http://example.com/admin'])

    def test_http_request_records_transport_failure_without_bypassing_retries(self):
        """Browser.__http_request() should track missing responses after provider retries are exhausted."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = None
        pool = SimpleNamespace(items_size=1, total_items_size=10)
        response_handler = MagicMock()

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__response', response_handler)

        debug_state = MagicMock()
        debug_state.is_scan_debug.return_value = True
        setattr(br, '_Browser__debug', debug_state)

        with patch('src.lib.browser.browser.tpl.debug') as debug_mock, \
                patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__http_request('http://example.com/admin')

        client.request.assert_called_once_with('http://example.com/admin')
        response_handler.handle.assert_not_called()
        warning_mock.assert_not_called()
        debug_mock.assert_called_once()
        self.assertIn('Consecutive max-retry path failures: 1/10', debug_mock.call_args.kwargs.get('msg', ''))

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['ignored'], 1)
        self.assertEqual(result['items']['ignored'], ['http://example.com/admin'])


    def test_http_request_includes_tls_diagnostic_in_transport_failure(self):
        """Browser transport-failure messages should include provider TLS diagnostics."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = None
        pool = SimpleNamespace(items_size=1, total_items_size=10)
        response_handler = MagicMock()

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__response', response_handler)
        setattr(getattr(br, '_Browser__config'), 'last_transport_error', 'TLS handshake failed: DH_KEY_TOO_SMALL. Retry with --tls-legacy.')

        debug_state = MagicMock()
        debug_state.is_scan_debug.return_value = True
        setattr(br, '_Browser__debug', debug_state)

        with patch('src.lib.browser.browser.tpl.debug') as debug_mock, \
                patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__http_request('https://example.com/admin')

        warning_mock.assert_not_called()
        self.assertIn('DH_KEY_TOO_SMALL', debug_mock.call_args.kwargs.get('msg', ''))
        self.assertIn('--tls-legacy', debug_mock.call_args.kwargs.get('msg', ''))

    def test_http_request_aborts_after_configured_retries_fail_streak(self):
        """Browser.__http_request() should stop after the configured exhausted-retry streak."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = None
        pool = SimpleNamespace(items_size=1, total_items_size=10)
        response_handler = MagicMock()

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__response', response_handler)
        setattr(getattr(br, '_Browser__config'), '_retries_fail_streak', 2)

        br._Browser__http_request('http://example.com/first')

        with self.assertRaises(BrowserError) as context:
            br._Browser__http_request('http://example.com/second')

        self.assertIn('Aborting scan after 2 consecutive request(s) exhausted configured --retries', str(context.exception))
        self.assertIn('--retries-fail-streak', str(context.exception))
        self.assertEqual(client.request.call_count, 2)
        client.request.assert_any_call('http://example.com/first')
        client.request.assert_any_call('http://example.com/second')
        response_handler.handle.assert_not_called()

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['ignored'], 2)
        self.assertEqual(result['items']['ignored'], ['http://example.com/first', 'http://example.com/second'])

    def test_http_request_does_not_abort_before_default_retries_fail_streak(self):
        """Browser.__http_request() should keep max-retry paths skipped until the default threshold."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = None
        pool = SimpleNamespace(items_size=1, total_items_size=10)
        response_handler = MagicMock()

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__response', response_handler)

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__http_request('http://example.com/.well')
            br._Browser__http_request('http://example.com/.idea/dictionaries')

        self.assertEqual(client.request.call_count, 2)
        client.request.assert_any_call('http://example.com/.well')
        client.request.assert_any_call('http://example.com/.idea/dictionaries')
        response_handler.handle.assert_not_called()
        warning_mock.assert_not_called()
        self.assertEqual(getattr(br, '_Browser__transport_failure_streak'), 2)

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['ignored'], 2)
        self.assertEqual(
            result['items']['ignored'],
            ['http://example.com/.well', 'http://example.com/.idea/dictionaries']
        )

    def test_http_request_does_not_run_healthcheck_during_max_retry_streak(self):
        """Browser.__http_request() should not add probe requests while counting max-retry paths."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = None
        pool = SimpleNamespace(items_size=1, total_items_size=10)
        response_handler = MagicMock()

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__response', response_handler)
        setattr(getattr(br, '_Browser__config'), '_retries_fail_streak', 3)

        br._Browser__http_request('http://example.com/.well')
        br._Browser__http_request('http://example.com/.git/config')

        self.assertEqual(client.request.call_count, 2)
        self.assertNotIn('http://example.com/', [call.args[0] for call in client.request.call_args_list])
        self.assertEqual(getattr(br, '_Browser__transport_failure_streak'), 2)

    def test_http_request_resets_transport_failure_streak_after_success(self):
        """Browser.__http_request() should not abort when transport recovers between failures."""

        br = self.make_browser()
        client = MagicMock()
        client.request.side_effect = [None, 'response', None]
        pool = SimpleNamespace(items_size=1, total_items_size=10)
        response_handler = MagicMock()
        response_handler.handle.return_value = ('success', 'http://example.com/ok', '1B', '200')

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', MagicMock(get_ignored_list=MagicMock(return_value=[])))
        setattr(br, '_Browser__response', response_handler)

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._Browser__http_request('http://example.com/miss-1')
            br._Browser__http_request('http://example.com/ok')
            br._Browser__http_request('http://example.com/miss-2')

        self.assertEqual(client.request.call_count, 3)
        warning_mock.assert_not_called()
        self.assertEqual(getattr(br, '_Browser__transport_failure_streak'), 1)

    def test_transport_failure_summary_reports_skipped_path_specific_failures(self):
        """Browser should summarize skipped path-specific transport failures once."""

        br = self.make_browser()
        setattr(br, '_Browser__transport_failure_lock', threading.RLock())
        setattr(br, '_Browser__transport_failures_skipped', 3)
        setattr(br, '_Browser__transport_failure_summary_emitted', False)

        with patch('src.lib.browser.browser.tpl.info') as info_mock:
            br._Browser__emit_transport_failure_summary()
            br._Browser__emit_transport_failure_summary()

        info_mock.assert_called_once()
        message = info_mock.call_args.kwargs.get('msg', '')
        self.assertIn('Transport failures skipped: 3 request(s)', message)
        self.assertIn('Scan continued without reaching --retries-fail-streak.', message)

    def test_http_request_records_status_from_response_handler(self):
        """Browser.__http_request() should record the tuple returned by the response handler."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = 'response'
        pool = SimpleNamespace(items_size=2, total_items_size=10)
        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        response_handler = MagicMock()
        response_handler.handle.return_value = ('success', 'http://example.com/login.php', '42B', '200')

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__response', response_handler)

        br._Browser__http_request('http://example.com/login.php')

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['success'], 1)
        self.assertEqual(result['items']['success'], ['http://example.com/login.php'])

    def test_http_request_accepts_depth_argument_without_affecting_handling(self):
        """Browser.__http_request() should accept depth and preserve the existing handling flow."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = 'response'
        pool = SimpleNamespace(items_size=2, total_items_size=10)
        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        response_handler = MagicMock()
        response_handler.handle.return_value = ('success', 'http://example.com/login.php', '42B', '200')

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__response', response_handler)

        br._Browser__http_request('http://example.com/login.php', depth=2)

        client.request.assert_called_once_with('http://example.com/login.php')
        response_handler.handle.assert_called_once_with(
            'response',
            request_url='http://example.com/login.php',
            items_size=2,
            total_size=10,
            ignore_list=[],
            emit_debug=False,
        )
        response_handler.debug_response_data.assert_called_once_with(
            ('success', 'http://example.com/login.php', '42B', '200'),
            request_url='http://example.com/login.php',
            items_size=2,
            total_size=10,
            response='response',
        )

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['success'], 1)
        self.assertEqual(result['items']['success'], ['http://example.com/login.php'])

    def test_http_request_wraps_response_errors(self):
        """Browser.__http_request() should wrap response processing errors into BrowserError."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = 'response'
        pool = SimpleNamespace(items_size=0, total_items_size=0)
        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        response_handler = MagicMock()
        response_handler.handle.side_effect = ResponseError('boom')

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__response', response_handler)

        with self.assertRaises(BrowserError):
            br._Browser__http_request('http://example.com')

    def test_http_request_wraps_client_request_errors(self):
        """Browser.__http_request() should wrap low-level client request failures into BrowserError."""

        br = self.make_browser()
        client = MagicMock()
        client.request.side_effect = HttpRequestError('boom')
        pool = SimpleNamespace(items_size=1, total_items_size=10)
        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        response_handler = MagicMock()

        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__response', response_handler)

        with self.assertRaises(BrowserError):
            br._Browser__http_request('http://example.com')

    def test_is_ignored_checks_normalized_path_against_reader_list(self):
        """Browser.__is_ignored() should compare normalized URL paths with ignored items."""

        br = self.make_browser()
        reader = MagicMock()
        reader.get_ignored_list.return_value = ['admin']
        setattr(br, '_Browser__reader', reader)

        self.assertTrue(br._Browser__is_ignored('http://example.com/admin/'))
        self.assertFalse(br._Browser__is_ignored('http://example.com/login/'))

    def test_add_urls_sends_only_non_ignored_urls_to_pool_with_zero_depth(self):
        """Browser._add_urls() should enqueue only non-ignored URLs and pass root depth as 0."""

        br = self.make_browser()
        pool = MagicMock()
        pool.join.return_value = None
        reader = MagicMock()
        reader.get_ignored_list.return_value = ['admin']
        type(reader).total_lines = property(lambda _self: 20)

        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._add_urls(['http://example.com/admin', 'http://example.com/login'])

        pool.add.assert_called_once_with(
            getattr(br, '_Browser__http_request'),
            'http://example.com/login',
            0
        )
        pool.join.assert_called_once_with()
        warning_mock.assert_called_once()

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['ignored'], 1)
        self.assertEqual(result['items']['ignored'], ['http://example.com/admin'])

    def test_add_urls_deduplicates_subdomain_candidates_before_queueing(self):
        """Browser._add_urls() should skip duplicate subdomain URLs before HTTP queueing."""

        br = self.make_browser()
        config = self.browser_configuration({'host': 'example.com', 'scan': 'subdomains', 'reports': 'std'})
        pool = SimpleNamespace(
            total_items_size=3,
            submitted_size=0,
            add=MagicMock(),
            join=MagicMock(),
        )
        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        type(reader).total_lines = property(lambda _self: 3)

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        br._add_urls([
            'http://api.example.com',
            'http://api.example.com',
            'http://admin.example.com',
        ])

        self.assertEqual(pool.add.call_count, 2)
        self.assertEqual(pool.total_items_size, 2)
        self.assertEqual(
            [call.args[1] for call in pool.add.call_args_list],
            ['http://api.example.com', 'http://admin.example.com']
        )
        pool.join.assert_called_once_with()

    def test_add_urls_does_not_shrink_directory_scan_totals_for_duplicate_urls(self):
        """Browser._add_urls() should keep directory scan totals compatible with previous behavior."""

        br = self.make_browser()
        pool = SimpleNamespace(
            total_items_size=2,
            submitted_size=0,
            add=MagicMock(),
            join=MagicMock(),
        )
        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        type(reader).total_lines = property(lambda _self: 2)

        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        br._add_urls([
            'http://example.com/admin',
            'http://example.com/admin',
        ])

        self.assertEqual(pool.add.call_count, 1)
        self.assertEqual(pool.total_items_size, 2)
        pool.join.assert_called_once_with()

    def test_add_urls_deduplicates_subdomain_ignored_candidate_once(self):
        """Browser._add_urls() should report a duplicated ignored subdomain candidate only once."""

        br = self.make_browser()
        config = self.browser_configuration({'host': 'example.com', 'scan': 'subdomains', 'reports': 'std'})
        pool = SimpleNamespace(
            total_items_size=2,
            submitted_size=0,
            add=MagicMock(),
            join=MagicMock(),
        )
        reader = MagicMock()
        reader.get_ignored_list.return_value = ['admin']
        type(reader).total_lines = property(lambda _self: 2)

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br._add_urls([
                'http://admin.example.com/admin',
                'http://admin.example.com/admin',
            ])

        pool.add.assert_not_called()
        self.assertEqual(pool.total_items_size, 1)
        self.assertEqual(getattr(br, '_Browser__result')['total']['ignored'], 1)
        warning_mock.assert_called_once()
        pool.join.assert_called_once_with()

    def test_add_urls_propagates_keyboard_interrupt(self):
        """Browser._add_urls() should re-raise KeyboardInterrupt from the pool layer."""

        br = self.make_browser()
        pool = MagicMock()
        pool.join.side_effect = KeyboardInterrupt
        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        type(reader).total_lines = property(lambda _self: 5)

        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with self.assertRaises(KeyboardInterrupt):
            br._add_urls(['http://example.com/login'])

    def test_scan_randomizes_list_and_reads_urls_when_pool_started(self):
        """Browser.scan() should randomize the selected list and load URLs when the pool is started."""

        br = self.make_browser()
        config = SimpleNamespace(
            is_random_list=True,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=True,
            is_ignore_extension_filter=False,
            host='example.com',
            port=80,
            scheme='http://'
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=10, is_started=True)
        reader = MagicMock()
        reader.total_lines = 10
        reader.count_active_lines.return_value = 10

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with patch.object(br, '_Browser__start_request_provider') as start_provider, \
                patch('src.lib.browser.browser.tpl.info') as info_mock:
            br.scan()

        self.assertEqual(config.scan, 'extensionlist')
        reader.randomize_list.assert_called_once_with(target='extensionlist', output='tmplist')
        reader.get_lines.assert_called_once()
        start_provider.assert_called_once_with()
        debug.debug_user_agents.assert_called_once_with()
        debug.debug_list.assert_called_once_with(total_lines=10)
        info_mock.assert_any_call(key='scanning', host='example.com')

    def test_scan_randomizes_ignore_extension_list(self):
        """Browser.scan() should switch to ignore_extensionlist when randomizing ignored extensions."""

        br = self.make_browser()
        config = SimpleNamespace(
            is_random_list=True,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=True,
            host='example.com',
            port=80,
            scheme='http://'
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=10, is_started=True)
        reader = MagicMock()
        reader.total_lines = 10
        reader.count_active_lines.return_value = 10

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with patch.object(br, '_Browser__start_request_provider') as start_provider, \
                patch('src.lib.browser.browser.tpl.info'):
            br.scan()

        self.assertEqual(config.scan, 'ignore_extensionlist')
        reader.randomize_list.assert_called_once_with(target='ignore_extensionlist', output='tmplist')
        reader.get_lines.assert_called_once()
        start_provider.assert_called_once_with()

    def test_scan_randomizes_non_default_scan_without_rewriting_target(self):
        """Browser.scan() should randomize the current non-default scan target as-is."""

        br = self.make_browser()
        config = SimpleNamespace(
            is_random_list=True,
            scan='subdomains',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=False,
            host='example.com',
            port=80,
            scheme='http://'
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=10, is_started=True)
        reader = MagicMock()
        reader.total_lines = 10
        reader.count_active_lines.return_value = 10

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with patch.object(br, '_Browser__start_request_provider') as start_provider, \
                patch('src.lib.browser.browser.tpl.info'):
            br.scan()

        self.assertEqual(config.scan, 'subdomains')
        reader.randomize_list.assert_called_once_with(target='subdomains', output='tmplist')
        reader.get_lines.assert_called_once()
        start_provider.assert_called_once_with()

    def test_scan_restarts_existing_direct_request_provider_after_scan_target_rewrite(self):
        """Browser.scan() should refresh direct clients after random-list scan target rewrites."""

        br = self.make_browser()
        config = SimpleNamespace(
            is_proxy=False,
            is_random_list=True,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=True,
            host='example.com',
            port=80,
            scheme='http://'
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=10, is_started=True)
        reader = MagicMock()
        reader.total_lines = 10
        reader.count_active_lines.return_value = 10

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__client', object())

        with patch.object(br, '_Browser__start_request_provider') as start_provider, \
                patch('src.lib.browser.browser.tpl.info'):
            br.scan()

        self.assertEqual(config.scan, 'ignore_extensionlist')
        reader.randomize_list.assert_called_once_with(target='ignore_extensionlist', output='tmplist')
        reader.get_lines.assert_called_once()
        start_provider.assert_called_once_with()

    def test_scan_reuses_existing_proxy_request_provider(self):
        """Browser.scan() should keep proxy pools initialized by fingerprint/calibration setup."""

        br = self.make_browser()
        config = SimpleNamespace(
            is_proxy=True,
            is_random_list=False,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=False,
            host='example.com',
            port=80,
            scheme='http://'
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=10, is_started=True)
        reader = MagicMock()
        reader.count_active_lines.return_value = 10

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__client', object())

        with patch.object(br, '_Browser__start_request_provider') as start_provider, \
                patch('src.lib.browser.browser.tpl.info'):
            br.scan()

        start_provider.assert_not_called()
        reader.get_lines.assert_called_once()

    def test_scan_skips_loading_lines_when_pool_is_not_started(self):
        """Browser.scan() should not request lines when the thread pool is paused."""

        br = self.make_browser()
        config = SimpleNamespace(
            is_random_list=False,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=False,
            host='example.com',
            port=80,
            scheme='http://'
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=10, is_started=False)
        reader = MagicMock()
        reader.count_active_lines.return_value = 10

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with patch.object(br, '_Browser__start_request_provider') as start_provider, \
                patch('src.lib.browser.browser.tpl.info'):
            br.scan()

        reader.get_lines.assert_not_called()
        start_provider.assert_called_once_with()

    def test_scan_wraps_reader_errors(self):
        """Browser.scan() should wrap reader failures into BrowserError."""

        br = self.make_browser()
        config = SimpleNamespace(
            is_random_list=True,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=False,
            host='example.com',
            port=80,
            scheme='http://'
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=10, is_started=True)
        reader = MagicMock()
        reader.count_active_lines.return_value = 10
        reader.randomize_list.side_effect = ReaderError('bad list')

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with self.assertRaises(BrowserError):
            br.scan()

    def test_scan_wraps_request_provider_start_errors(self):
        """Browser.scan() should wrap request provider initialization errors into BrowserError."""

        br = self.make_browser()
        config = SimpleNamespace(
            is_random_list=False,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=False,
            host='example.com',
            port=80,
            scheme='http://'
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=10, is_started=True)
        reader = MagicMock()
        reader.count_active_lines.return_value = 10

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with patch.object(br, '_Browser__start_request_provider', side_effect=HttpRequestError('boom')), \
                patch('src.lib.browser.browser.tpl.info'):
            with self.assertRaises(BrowserError):
                br.scan()

    def test_scan_aborts_when_active_wordlist_is_shorter_than_planned_total(self):
        """Browser.scan() should not silently finish a partial runtime wordlist."""

        br = self.make_browser()
        config = SimpleNamespace(
            is_random_list=True,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=True,
            host='example.com',
            port=80,
            scheme='http://'
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=93661, is_started=True)
        reader = MagicMock()
        reader.total_lines = 93661
        reader.count_active_lines.return_value = 4167

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            with self.assertRaises(BrowserError) as ctx:
                br.scan()

        self.assertIn('planned 93661 item(s), active runtime list has 4167', str(ctx.exception))
        warning_mock.assert_called_with(msg='Active scan list size mismatch: planned 93661 item(s), active runtime list has 4167. Aborting to avoid a partial scan.')
        reader.get_lines.assert_not_called()



    def test_prepare_runtime_paths_skips_workspace_without_temp_outputs(self):
        """Browser should not allocate a temp workspace when no runtime wordlist is generated."""

        br = Browser.__new__(Browser)
        config = SimpleNamespace(
            is_random_list=False,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=False,
        )
        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__temp_workspace', None)

        self.assertEqual(br._Browser__prepare_runtime_paths(), {})
        self.assertIsNone(getattr(br, '_Browser__temp_workspace'))

    def test_prepare_runtime_paths_allocates_workspace_for_random_scan(self):
        """Browser should allocate a workspace before random-list generation."""

        br = Browser.__new__(Browser)
        workspace = MagicMock()
        workspace.paths = {'tmplist': '/tmp/opendoor-scan-x/list.tmp'}
        config = SimpleNamespace(
            is_random_list=True,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=False,
        )
        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__temp_workspace', None)

        with patch('src.lib.browser.browser.ScanTempWorkspace', return_value=workspace):
            self.assertEqual(br._Browser__prepare_runtime_paths(), workspace.paths)

        self.assertIs(getattr(br, '_Browser__temp_workspace'), workspace)

    def test_scan_cleans_temp_workspace_on_success(self):
        """Browser.scan() should cleanup its managed workspace after normal completion."""

        br = self.make_browser()
        workspace = MagicMock()
        config = SimpleNamespace(
            is_random_list=False,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=False,
            host='example.com',
            port=80,
            scheme='http://',
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=10, is_started=True)
        reader = MagicMock()

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__temp_workspace', workspace)

        with patch.object(br, '_Browser__start_request_provider'), \
                patch('src.lib.browser.browser.tpl.info'):
            br.scan()

        workspace.cleanup.assert_called_once_with()
        self.assertIsNone(getattr(br, '_Browser__temp_workspace'))

    def test_scan_cleans_temp_workspace_on_browser_error(self):
        """Browser.scan() should cleanup its managed workspace when scan startup fails."""

        br = self.make_browser()
        workspace = MagicMock()
        config = SimpleNamespace(
            is_random_list=True,
            scan='directories',
            DEFAULT_SCAN='directories',
            is_extension_filter=False,
            is_ignore_extension_filter=False,
            host='example.com',
            port=80,
            scheme='http://',
        )
        debug = MagicMock()
        pool = SimpleNamespace(total_items_size=10, is_started=True)
        reader = MagicMock()
        reader.randomize_list.side_effect = ReaderError('bad list')

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__temp_workspace', workspace)

        with self.assertRaises(BrowserError):
            br.scan()

        workspace.cleanup.assert_called_once_with()
        self.assertIsNone(getattr(br, '_Browser__temp_workspace'))

    def test_done_warns_when_streaming_finishes_before_all_planned_items_are_submitted(self):
        """Browser.done() should explain early EOF instead of only printing the final summary."""

        br = self.make_browser()
        config = SimpleNamespace(reports=[])
        pool = SimpleNamespace(
            total_items_size=93661,
            submitted_size=4167,
            workers_size=1,
            size=0,
        )

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__session', None)
        setattr(br, '_Browser__session_dirty', False)

        with patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            br.done()

        warning_mock.assert_called_once()
        message = warning_mock.call_args.kwargs['msg']
        self.assertIn('consuming 4167/93661 planned item(s)', message)
        self.assertIn('(4167 submitted to workers)', message)
        self.assertIn('active wordlist ended early or was changed during streaming', message)

    def test_catch_report_data_initializes_report_items_when_missing(self):
        """Browser.__catch_report_data() should restore report_items when old payloads do not have it."""

        br = browser.__new__(browser)
        setattr(br, '_Browser__result', {'total': helper.counter(), 'items': helper.list()})

        br._Browser__catch_report_data('success', 'http://example.com/admin', '5B', '200')

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['items']['success'], ['http://example.com/admin'])
        self.assertEqual(result['report_items']['success'], [{'url': 'http://example.com/admin', 'size': '5B', 'code': '200'}])

    def test_catch_report_data_keeps_waf_metadata_for_blocked_items(self):
        """Browser.__catch_report_data() should persist WAF metadata into detailed report items."""

        br = browser.__new__(browser)
        setattr(br, '_Browser__result', {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()})

        br._Browser__catch_report_data(
            'blocked',
            'https://example.com/login',
            '25B',
            '200',
            metadata={
                'name': 'Cloudflare',
                'confidence': 92,
                'signals': ['header:cf-ray', 'header:server: cloudflare'],
            }
        )

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['items']['blocked'], ['https://example.com/login'])
        self.assertEqual(
            result['report_items']['blocked'],
            [{
                'url': 'https://example.com/login',
                'size': '25B',
                'code': '200',
                'waf': 'Cloudflare',
                'waf_confidence': 92,
                'waf_signals': ['header:cf-ray', 'header:server: cloudflare'],
            }]
        )

    def test_done_processes_reports_when_queue_is_empty(self):
        """Browser.done() should load and process all configured reports when the queue is the queue is empty."""

        br = self.make_browser()
        setattr(br, '_Browser__pool', SimpleNamespace(total_items_size=10, workers_size=2, size=0))
        setattr(br, '_Browser__config', SimpleNamespace(reports=['std', 'json'], host='test.local'))
        report_one = MagicMock()
        report_two = MagicMock()

        with patch('src.lib.browser.browser.Reporter.load', side_effect=[report_one, report_two]) as load_mock:
            br.done()

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['items'], 10)
        self.assertEqual(result['total']['workers'], 2)
        self.assertEqual(load_mock.call_count, 2)
        report_one.process.assert_called_once_with()
        report_two.process.assert_called_once_with()

    def test_done_passes_enriched_result_to_reporter(self):
        """Browser.done() should pass report_items metadata into Reporter.load()."""

        br = self.make_browser()
        result = {
            'total': helper.counter(),
            'items': helper.list(),
            'report_items': helper.list(),
        }
        result['items']['success'] += ['http://example.com/admin']
        result['report_items']['success'] += [{'url': 'http://example.com/admin', 'size': '5B', 'code': '200'}]

        setattr(br, '_Browser__result', result)
        setattr(br, '_Browser__pool', SimpleNamespace(total_items_size=1, workers_size=1, size=0))
        setattr(br, '_Browser__config', SimpleNamespace(reports=['json'], host='test.local'))

        report = MagicMock()
        with patch('src.lib.browser.browser.Reporter.load', return_value=report) as load_mock:
            br.done()

        passed_result = load_mock.call_args[0][2]
        self.assertIn('report_items', passed_result)
        self.assertEqual(
            passed_result['report_items']['success'],
            [{'url': 'http://example.com/admin', 'size': '5B', 'code': '200'}]
        )
        report.process.assert_called_once_with()

    def test_done_prints_debug_runtime_diagnostics_before_reports(self):
        """Browser.done() should print terminal-only runtime diagnostics when debug is enabled."""

        br = self.make_browser()
        total = helper.counter()
        total.update({'calibrated': 3})
        result = {'total': total, 'items': helper.list(), 'report_items': helper.list()}
        config = SimpleNamespace(
            reports=[],
            host='test.local',
            retries_fail_streak=30,
            is_auto_calibrate=True,
        )
        debug = SimpleNamespace(is_scan_debug=lambda: True)
        pool = SimpleNamespace(
            total_items_size=10,
            submitted_size=9,
            workers_size=1,
            size=0,
            items_size=9,
            completed_size=9,
        )

        setattr(br, '_Browser__result', result)
        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__streamed_items_count', 10)
        setattr(br, '_Browser__pre_request_skipped', 1)
        setattr(br, '_Browser__transport_failures_skipped', 2)
        setattr(br, '_Browser__transport_failure_summary_emitted', True)
        setattr(br, '_Browser__runtime_active_seconds_offset', 2.0)
        setattr(br, '_Browser__runtime_diagnostics_emitted', False)

        with patch('src.lib.browser.browser.tpl.info') as info_mock:
            br.done()

        diagnostic_messages = [
            call.kwargs.get('msg', '')
            for call in info_mock.call_args_list
            if 'Runtime diagnostics' in call.kwargs.get('msg', '')
        ]
        self.assertEqual(len(diagnostic_messages), 1)
        rendered = diagnostic_messages[0]
        self.assertIn('Progress:          10/10 (100.0%)', rendered)
        self.assertIn('Requests:          9 submitted, 1 skipped before request', rendered)
        self.assertIn('Rate:              5.0/s average', rendered)
        self.assertIn('Time:              active 00:00:02, remaining 00:00:00', rendered)
        self.assertIn('Retries:           exhausted transport paths 2, fail streak 0/30', rendered)
        self.assertIn('Calibration:       enabled, 3 responses suppressed', rendered)
        self.assertNotIn('Response filters:', rendered)
        self.assertNotIn('Sniffers:', rendered)
        self.assertNotIn('WAF detection:', rendered)
        self.assertNotIn('WAF safe mode:', rendered)
        self.assertNotIn('Status:', rendered)

    def test_done_does_not_print_runtime_diagnostics_without_debug(self):
        """Browser.done() should keep normal summary output unchanged when debug is disabled."""

        br = self.make_browser()
        setattr(br, '_Browser__pool', SimpleNamespace(
            total_items_size=1,
            submitted_size=1,
            workers_size=1,
            size=0,
            items_size=1,
            completed_size=1,
        ))
        setattr(br, '_Browser__config', SimpleNamespace(reports=[], host='test.local'))
        setattr(br, '_Browser__debug', SimpleNamespace(is_scan_debug=lambda: False))

        with patch('src.lib.browser.browser.tpl.info') as info_mock:
            br.done()

        self.assertFalse(any(
            'Runtime diagnostics' in call.kwargs.get('msg', '')
            for call in info_mock.call_args_list
        ))

    def test_runtime_diagnostics_marks_interrupted_scans(self):
        """Browser runtime diagnostics should estimate remaining time for interrupted scans."""

        br = self.make_browser()
        setattr(br, '_Browser__pool', SimpleNamespace(
            total_items_size=10,
            submitted_size=5,
            workers_size=1,
            size=0,
            items_size=5,
            completed_size=5,
        ))
        setattr(br, '_Browser__config', SimpleNamespace(
            retries_fail_streak=30,
            is_auto_calibrate=False,
        ))
        setattr(br, '_Browser__runtime_active_seconds_offset', 10.0)

        rendered = br._Browser__format_runtime_diagnostics(status='interrupted')

        self.assertIn('Progress:          5/10 (50.0%)', rendered)
        self.assertIn('Rate:              0.5/s average', rendered)
        self.assertIn('Time:              active 00:00:10, remaining 00:00:10', rendered)
        self.assertIn('Status:            interrupted', rendered)

    def test_runtime_clock_accumulates_active_time_without_double_counting(self):
        """Browser runtime clock should accumulate active scan time safely."""

        br = self.make_browser()

        with patch('src.lib.browser.browser.time.monotonic', side_effect=[100.0, 102.25, 105.75]):
            br._Browser__start_runtime_clock()
            br._Browser__start_runtime_clock()

            self.assertAlmostEqual(br._Browser__active_runtime_seconds(), 2.25)

            br._Browser__stop_runtime_clock()

        self.assertIsNone(getattr(br, '_Browser__runtime_started_at'))
        self.assertAlmostEqual(getattr(br, '_Browser__runtime_active_seconds_offset'), 5.75)

        br._Browser__stop_runtime_clock()
        self.assertAlmostEqual(getattr(br, '_Browser__runtime_active_seconds_offset'), 5.75)

        setattr(br, '_Browser__runtime_started_at', 200.0)
        setattr(br, '_Browser__runtime_finished_at', 201.0)
        br._Browser__stop_runtime_clock()
        self.assertAlmostEqual(getattr(br, '_Browser__runtime_active_seconds_offset'), 5.75)

    def test_runtime_diagnostics_handles_zero_totals_and_malformed_result_counters(self):
        """Browser runtime diagnostics should stay stable with empty counters."""

        br = self.make_browser()
        setattr(br, '_Browser__pool', SimpleNamespace(
            total_items_size=0,
            submitted_size='bad',
            workers_size='2',
            size=0,
            items_size='bad',
            completed_size='bad',
        ))
        setattr(br, '_Browser__config', SimpleNamespace(
            retries_fail_streak=10,
            is_auto_calibrate=False,
        ))
        setattr(br, '_Browser__result', {'total': 'bad', 'items': helper.list(), 'report_items': helper.list()})

        rendered = br._Browser__format_runtime_diagnostics(status='completed')

        self.assertIn('Progress:          0/0 (0.0%)', rendered)
        self.assertIn('Requests:          0 submitted, 0 skipped before request', rendered)
        self.assertIn('Rate:              0.0/s average', rendered)
        self.assertIn('Threads:           2', rendered)
        self.assertIn('Retries:           exhausted transport paths 0, fail streak 0/10', rendered)
        self.assertIn('Calibration:       disabled, 0 responses suppressed', rendered)
        self.assertNotIn('Status:', rendered)

    def test_emit_runtime_diagnostics_is_idempotent(self):
        """Browser runtime diagnostics should not print more than once."""

        br = self.make_browser()
        setattr(br, '_Browser__pool', SimpleNamespace(
            total_items_size=1,
            submitted_size=1,
            workers_size=1,
            size=0,
            items_size=1,
            completed_size=1,
        ))
        setattr(br, '_Browser__config', SimpleNamespace(
            retries_fail_streak=30,
            is_auto_calibrate=True,
        ))
        setattr(br, '_Browser__debug', SimpleNamespace(is_scan_debug=lambda: True))
        setattr(br, '_Browser__runtime_diagnostics_emitted', True)

        with patch('src.lib.browser.browser.tpl.info') as info_mock:
            emitted = br._Browser__emit_runtime_diagnostics(status='completed')

        self.assertFalse(emitted)
        info_mock.assert_not_called()

    def test_done_skips_report_generation_when_queue_is_not_empty(self):
        """Browser.done() should skip reporting while there are still queued items."""

        br = self.make_browser()
        setattr(br, '_Browser__pool', SimpleNamespace(total_items_size=10, workers_size=2, size=1))
        setattr(br, '_Browser__config', SimpleNamespace(reports=['std'], host='test.local'))

        with patch('src.lib.browser.browser.Reporter.load') as load_mock:
            br.done()

        load_mock.assert_not_called()

    def test_done_wraps_reporter_errors(self):
        """Browser.done() should wrap reporter failures into BrowserError."""

        br = self.make_browser()
        setattr(br, '_Browser__pool', SimpleNamespace(total_items_size=10, workers_size=2, size=0))
        setattr(br, '_Browser__config', SimpleNamespace(reports=['raisesexc'], host='test.local'))

        with patch('src.lib.browser.browser.Reporter.load', side_effect=ReporterError('raisesexc')):
            with self.assertRaises(BrowserError):
                br.done()

    def test_should_expand_recursively_returns_false_when_recursive_is_disabled(self):
        """Browser recursive expansion should stay disabled when the feature is turned off."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'scan': 'directories',
            'recursive': False,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }))

        actual = br._Browser__should_expand_recursively('200', 'http://example.com/admin', 0)

        self.assertFalse(actual)

    def test_should_expand_recursively_returns_false_for_non_default_scan(self):
        """Browser recursive expansion should stay disabled for non-default scan types."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'scan': 'subdomains',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }))

        actual = br._Browser__should_expand_recursively('200', 'http://example.com/admin', 0)

        self.assertFalse(actual)

    def test_should_expand_recursively_respects_depth_limit(self):
        """Browser recursive expansion should stop at the configured depth."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'scan': 'directories',
            'recursive': True,
            'recursive_depth': 1,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }))

        actual = br._Browser__should_expand_recursively('200', 'http://example.com/admin', 1)

        self.assertFalse(actual)

    def test_should_expand_recursively_respects_allowed_statuses(self):
        """Browser recursive expansion should only allow configured HTTP statuses."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'scan': 'directories',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }))

        self.assertTrue(br._Browser__should_expand_recursively('200', 'http://example.com/admin', 0))
        self.assertTrue(br._Browser__should_expand_recursively('403', 'http://example.com/admin', 0))
        self.assertFalse(br._Browser__should_expand_recursively('302', 'http://example.com/admin', 0))

    def test_should_expand_recursively_skips_excluded_extensions(self):
        """Browser recursive expansion should skip excluded file extensions."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'scan': 'directories',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png,css',
        }))

        self.assertFalse(br._Browser__should_expand_recursively('200', 'http://example.com/assets/logo.png', 0))
        self.assertFalse(br._Browser__should_expand_recursively('200', 'http://example.com/assets/site.css', 0))
        self.assertTrue(br._Browser__should_expand_recursively('200', 'http://example.com/admin', 0))

    def test_build_recursive_url_should_build_nested_path_from_root(self):
        """Browser should build nested recursive URLs from a root-level parent path."""

        br = self.make_browser()

        actual = br._Browser__build_recursive_url('http://example.com', 'admin')

        self.assertEqual(actual, 'http://example.com/admin')

    def test_build_recursive_url_should_build_nested_path_from_existing_directory(self):
        """Browser should build nested recursive URLs from an existing directory path."""

        br = self.make_browser()

        actual = br._Browser__build_recursive_url('http://example.com/admin/', 'panel')

        self.assertEqual(actual, 'http://example.com/admin/panel')

    def test_build_recursive_url_should_strip_leading_slash_and_ignore_empty_suffix(self):
        """Browser recursive URL builder should normalize suffixes and ignore empty values."""

        br = self.make_browser()

        self.assertEqual(
            br._Browser__build_recursive_url('http://example.com/admin', '/panel'),
            'http://example.com/admin/panel'
        )
        self.assertIsNone(br._Browser__build_recursive_url('http://example.com/admin', ''))
        self.assertIsNone(br._Browser__build_recursive_url('http://example.com/admin', '   '))

    def test_enqueue_recursive_children_extends_pool_and_adds_nested_urls(self):
        """Browser should extend the pool and enqueue nested recursive child URLs."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'scan': 'directories',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }))

        pool = MagicMock()
        reader = MagicMock()

        def fake_get_lines(params, loader):
            loader([
                'http://example.com/admin',
                'http://example.com/login',
            ])

        reader.get_lines.side_effect = fake_get_lines

        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        br._Browser__enqueue_recursive_children('http://example.com/panel', 0)

        pool.extend_total_items.assert_called_once_with(2)
        self.assertEqual(
            pool.add.call_args_list,
            [
                unittest.mock.call(getattr(br, '_Browser__http_request'), 'http://example.com/panel/admin', 1),
                unittest.mock.call(getattr(br, '_Browser__http_request'), 'http://example.com/panel/login', 1),
            ]
        )

    def test_enqueue_recursive_children_skips_duplicate_urls(self):
        """Browser recursive enqueue should skip duplicate nested URLs."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'scan': 'directories',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }))

        pool = MagicMock()
        reader = MagicMock()

        def fake_get_lines(params, loader):
            loader([
                'http://example.com/admin',
                'http://example.com/admin',
            ])

        reader.get_lines.side_effect = fake_get_lines

        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        br._Browser__enqueue_recursive_children('http://example.com/panel', 0)

        pool.extend_total_items.assert_called_once_with(1)
        pool.add.assert_called_once_with(
            getattr(br, '_Browser__http_request'),
            'http://example.com/panel/admin',
            1
        )
    def test_enqueue_recursive_children_strips_configured_prefix_from_suffix(self):
        """Browser recursive enqueue should not duplicate the configured prefix inside nested paths."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'prefix': '/api/',
            'scan': 'directories',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }))

        pool = MagicMock()
        reader = MagicMock()

        def fake_get_lines(params, loader):
            loader([
                'http://example.com/api/login',
            ])

        reader.get_lines.side_effect = fake_get_lines

        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        br._Browser__enqueue_recursive_children('http://example.com/api/admin', 0)

        pool.extend_total_items.assert_called_once_with(1)
        pool.add.assert_called_once_with(
            getattr(br, '_Browser__http_request'),
            'http://example.com/api/admin/login',
            1
        )

    def test_http_request_enqueues_recursive_children_for_eligible_response(self):
        """Browser.__http_request() should enqueue recursive children for eligible responses."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = 'response'
        pool = SimpleNamespace(items_size=2, total_items_size=10)
        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        response_handler = MagicMock()
        response_handler.handle.return_value = ('success', 'http://example.com/admin', '42B', '200')

        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'scan': 'directories',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }))
        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__response', response_handler)
        setattr(br, '_Browser__enqueue_recursive_children', MagicMock())

        br._Browser__http_request('http://example.com/admin', depth=0)

        getattr(br, '_Browser__enqueue_recursive_children').assert_called_once_with(
            'http://example.com/admin',
            0
        )

    def test_http_request_does_not_enqueue_recursive_children_for_non_eligible_response(self):
        """Browser.__http_request() should not enqueue recursive children for non-eligible responses."""

        br = self.make_browser()
        client = MagicMock()
        client.request.return_value = 'response'
        pool = SimpleNamespace(items_size=2, total_items_size=10)
        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        response_handler = MagicMock()
        response_handler.handle.return_value = ('ignored', 'http://example.com/missing', '0B', '404')

        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'scan': 'directories',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }))
        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__response', response_handler)
        setattr(br, '_Browser__enqueue_recursive_children', MagicMock())

        br._Browser__http_request('http://example.com/missing', depth=0)

        getattr(br, '_Browser__enqueue_recursive_children').assert_not_called()

    def test_build_recursive_url_and_enqueue_children_cover_skip_paths(self):
        """Browser recursive helpers should skip blank/duplicate children and handle nested parents."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'prefix': '/api/',
            'scan': 'directories',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200,403',
            'recursive_exclude': 'jpg,png',
        }))
        reader = MagicMock()
        setattr(br, '_Browser__reader', reader)
        pool = MagicMock()
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__queued_recursive', {'http://example.com/api/users'})

        self.assertIsNone(br._Browser__build_recursive_url('http://example.com/api', '   '))
        self.assertEqual(
            br._Browser__build_recursive_url('http://example.com/api', 'users'),
            'http://example.com/api/users'
        )
        self.assertEqual(
            br._Browser__build_recursive_url('http://example.com', 'users'),
            'http://example.com/users'
        )

        def fake_get_lines(params, loader):
            loader([
                'http://example.com/api/users',
                'http://example.com/api/roles',
                'http://example.com/api/',
            ])

        reader.get_lines.side_effect = fake_get_lines
        br._Browser__enqueue_recursive_children('http://example.com/api', 0)

        pool.extend_total_items.assert_called_once_with(1)
        pool.add.assert_called_once_with(
            getattr(br, '_Browser__http_request'),
            'http://example.com/api/roles',
            1
        )

    def test_enqueue_recursive_children_stops_at_depth_limit(self):
        """Browser recursive child enqueue should stop immediately at the configured depth limit."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'recursive': True,
            'recursive_depth': 1,
        }))
        reader = MagicMock()
        setattr(br, '_Browser__reader', reader)
        pool = MagicMock()
        setattr(br, '_Browser__pool', pool)

        br._Browser__enqueue_recursive_children('http://example.com/admin', 1)

        reader.get_lines.assert_not_called()
        pool.add.assert_not_called()

    def test_apply_regex_filters_handles_match_and_exclude_paths(self):
        """Browser regex filter helper should return False for unmet match or hit exclude patterns."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'match_regex': ['admin'],
            'exclude_regex': ['forbidden'],
        }))

        self.assertTrue(br._Browser__apply_regex_filters('admin panel'))
        self.assertFalse(br._Browser__apply_regex_filters('public panel'))
        self.assertFalse(br._Browser__apply_regex_filters('admin forbidden'))

    def test_get_response_length_prefers_content_length_and_falls_back_to_body(self):
        """Browser response size helper should prefer Content-Length and fall back to raw body bytes."""

        br = self.make_browser()

        response = SimpleNamespace(headers={'Content-Length': '12'}, data=b'abcdef')
        self.assertEqual(br._Browser__get_response_length(response), 12)

        response = SimpleNamespace(headers={'Content-Length': 'bad'}, data=b'abcdef')
        self.assertEqual(br._Browser__get_response_length(response), 6)

        response = SimpleNamespace(data=b'xyz')
        self.assertEqual(br._Browser__get_response_length(response), 3)

        response = SimpleNamespace(headers={})
        self.assertEqual(br._Browser__get_response_length(response), 0)

    def test_get_response_body_returns_decoded_text_or_empty_string(self):
        """Browser body helper should decode response bytes and gracefully handle missing data."""

        br = self.make_browser()
        response = SimpleNamespace(data='тест'.encode('utf-8'))
        self.assertEqual(br._Browser__get_response_body(response), 'тест')
        self.assertEqual(br._Browser__get_response_body(SimpleNamespace()), '')

    def test_is_response_allowed_respects_status_and_size_filters(self):
        """Browser response filters should honor status and size constraints before body checks."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'include_status': ['200-201'],
            'exclude_status': ['404'],
            'exclude_size': ['12'],
            'exclude_size_range': ['20-30'],
            'min_response_length': 5,
            'max_response_length': 15,
        }))

        allowed_resp = SimpleNamespace(headers={'Content-Length': '10'}, data=b'0123456789')
        self.assertTrue(br._Browser__is_response_allowed(allowed_resp, ('success', 'u', '10B', '200')))
        self.assertFalse(
            br._Browser__is_response_allowed(
                SimpleNamespace(headers={'Content-Length': '10'}, data=b'0123456789'),
                ('success', 'u', '10B', '404')
            )
        )
        self.assertFalse(
            br._Browser__is_response_allowed(
                SimpleNamespace(headers={'Content-Length': '12'}, data=b'012345678901'),
                ('success', 'u', '12B', '200')
            )
        )
        self.assertFalse(
            br._Browser__is_response_allowed(
                SimpleNamespace(headers={'Content-Length': '25'}, data=b'x' * 25),
                ('success', 'u', '25B', '200')
            )
        )
        self.assertFalse(
            br._Browser__is_response_allowed(
                SimpleNamespace(headers={'Content-Length': '4'}, data=b'1234'),
                ('success', 'u', '4B', '200')
            )
        )
        self.assertFalse(
            br._Browser__is_response_allowed(
                SimpleNamespace(headers={'Content-Length': '16'}, data=b'x' * 16),
                ('success', 'u', '16B', '200')
            )
        )

    def test_is_response_allowed_respects_text_and_regex_filters(self):
        """Browser response filters should honor body text and regex match/exclude rules."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'match_text': ['login'],
            'exclude_text': ['forbidden'],
            'match_regex': ['(?i)admin'],
            'exclude_regex': ['(?i)denied'],
        }))

        self.assertTrue(
            br._Browser__is_response_allowed(
                SimpleNamespace(data=b'login admin portal'),
                ('success', 'u', '18B', '200')
            )
        )
        self.assertFalse(
            br._Browser__is_response_allowed(
                SimpleNamespace(data=b'admin portal'),
                ('success', 'u', '12B', '200')
            )
        )
        self.assertFalse(
            br._Browser__is_response_allowed(
                SimpleNamespace(data=b'login admin forbidden area'),
                ('success', 'u', '26B', '200')
            )
        )
        self.assertFalse(
            br._Browser__is_response_allowed(
                SimpleNamespace(data=b'login portal'),
                ('success', 'u', '12B', '200')
            )
        )
        self.assertFalse(
            br._Browser__is_response_allowed(
                SimpleNamespace(data=b'login admin access denied'),
                ('success', 'u', '24B', '200')
            )
        )

    def test_init_warns_when_head_is_overridden_to_get(self):
        """Browser.__init__() should emit a warning for explicit HEAD to GET override."""

        with patch('src.lib.browser.browser.Config') as config_cls, \
                patch('src.lib.browser.browser.Debug', return_value=MagicMock()), \
                patch('src.lib.browser.browser.Reader') as reader_cls, \
                patch('src.lib.browser.browser.Filter.__init__', return_value=None), \
                patch('src.lib.browser.browser.ThreadPool', return_value=MagicMock()), \
                patch('src.lib.browser.browser.response', return_value=MagicMock()), \
                patch.object(Tpl, 'warning') as warning_mock:
            cfg = SimpleNamespace(
                scan='directories',
                DEFAULT_SCAN='directories',
                proxy_list=None,
                is_random_list=False,
                is_extension_filter=False,
                is_ignore_extension_filter=False,
                is_external_wordlist=False,
                wordlist='',
                is_standalone_proxy=False,
                is_external_proxy_list=False,
                prefix='',
                is_external_reports_dir=False,
                reports_dir='',
                extensions=[],
                ignore_extensions=[],
                threads=1,
                delay=0,
                _method='HEAD',
                method='GET',
                method_override_items=['indexof', 'collation'],
            )
            config_cls.return_value = cfg

            reader = MagicMock()
            reader.total_lines = 5
            reader_cls.return_value = reader

            browser({'host': 'test.local', 'port': 80})

        warning_mock.assert_called_once_with(
            key='method_override',
            sniffers='indexof, collation'
        )

    def test_extract_response_code_should_return_none_when_status_and_response_data_are_invalid(self):
        """Browser.__extract_response_code() should return None when all status sources are invalid."""

        response = SimpleNamespace(status='bad')

        actual = Browser._Browser__extract_response_code(
            response,
            ('success', 'http://example.com', '1B', '-')
        )

        self.assertIsNone(actual)

    def test_extract_response_code_should_use_response_data_when_response_status_is_invalid(self):
        """Browser.__extract_response_code() should fallback to handled response data code."""

        response = SimpleNamespace(status='bad')

        actual = Browser._Browser__extract_response_code(
            response,
            ('success', 'http://example.com', '1B', '404')
        )

        self.assertEqual(actual, 404)

    def test_get_header_value_should_return_direct_header_lookup(self):
        """Browser.__get_header_value() should return header value from direct lookup."""

        response = SimpleNamespace(headers={'Retry-After': '5'})

        actual = Browser._Browser__get_header_value(response, 'Retry-After')

        self.assertEqual(actual, '5')

    def test_get_header_value_should_return_lowercase_header_lookup(self):
        """Browser.__get_header_value() should return header value from lowercase lookup."""

        response = SimpleNamespace(headers={'retry-after': '7'})

        actual = Browser._Browser__get_header_value(response, 'Retry-After')

        self.assertEqual(actual, '7')

    def test_get_header_value_should_return_items_fallback_lookup(self):
        """Browser.__get_header_value() should return header value from items fallback."""

        class HeadersWithoutGet(object):
            def items(self):
                return [('Retry-After', '9')]

        response = SimpleNamespace(headers=HeadersWithoutGet())

        actual = Browser._Browser__get_header_value(response, 'retry-after')

        self.assertEqual(actual, '9')

    def test_get_header_value_should_return_none_when_headers_have_no_mapping_api(self):
        """Browser.__get_header_value() should return None for unsupported headers object."""

        response = SimpleNamespace(headers=object())

        actual = Browser._Browser__get_header_value(response, 'Retry-After')

        self.assertIsNone(actual)

    def test_get_header_value_should_return_none_without_headers_attribute(self):
        """Browser.__get_header_value() should return None when response has no headers."""

        response = SimpleNamespace()

        actual = Browser._Browser__get_header_value(response, 'Retry-After')

        self.assertIsNone(actual)

    def test_get_retry_after_delay_should_return_none_for_invalid_retry_after_value(self):
        """Browser.__get_retry_after_delay() should return None for non-numeric Retry-After."""

        br = self.make_browser()
        response = SimpleNamespace(headers={'Retry-After': 'soon'})

        actual = br._Browser__get_retry_after_delay(response)

        self.assertIsNone(actual)

    def test_get_retry_after_delay_should_return_none_for_negative_retry_after_value(self):
        """Browser.__get_retry_after_delay() should return None for negative Retry-After."""

        br = self.make_browser()
        response = SimpleNamespace(headers={'Retry-After': '-1'})

        actual = br._Browser__get_retry_after_delay(response)

        self.assertIsNone(actual)

    def test_get_retry_after_delay_should_return_numeric_retry_after_value(self):
        """Browser.__get_retry_after_delay() should return numeric Retry-After delay."""

        br = self.make_browser()
        response = SimpleNamespace(headers={'Retry-After': '3.5'})

        actual = br._Browser__get_retry_after_delay(response)

        self.assertEqual(actual, 3.5)

    def test_recover_waf_safe_backoff_should_reset_counter_when_delay_is_minimal(self):
        """Browser.__recover_waf_safe_backoff() should reset recovery counter when delay is already minimal."""

        br = self.make_browser()

        setattr(br, '_Browser__waf_safe_delay', br.WAF_SAFE_MIN_DELAY)
        setattr(br, '_Browser__waf_safe_recovery_count', 3)

        br._Browser__recover_waf_safe_backoff()

        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), br.WAF_SAFE_MIN_DELAY)
        self.assertEqual(getattr(br, '_Browser__waf_safe_recovery_count'), 0)

    def test_update_waf_safe_backoff_should_ignore_none_response_data(self):
        """Browser.__update_waf_safe_backoff() should ignore missing handled response data."""

        br = self.make_browser()
        setattr(br, '_Browser__config', SimpleNamespace(is_waf_safe_mode=True))
        setattr(br, '_Browser__waf_safe_active', True)
        setattr(br, '_Browser__waf_safe_delay', 4.0)

        br._Browser__update_waf_safe_backoff(
            SimpleNamespace(status=429, headers={'Retry-After': '1'}),
            None
        )

        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 4.0)

    def test_update_waf_safe_backoff_should_ignore_when_safe_mode_is_disabled(self):
        """Browser.__update_waf_safe_backoff() should ignore updates when WAF safe mode is disabled."""

        br = self.make_browser()
        setattr(br, '_Browser__config', SimpleNamespace(is_waf_safe_mode=False))
        setattr(br, '_Browser__waf_safe_active', True)
        setattr(br, '_Browser__waf_safe_delay', 4.0)

        br._Browser__update_waf_safe_backoff(
            SimpleNamespace(status=429, headers={'Retry-After': '1'}),
            ('blocked', 'http://example.com', '1B', '429')
        )

        self.assertEqual(getattr(br, '_Browser__waf_safe_delay'), 4.0)

    def test_http_request_should_not_enqueue_recursive_children_for_already_visited_url(self):
        """Browser.__http_request() should not enqueue recursive children for already visited URL."""

        br = self.make_browser()

        client = MagicMock()
        client.request.return_value = SimpleNamespace(
            status=200,
            headers={},
            data=b'ok',
        )

        response_handler = MagicMock()
        response_handler.handle.return_value = (
            'success',
            'http://example.com/panel',
            '2B',
            '200'
        )

        reader = MagicMock()
        reader.get_ignored_list.return_value = []

        pool = SimpleNamespace(items_size=1, total_items_size=10)

        config = self.browser_configuration({
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'recursive': True,
            'recursive_depth': 2,
            'recursive_status': '200',
            'recursive_exclude': 'jpg,png,css,js',
        })

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__response', response_handler)
        setattr(br, '_Browser__reader', reader)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__visited_recursive', {'http://example.com/panel'})

        with patch.object(br, '_Browser__enqueue_recursive_children') as enqueue_mock:
            br._Browser__http_request('http://example.com/panel', depth=0)

        enqueue_mock.assert_not_called()
        self.assertEqual(getattr(br, '_Browser__result')['total']['success'], 1)

    def test_finalize_processed_request_is_noop_when_session_is_disabled(self):
        """Browser session finalization should not mutate state when session mode is disabled."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'session_save': None,
        }))

        with patch.object(br, '_Browser__complete_request') as complete_mock, \
                patch.object(br, '_Browser__save_session') as save_mock:
            br._Browser__finalize_processed_request('http://example.com/admin', 0)

        complete_mock.assert_not_called()
        save_mock.assert_not_called()

    def test_register_pending_request_self_initializes_session_state_for_legacy_objects(self):
        """Browser session bookkeeping should self-initialize for legacy __new__()-style test objects."""

        br = browser.__new__(browser)

        actual = br._Browser__register_pending_request('http://example.com/admin', 0)

        self.assertTrue(actual)
        self.assertIn(
            '0::http://example.com/admin',
            getattr(br, '_Browser__pending_requests')
        )

    def test_http_request_legacy_objects_do_not_fail_on_session_finalize_paths(self):
        """Browser.__http_request() should remain safe for legacy objects without session attributes."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'session_save': None,
        }))

        client = MagicMock()
        client.request.return_value = SimpleNamespace(status=200, headers={}, data=b'ok')
        setattr(br, '_Browser__client', client)

        response_handler = MagicMock()
        response_handler.handle.return_value = ('success', 'http://example.com/admin', '2B', '200')
        setattr(br, '_Browser__response', response_handler)

        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        setattr(br, '_Browser__reader', reader)

        pool = SimpleNamespace(items_size=0, total_items_size=1)
        setattr(br, '_Browser__pool', pool)

        result = {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()}
        setattr(br, '_Browser__result', result)

        br._Browser__http_request('http://example.com/admin')

        self.assertEqual(result['items']['success'], ['http://example.com/admin'])

        client = MagicMock()
        client.request.return_value = SimpleNamespace(status=200, headers={}, data=b'ok')
        setattr(br, '_Browser__client', client)

        response_handler = MagicMock()
        response_handler.handle.return_value = ('success', 'http://example.com/admin', '2B', '200')
        setattr(br, '_Browser__response', response_handler)

        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        setattr(br, '_Browser__reader', reader)

        result = {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()}
        setattr(br, '_Browser__result', result)

        br._Browser__http_request('http://example.com/admin')

        self.assertEqual(result['items']['success'], ['http://example.com/admin'])

    def test_browser_result_should_return_defensive_copy(self):
        """Browser.result should expose a copy of internal scan result."""

        instance = Browser.__new__(Browser)
        instance._Browser__result = {
            'total': {'success': 1},
            'items': {'success': ['http://example.com/admin']},
            'report_items': {'success': [{'url': 'http://example.com/admin'}]},
        }

        actual = instance.result
        actual['total']['success'] = 99

        self.assertEqual(instance._Browser__result['total']['success'], 1)

    def test_http_request_should_put_calibration_matches_into_calibrated_bucket(self):
        """Browser.__http_request() should classify calibration matches as calibrated."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'auto_calibrate': True,
        }))

        client = MagicMock()
        client.request.return_value = SimpleNamespace(
            status=200,
            headers={'Content-Type': 'text/html'},
            data=b'<html><title>Not Found</title><body>Missing 123456</body></html>'
        )
        setattr(br, '_Browser__client', client)

        response_handler = MagicMock()
        response_handler.handle.return_value = (
            'success',
            'http://example.com/admin',
            '67B',
            '200'
        )
        setattr(br, '_Browser__response', response_handler)

        reader = MagicMock()
        reader.get_ignored_list.return_value = []
        setattr(br, '_Browser__reader', reader)

        pool = SimpleNamespace(items_size=0, total_items_size=1)
        setattr(br, '_Browser__pool', pool)

        calibration = MagicMock()
        calibration.match.return_value = {
            'calibration_score': 0.97,
            'calibration_reason': 'body-hash,skeleton-hash',
        }
        setattr(br, '_Browser__calibration', calibration)

        br._Browser__http_request('http://example.com/admin')

        self.assertEqual(response_handler.handle.call_count, 1)
        self.assertEqual(response_handler.handle.call_args.kwargs.get('emit_debug'), False)

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['total']['calibrated'], 1)
        self.assertEqual(result['items']['calibrated'], ['http://example.com/admin'])
        self.assertEqual(result['report_items']['calibrated'][0]['calibration_score'], 0.97)

    def test_calibrate_should_build_neutral_probe_urls(self):
        """Browser calibration probes should avoid branded scanner markers in request URLs."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'auto_calibrate': True,
            'calibration_samples': 2,
        }))

        with patch('src.lib.browser.browser.uuid.uuid4') as uuid4_mock:
            uuid4_mock.return_value.hex = 'abcdef1234567890'
            actual = br._Browser__build_calibration_urls()

        self.assertEqual(actual, [
            'http://example.com/abcdef123456-0',
            'http://example.com/assets/abcdef123456-1.map',
        ])
        self.assertNotIn('opendoor', ''.join(actual).lower())

    def test_calibrate_should_build_mixed_probe_url_shapes(self):
        """Browser calibration probes should cover root, asset and app-like paths."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'auto_calibrate': True,
            'calibration_samples': 8,
        }))

        with patch('src.lib.browser.browser.uuid.uuid4') as uuid4_mock:
            uuid4_mock.return_value.hex = 'abcdef1234567890'
            actual = br._Browser__build_calibration_urls()

        self.assertEqual(actual, [
            'http://example.com/abcdef123456-0',
            'http://example.com/assets/abcdef123456-1.map',
            'http://example.com/abcdef123456-2.php',
            'http://example.com/abcdef123456-3.html',
            'http://example.com/api/abcdef123456-4',
            'http://example.com/static/abcdef123456-5.js',
            'http://example.com/wp-content/uploads/abcdef123456-6.php',
            'http://example.com/admin/abcdef123456-7',
        ])

    def test_calibrate_should_build_baseline_from_probe_responses(self):
        """Browser.calibrate() should build baseline signatures from calibration probes."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'auto_calibrate': True,
            'calibration_samples': 2,
            'calibration_threshold': 0.92,
        }))

        client = MagicMock()
        client.request.return_value = SimpleNamespace(
            status=200,
            headers={'Content-Type': 'text/html'},
            data=b'<html><title>Not Found</title><body>Missing 123456</body></html>'
        )
        setattr(br, '_Browser__client', client)

        response_handler = MagicMock()
        response_handler.handle.return_value = (
            'success',
            'http://example.com/assets/abcdef123456-0.map',
            '67B',
            '200'
        )
        setattr(br, '_Browser__response', response_handler)

        with patch('src.lib.browser.browser.tpl.info'), \
                patch('src.lib.browser.browser.tpl.warning'):
            actual = br.calibrate()

        self.assertIsNotNone(actual)
        self.assertTrue(actual.is_enabled)
        self.assertEqual(len(actual.signatures), 2)
        response_handler.handle.assert_called()
        for call_args in response_handler.handle.call_args_list:
            self.assertEqual(call_args.kwargs.get('emit_debug'), False)

    def test_calibrate_should_noop_when_auto_calibration_is_disabled(self):
        """Browser.calibrate() should do nothing when auto-calibration is disabled."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'auto_calibrate': False,
        }))

        actual = br.calibrate()

        self.assertIsNone(actual)

    def test_calibrate_should_return_restored_baseline_when_available(self):
        """Browser.calibrate() should reuse restored calibration baseline."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'auto_calibrate': True,
        }))
        calibration = Calibration(signatures=[{'code': 404}], threshold=0.92)
        setattr(br, '_Browser__calibration', calibration)

        with patch('src.lib.browser.browser.tpl.info') as info_mock:
            actual = br.calibrate()

        self.assertIs(actual, calibration)
        info_mock.assert_called_once_with(msg='Auto-calibration baseline restored from session checkpoint')

    def test_calibrate_should_start_request_provider_when_client_is_missing(self):
        """Browser.calibrate() should initialize request provider when client is missing."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'auto_calibrate': True,
            'calibration_samples': 1,
            'calibration_threshold': 0.92,
        }))
        setattr(br, '_Browser__client', None)

        client = MagicMock()
        client.request.return_value = SimpleNamespace(
            status=404,
            headers={'Content-Type': 'text/html'},
            data=b'not found'
        )

        response_handler = MagicMock()
        response_handler.handle.return_value = (
            'success',
            'http://example.com/assets/abcdef123456-0.map',
            '9B',
            '404'
        )
        setattr(br, '_Browser__response', response_handler)

        def start_provider():
            setattr(br, '_Browser__client', client)

        with patch.object(br, '_Browser__start_request_provider', side_effect=start_provider) as start_mock, \
                patch('src.lib.browser.browser.tpl.info'), \
                patch('src.lib.browser.browser.tpl.warning'):
            actual = br.calibrate()

        self.assertIsNotNone(actual)
        start_mock.assert_called_once_with()
        client.request.assert_called_once()

    def test_calibrate_should_skip_none_and_blocked_probe_responses(self):
        """Browser.calibrate() should skip ignored and blocked calibration probes."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'auto_calibrate': True,
            'calibration_samples': 2,
            'calibration_threshold': 0.92,
        }))

        client = MagicMock()
        client.request.return_value = SimpleNamespace(
            status=403,
            headers={'Content-Type': 'text/html'},
            data=b'blocked'
        )
        setattr(br, '_Browser__client', client)

        response_handler = MagicMock()
        response_handler.handle.side_effect = [
            None,
            ('blocked', 'http://example.com/assets/abcdef123456-0.map', '7B', '403'),
        ]
        setattr(br, '_Browser__response', response_handler)

        with patch('src.lib.browser.browser.tpl.info'), \
                patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            actual = br.calibrate()

        self.assertIsNone(actual)
        self.assertEqual(response_handler.handle.call_count, 2)
        warning_mock.assert_any_call(msg='Auto-calibration disabled: no usable baseline signatures')

    def test_calibrate_should_continue_after_probe_request_error(self):
        """Browser.calibrate() should continue and disable baseline when probes fail."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'port': 80,
            'scheme': 'http://',
            'auto_calibrate': True,
            'calibration_samples': 1,
            'calibration_threshold': 0.92,
        }))

        client = MagicMock()
        client.request.side_effect = HttpRequestError('boom')
        setattr(br, '_Browser__client', client)
        setattr(br, '_Browser__response', MagicMock())

        with patch('src.lib.browser.browser.tpl.info'), \
                patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            actual = br.calibrate()

        self.assertIsNone(actual)
        warning_mock.assert_any_call(msg='Auto-calibration probe failed: boom')
        warning_mock.assert_any_call(msg='Auto-calibration disabled: no usable baseline signatures')

    def test_calibrate_should_skip_on_unexpected_runtime_error(self):
        """Browser.calibrate() should skip calibration on unexpected runtime errors."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'auto_calibrate': True,
        }))
        setattr(br, '_Browser__client', MagicMock())

        with patch.object(br, '_Browser__build_calibration_urls', side_effect=AttributeError('bad state')), \
                patch('src.lib.browser.browser.tpl.info'), \
                patch('src.lib.browser.browser.tpl.warning') as warning_mock:
            actual = br.calibrate()

        self.assertIsNone(actual)
        warning_mock.assert_called_with(msg='Auto-calibration skipped: bad state')

    def test_build_calibration_url_should_include_prefix_and_non_default_http_port(self):
        """Browser.__build_calibration_url() should include prefix and non-default HTTP port."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'port': 8080,
            'prefix': 'api/v1',
        }))

        actual = br._Browser__build_calibration_url('/probe')

        self.assertEqual(actual, 'http://example.com:8080/api/v1/probe')

    def test_build_calibration_url_should_include_non_default_https_port(self):
        """Browser.__build_calibration_url() should include non-default HTTPS port."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'scheme': 'https://',
            'ssl': True,
            'port': 9443,
        }))

        actual = br._Browser__build_calibration_url('probe')

        self.assertEqual(actual, 'https://example.com:9443/probe')

    def test_match_calibrated_response_should_return_none_when_disabled_or_missing_baseline(self):
        """Browser.__match_calibrated_response() should return None without enabled calibration baseline."""

        br = self.make_browser()
        response = SimpleNamespace(status=404, headers={}, data=b'not found')
        response_data = ('success', 'http://example.com/admin', '9B', '404')

        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'auto_calibrate': False,
        }))
        self.assertIsNone(br._Browser__match_calibrated_response(response, response_data))

        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'auto_calibrate': True,
        }))
        setattr(br, '_Browser__calibration', None)
        self.assertIsNone(br._Browser__match_calibrated_response(response, response_data))

    def test_session_snapshot_should_include_calibration_state(self):
        """Browser session snapshot should include calibration baseline state."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({
            'reports': 'std',
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'port': 80,
            'auto_calibrate': True,
            'calibration_samples': 5,
            'calibration_threshold': 0.92,
        }))
        setattr(br, '_Browser__pool', SimpleNamespace(items_size=0, total_items_size=1))
        setattr(br, '_Browser__calibration', Calibration(signatures=[{'code': 404}], threshold=0.92))

        snapshot = br._Browser__build_session_snapshot(reason='test')

        self.assertEqual(snapshot['calibration'], {
            'threshold': 0.92,
            'signatures': [{'code': 404}],
        })
        self.assertTrue(snapshot['params']['auto_calibrate'])
        self.assertEqual(snapshot['params']['calibration_samples'], 5)
        self.assertEqual(snapshot['params']['calibration_threshold'], 0.92)

    def test_restore_session_state_should_restore_calibration_state(self):
        """Browser.__restore_session_state() should restore calibration baseline from snapshot."""

        br = self.make_browser()
        setattr(br, '_Browser__pool', SimpleNamespace(total_items_size=1))

        br._Browser__restore_session_state({
            'result': {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()},
            'visitedRecursive': [],
            'queuedRecursive': [],
            'seen': [],
            'pending': [],
            'stats': {'processed': 0, 'total_items': 1},
            'wafSafeMode': {},
            'calibration': {
                'threshold': 0.93,
                'signatures': [{'code': 404}],
            },
        })

        calibration = getattr(br, '_Browser__calibration')
        self.assertIsNotNone(calibration)
        self.assertEqual(calibration.threshold, 0.93)
        self.assertEqual(calibration.signatures, [{'code': 404}])

if __name__ == '__main__':
    unittest.main()
