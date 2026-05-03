# -*- coding: utf-8 -*-

import os
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
                patch('src.lib.browser.browser.socket.get_ip_address', return_value='127.0.0.1') as mock_ip:
            self.assertIs(br.ping(), None)
            mock_ping.assert_called_once()
            mock_ip.assert_called_once_with('example.com')

    def test_ping_wraps_socket_errors(self):
        """Browser.ping() should wrap socket failures into BrowserError."""

        br = self.make_browser()
        setattr(br, '_Browser__config', self.browser_configuration({'reports': 'std', 'host': 'example.com', 'port': 80}))

        with patch('src.lib.browser.browser.socket.ping', side_effect=SocketError('offline')):
            with self.assertRaises(BrowserError):
                br.ping()

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

        setattr(br, '_Browser__config', config)
        setattr(br, '_Browser__debug', debug)
        setattr(br, '_Browser__pool', pool)
        setattr(br, '_Browser__reader', reader)

        with patch.object(br, '_Browser__start_request_provider', side_effect=HttpRequestError('boom')), \
                patch('src.lib.browser.browser.tpl.info'):
            with self.assertRaises(BrowserError):
                br.scan()

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
        setattr(br, '_Browser__queued_recursive', set(['http://example.com/api/users']))

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
            'recursive_depth': 0,
        }))
        reader = MagicMock()
        setattr(br, '_Browser__reader', reader)
        pool = MagicMock()
        setattr(br, '_Browser__pool', pool)

        br._Browser__enqueue_recursive_children('http://example.com/admin', 0)

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

    def test_catch_report_data_initializes_report_items_when_missing(self):
        """Browser.__catch_report_data() should restore report_items when old payloads do not have it."""

        br = browser.__new__(browser)
        setattr(br, '_Browser__result', {'total': helper.counter(), 'items': helper.list()})

        br._Browser__catch_report_data('success', 'http://example.com/admin', '5B', '200')

        result = getattr(br, '_Browser__result')
        self.assertEqual(result['items']['success'], ['http://example.com/admin'])
        self.assertEqual(
            result['report_items']['success'],
            [{'url': 'http://example.com/admin', 'size': '5B', 'code': '200'}]
        )

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
            'http://example.com/assets/abcdef123456-0.map',
            'http://example.com/assets/abcdef123456-1.map',
        ])
        self.assertNotIn('opendoor', ''.join(actual).lower())

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