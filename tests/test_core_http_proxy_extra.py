# -*- coding: utf-8 -*-

import io
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib3.exceptions import MaxRetryError, ProxySchemeUnknown, ReadTimeoutError
from urllib3.response import HTTPResponse

from src.core.http.exceptions import ProxyRequestError
from src.core.http.proxy import Proxy


class TestProxyExtra(unittest.TestCase):
    """TestProxyExtra class."""

    @staticmethod
    def make_cfg(**overrides):
        """Create a minimal config namespace for Proxy tests."""

        base = {
            'keep_alive': False,
            'is_standalone_proxy': True,
            'proxy': 'http://127.0.0.1:8080',
            'threads': 2,
            'timeout': 1,
            'retries': False,
            'accept_cookies': False,
            'method': 'HEAD',
            'DEFAULT_SCAN': 'directories',
            'scan': 'directories',
            'is_random_user_agent': False,
            'user_agent': 'UA',
            'scheme': 'http://',
            'host': 'example.com',
            'port': 80,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @staticmethod
    def make_debug(level=0):
        """Create a simple debug stub."""

        return SimpleNamespace(
            level=level,
            debug_proxy_pool=MagicMock(),
            debug_proxy_selected=MagicMock(),
            debug_request=MagicMock(),
            debug_response=MagicMock(),
        )

    def test_init_rejects_empty_proxy_list_for_non_standalone_mode(self):
        """Proxy should reject empty proxy lists when standalone proxy is disabled."""

        cfg = self.make_cfg(is_standalone_proxy=False)

        with self.assertRaises(ProxyRequestError):
            Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=[], agent_list=['UA'])

    def test_get_random_proxy_returns_stripped_value(self):
        """Proxy.__get_random_proxy() should return a stripped proxy server string."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        proxy = Proxy(
            cfg,
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=[' http://one:8080 ', ' https://two:8443 '],
            agent_list=['UA'],
        )

        with patch('src.core.http.proxy.random.randrange', return_value=1):
            actual = getattr(proxy, '_Proxy__get_random_proxy')()

        self.assertEqual(actual, 'https://two:8443')

    def test_get_proxy_type_detects_socks_https_and_http(self):
        """Proxy.__get_proxy_type() should classify supported proxy schemes."""

        proxy_type = getattr(Proxy, '_Proxy__get_proxy_type')

        self.assertEqual(proxy_type('socks5://127.0.0.1:9050'), 'socks')
        self.assertEqual(proxy_type('socks5h://127.0.0.1:9050'), 'socks')
        self.assertEqual(proxy_type('https://proxy.example.com'), 'https')
        self.assertEqual(proxy_type('http://proxy.example.com'), 'http')

    def test_proxy_pool_uses_proxy_manager_for_http_proxy(self):
        """Proxy.__proxy_pool() should use ProxyManager for non-socks proxies."""

        cfg = self.make_cfg(is_standalone_proxy=True, proxy='http://127.0.0.1:8080')
        pool = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch('src.core.http.proxy.ProxyManager', return_value=pool) as proxy_manager_mock:
            actual = getattr(proxy, '_Proxy__proxy_pool')()
            cached = getattr(proxy, '_Proxy__proxy_pool')()

        self.assertIs(actual, pool)
        self.assertIs(cached, pool)
        proxy_manager_mock.assert_called_once()


    def test_prepare_connection_pool_prewarms_rotating_proxy_once(self):
        """Proxy.prepare_connection_pool() should pre-create the rotating proxy pool."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        debug = self.make_debug()
        pool = MagicMock()
        proxy = Proxy(
            cfg,
            debug,
            tpl=MagicMock(),
            proxy_list=['socks5://127.0.0.1:9050'],
            agent_list=['UA'],
        )

        with patch('src.core.http.proxy.random.randrange', return_value=0), \
                patch('src.core.http.proxy.disable_warnings'), \
                patch('src.core.http.proxy.importlib.import_module', return_value=SimpleNamespace(SOCKSProxyManager=MagicMock(return_value=pool))):
            self.assertTrue(proxy.prepare_connection_pool())
            self.assertTrue(proxy.prepare_connection_pool())

        debug.debug_proxy_selected.assert_called_once_with('socks5://127.0.0.1:9050')

    def test_prepare_connection_pool_skips_standalone_proxy(self):
        """Proxy.prepare_connection_pool() should not pre-create standalone proxy pools."""

        cfg = self.make_cfg(is_standalone_proxy=True, proxy='http://127.0.0.1:8080')
        debug = self.make_debug()
        proxy = Proxy(cfg, debug, tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__proxy_pool') as pool_mock:
            self.assertTrue(proxy.prepare_connection_pool())

        pool_mock.assert_not_called()
        debug.debug_proxy_selected.assert_not_called()

    def test_proxy_pool_passes_basic_auth_headers_for_authenticated_http_proxy(self):
        """Proxy.__proxy_pool() should pass Proxy-Authorization headers for HTTP CONNECT proxies."""

        cfg = self.make_cfg(is_standalone_proxy=True, proxy='http://user:pass@127.0.0.1:8080')
        pool = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch('src.core.http.proxy.ProxyManager', return_value=pool) as proxy_manager_mock:
            actual = getattr(proxy, '_Proxy__proxy_pool')()

        self.assertIs(actual, pool)
        proxy_headers = proxy_manager_mock.call_args.kwargs['proxy_headers']
        self.assertEqual(proxy_headers['proxy-authorization'], 'Basic dXNlcjpwYXNz')

    def test_proxy_pool_decodes_url_encoded_basic_auth_credentials(self):
        """Proxy.__proxy_pool() should decode URL-encoded proxy credentials before Basic auth."""

        cfg = self.make_cfg(is_standalone_proxy=True, proxy='http://user:p%40ss%3Aword@127.0.0.1:8080')
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch('src.core.http.proxy.ProxyManager', return_value=MagicMock()) as proxy_manager_mock:
            getattr(proxy, '_Proxy__proxy_pool')()

        proxy_headers = proxy_manager_mock.call_args.kwargs['proxy_headers']
        self.assertEqual(proxy_headers['proxy-authorization'], 'Basic dXNlcjpwQHNzOndvcmQ=')

    def test_proxy_pool_uses_empty_proxy_headers_without_credentials(self):
        """Proxy.__proxy_pool() should keep proxy headers empty when no credentials are present."""

        cfg = self.make_cfg(is_standalone_proxy=True, proxy='http://127.0.0.1:8080')
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch('src.core.http.proxy.ProxyManager', return_value=MagicMock()) as proxy_manager_mock:
            getattr(proxy, '_Proxy__proxy_pool')()

        self.assertEqual(proxy_manager_mock.call_args.kwargs['proxy_headers'], {})

    def test_mask_proxy_server_hides_password_only(self):
        """Proxy.__mask_proxy_server() should hide passwords in terminal diagnostics."""

        mask = getattr(Proxy, '_Proxy__mask_proxy_server')

        self.assertEqual(
            mask('http://user:pass@127.0.0.1:8080'),
            'http://user:*****@127.0.0.1:8080',
        )
        self.assertEqual(mask('http://127.0.0.1:8080'), 'http://127.0.0.1:8080')
        self.assertEqual(mask(None), '-')

    def test_proxy_pool_uses_socks_manager_and_disables_warnings(self):
        """Proxy.__proxy_pool() should use the SOCKS manager and disable warnings for socks proxies."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        pool = MagicMock()
        socks_manager = MagicMock(return_value=pool)
        package_module = SimpleNamespace(SOCKSProxyManager=socks_manager)

        proxy = Proxy(
            cfg,
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=['socks5://127.0.0.1:9050'],
            agent_list=['UA'],
        )

        with patch('src.core.http.proxy.random.randrange', return_value=0), \
                patch('src.core.http.proxy.disable_warnings') as disable_mock, \
                patch('src.core.http.proxy.importlib.import_module', return_value=package_module):
            actual = getattr(proxy, '_Proxy__proxy_pool')()
            cached = getattr(proxy, '_Proxy__proxy_pool')()

        self.assertIs(actual, pool)
        self.assertIs(cached, pool)
        disable_mock.assert_called_once()
        socks_manager.assert_called_once()

    def test_proxy_pool_wraps_proxy_scheme_errors(self):
        """Proxy.__proxy_pool() should wrap proxy scheme errors as ProxyRequestError."""

        cfg = self.make_cfg(is_standalone_proxy=True, proxy='http://127.0.0.1:8080')
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch('src.core.http.proxy.ProxyManager', side_effect=ProxySchemeUnknown('bad-scheme')):
            with self.assertRaises(ProxyRequestError):
                getattr(proxy, '_Proxy__proxy_pool')()

    def test_pool_request_uses_proxy_pool_and_routes_cookies(self):
        """Proxy.__pool_request() should delegate to the selected pool and route cookies."""

        cfg = self.make_cfg(is_standalone_proxy=True)
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        response = HTTPResponse(status=200, body=b'ok', headers={})
        pool = MagicMock()
        pool.request.return_value = response

        with patch.object(proxy, '_Proxy__proxy_pool', return_value=pool), \
                patch.object(proxy, 'cookies_middleware') as cookies_mock:
            actual = getattr(proxy, '_Proxy__pool_request')('http://example.com/path')

        self.assertEqual(actual.status, 200)
        pool.request.assert_called_once()
        cookies_mock.assert_called_once_with(is_accept=False, response=response)

    def test_request_sets_headers_and_uses_debug_path(self):
        """Proxy.request() should populate headers and call debug_request when debug level is high."""

        cfg = self.make_cfg(keep_alive=True)
        debug = self.make_debug(level=99)
        proxy = Proxy(cfg, debug, tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        response = HTTPResponse(status=200, body=b'ok', headers={})

        with patch.object(proxy, '_Proxy__pool_request', return_value=response) as pool_request_mock:
            actual = proxy.request('http://example.com/path')

        self.assertEqual(actual.status, 200)
        pool_request_mock.assert_called_once()
        self.assertEqual(pool_request_mock.call_args.args[0], 'http://example.com/path')
        self.assertIn('headers', pool_request_mock.call_args.kwargs)
        debug.debug_request.assert_called_once()

        headers = debug.debug_request.call_args.args[0]
        self.assertEqual(headers['User-Agent'], 'UA')
        self.assertEqual(headers['Connection'], 'keep-alive')

    def test_request_retries_once_on_max_retry_for_default_scan(self):
        """Proxy.request() should warn and retry once on MaxRetryError for default scan mode."""

        cfg = self.make_cfg(scan='directories')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])
        proxy._Proxy__server = 'http://127.0.0.1:8080'

        response = HTTPResponse(status=200, body=b'ok', headers={})

        with patch.object(proxy, '_Proxy__pool_request', side_effect=[MaxRetryError(None, '/', None), response]):
            actual = proxy.request('http://example.com/path')

        self.assertEqual(actual.status, 200)
        tpl.warning.assert_called_once()

    def test_request_raises_proxy_error_after_standalone_proxy_retry_fails(self):
        """Proxy.request() should fail fast when a standalone proxy retry also fails."""

        cfg = self.make_cfg(scan='directories', is_standalone_proxy=True)
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])
        proxy._Proxy__server = 'socks5://127.0.0.1:9050'

        with patch.object(
            proxy,
            '_Proxy__pool_request',
            side_effect=[
                MaxRetryError(None, '/', None),
                MaxRetryError(None, '/', OSError('Connection refused')),
            ],
        ) as pool_request_mock:
            with self.assertRaises(ProxyRequestError) as context:
                proxy.request('https://localhost/')

        self.assertEqual(pool_request_mock.call_count, 2)
        self.assertEqual(tpl.warning.call_count, 1)
        self.assertEqual(tpl.warning.call_args_list[0].kwargs['key'], 'proxy_max_retry_error')
        tpl.error.assert_called_once()
        self.assertIn('unavailable after retry', tpl.error.call_args.kwargs['msg'])
        self.assertIn('connection refused', tpl.error.call_args.kwargs['msg'])
        self.assertIn('connection refused', str(context.exception))

    def test_request_warns_after_proxy_list_retry_fails(self):
        """Proxy.request() should not abort the scan when a proxy-list retry fails."""

        cfg = self.make_cfg(scan='directories', is_standalone_proxy=False)
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])
        proxy._Proxy__server = 'socks5://127.0.0.1:9050'

        with patch.object(
            proxy,
            '_Proxy__pool_request',
            side_effect=[
                MaxRetryError(None, '/', None),
                MaxRetryError(None, '/', OSError('Connection refused')),
            ],
        ) as pool_request_mock:
            actual = proxy.request('https://localhost/')

        self.assertIsNone(actual)
        self.assertEqual(pool_request_mock.call_count, 2)
        self.assertEqual(tpl.warning.call_count, 2)
        tpl.error.assert_not_called()
        self.assertIn('unavailable after retry', tpl.warning.call_args_list[1].kwargs['msg'])
        self.assertIn('connection refused', tpl.warning.call_args_list[1].kwargs['msg'])

    def test_request_breaks_active_progress_line_before_proxy_warning(self):
        """Proxy.request() should move proxy warnings away from rotating progress output."""

        cfg = self.make_cfg(scan='directories')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])
        stdout = io.StringIO()
        response = HTTPResponse(status=200, body=b'ok', headers={})

        with patch('sys.stdout', stdout):
            with patch.object(proxy, '_Proxy__pool_request', side_effect=[MaxRetryError(None, '/', None), response]):
                actual = proxy.request('http://example.com/path')

        self.assertEqual(actual.status, 200)
        self.assertEqual(stdout.getvalue(), '\n')
        tpl.warning.assert_called_once()


    def test_request_warns_after_proxy_list_retry_times_out(self):
        """Proxy.request() should format retry read timeouts without raw urllib3 details."""

        cfg = self.make_cfg(scan='directories', is_standalone_proxy=False)
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])
        proxy._Proxy__server = 'socks5://127.0.0.1:9050'

        with patch.object(
            proxy,
            '_Proxy__pool_request',
            side_effect=[
                MaxRetryError(None, '/', None),
                ReadTimeoutError(None, '/', 'Read timed out'),
            ],
        ) as pool_request_mock:
            actual = proxy.request('https://localhost/')

        self.assertIsNone(actual)
        self.assertEqual(pool_request_mock.call_count, 2)
        self.assertEqual(tpl.warning.call_count, 2)
        self.assertIn('connection timed out', tpl.warning.call_args_list[1].kwargs['msg'])

    def test_finish_active_terminal_line_ignores_stdout_errors(self):
        """Proxy.__finish_active_terminal_line() should never fail on broken stdout."""

        class BrokenStdout(object):
            """stdout stub that raises while writing."""

            def write(self, _value):
                """Raise an OS error to emulate a closed output stream."""

                raise OSError('closed')

            def flush(self):
                """Flush no-op for interface completeness."""

                return None

        with patch('sys.stdout', BrokenStdout()):
            self.assertIsNone(getattr(Proxy, '_Proxy__finish_active_terminal_line')())

    def test_format_proxy_error_normalizes_common_network_errors(self):
        """Proxy.__format_proxy_error() should emit compact network diagnostics."""

        formatter = getattr(Proxy, '_Proxy__format_proxy_error')

        self.assertEqual(formatter(Exception('Operation timed out')), 'connection timed out')
        self.assertEqual(formatter(Exception('Connection reset by peer')), 'connection reset')
        self.assertEqual(formatter(Exception('Name or service not known')), 'name resolution failed')
        self.assertEqual(formatter(Exception('plain failure')), 'plain failure')

    def test_format_proxy_error_truncates_long_unknown_errors(self):
        """Proxy.__format_proxy_error() should keep unexpected errors readable."""

        formatter = getattr(Proxy, '_Proxy__format_proxy_error')
        message = formatter(Exception('x' * 300))

        self.assertEqual(len(message), 180)
        self.assertTrue(message.endswith('...'))

    def test_request_retries_once_on_max_retry_for_ignore_extensionlist_scan(self):
        """Proxy.request() should keep directory diagnostics for ignore-extension scans."""

        cfg = self.make_cfg(scan='ignore_extensionlist')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])
        proxy._Proxy__server = 'http://127.0.0.1:8080'
        response = HTTPResponse(status=200, body=b'ok', headers={})

        with patch.object(proxy, '_Proxy__pool_request', side_effect=[MaxRetryError(None, '/', None), response]):
            actual = proxy.request('http://example.com/path')

        self.assertEqual(actual.status, 200)
        tpl.warning.assert_called_once()

    def test_request_suppresses_retry_warning_for_non_default_scan(self):
        """Proxy.request() should not warn or retry on MaxRetryError for non-default scan mode."""

        cfg = self.make_cfg(scan='subdomains')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__pool_request', side_effect=MaxRetryError(None, '/', None)):
            self.assertIsNone(proxy.request('http://api.example.com'))

        tpl.warning.assert_not_called()

    def test_request_warns_on_read_timeout_for_default_scan(self):
        """Proxy.request() should warn on ReadTimeoutError for default scan mode."""

        cfg = self.make_cfg(scan='directories')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__pool_request', side_effect=ReadTimeoutError(None, '/', 'x')):
            self.assertIsNone(proxy.request('http://example.com/path'))

        tpl.warning.assert_called_once()

    def test_request_warns_on_read_timeout_for_ignore_extensionlist_scan(self):
        """Proxy.request() should warn on timeout for ignore-extension directory scans."""

        cfg = self.make_cfg(scan='ignore_extensionlist')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__pool_request', side_effect=ReadTimeoutError(None, '/', 'x')):
            self.assertIsNone(proxy.request('http://example.com/path'))

        tpl.warning.assert_called_once()

    def test_request_suppresses_read_timeout_warning_for_non_default_scan(self):
        """Proxy.request() should not warn on ReadTimeoutError for non-default scan mode."""

        cfg = self.make_cfg(scan='subdomains')
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://unused'], agent_list=['UA'])

        with patch.object(proxy, '_Proxy__pool_request', side_effect=ReadTimeoutError(None, '/', 'x')):
            self.assertIsNone(proxy.request('http://api.example.com'))

        tpl.warning.assert_not_called()

    def test_get_random_proxy_preserves_socks5h_scheme(self):
        """Proxy.__get_random_proxy() should keep socks5h proxy-list entries unchanged."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        proxy = Proxy(
            cfg,
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=[' socks5h://127.0.0.1:9050 '],
            agent_list=['UA'],
        )

        with patch('src.core.http.proxy.random.randrange', return_value=0):
            actual = getattr(proxy, '_Proxy__get_random_proxy')()

        self.assertEqual(actual, 'socks5h://127.0.0.1:9050')

    def test_get_random_proxy_normalizes_socks_alias(self):
        """Proxy.__get_random_proxy() should normalize socks:// aliases to socks5://."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        proxy = Proxy(
            cfg,
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=[' socks://127.0.0.1:9050 '],
            agent_list=['UA'],
        )

        with patch('src.core.http.proxy.random.randrange', return_value=0):
            actual = getattr(proxy, '_Proxy__get_random_proxy')()

        self.assertEqual(actual, 'socks5://127.0.0.1:9050')

    def test_proxy_pool_wraps_missing_pysocks_for_socks_proxy(self):
        """Proxy.__proxy_pool() should raise a helpful error when PySocks is missing."""

        cfg = self.make_cfg(is_standalone_proxy=True, proxy='socks://127.0.0.1:9050')
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch('src.core.http.proxy.importlib.import_module', side_effect=ImportError("No module named 'socks'")):
            with self.assertRaises(ProxyRequestError) as context:
                getattr(proxy, '_Proxy__proxy_pool')()

        self.assertIn('PySocks', str(context.exception))

    def test_debug_cookie_middleware_emits_accept_and_accepted_diagnostics(self):
        """Proxy.__debug_cookie_middleware() should report accepted cookies when enabled."""

        cfg = self.make_cfg(accept_cookies=True)
        debug = self.make_debug(level=3)
        debug.debug_cookie_accept_enabled = MagicMock()
        debug.debug_cookie_accepted = MagicMock()
        proxy = Proxy(cfg, debug, tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])
        response = HTTPResponse(status=200, body=b'ok', headers={'Set-Cookie': 'sid=abc; Path=/'})

        getattr(proxy, '_Proxy__debug_cookie_middleware')(response)

        debug.debug_cookie_accept_enabled.assert_called_once_with()
        debug.debug_cookie_accepted.assert_called_once_with('sid=abc')


    def test_proxy_pool_passes_basic_auth_headers_for_authenticated_rotating_proxy(self):
        """Proxy.__proxy_pool() should pass Proxy-Authorization for authenticated proxy-list entries."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        debug = self.make_debug(level=1)
        pool = MagicMock()
        proxy = Proxy(
            cfg,
            debug,
            tpl=MagicMock(),
            proxy_list=['http://user:pass@127.0.0.1:8080'],
            agent_list=['UA'],
        )

        with patch('src.core.http.proxy.ProxyManager', return_value=pool) as proxy_manager_mock:
            actual = getattr(proxy, '_Proxy__proxy_pool')()

        self.assertIs(actual, pool)
        proxy_headers = proxy_manager_mock.call_args.kwargs['proxy_headers']
        self.assertEqual(proxy_headers['proxy-authorization'], 'Basic dXNlcjpwYXNz')
        debug.debug_proxy_selected.assert_called_once_with('http://user:pass@127.0.0.1:8080')

    def test_proxy_pool_logs_rotating_proxy_selection_only_for_new_pool(self):
        """Proxy.__proxy_pool() should not spam selected-proxy debug for cached rotating pools."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        debug = self.make_debug(level=1)
        pool = MagicMock()
        proxy = Proxy(
            cfg,
            debug,
            tpl=MagicMock(),
            proxy_list=['http://127.0.0.1:8080'],
            agent_list=['UA'],
        )

        with patch('src.core.http.proxy.ProxyManager', return_value=pool) as proxy_manager_mock:
            first = getattr(proxy, '_Proxy__proxy_pool')()
            second = getattr(proxy, '_Proxy__proxy_pool')()
            third = getattr(proxy, '_Proxy__proxy_pool')()

        self.assertIs(first, pool)
        self.assertIs(second, pool)
        self.assertIs(third, pool)
        proxy_manager_mock.assert_called_once()
        debug.debug_proxy_selected.assert_called_once_with('http://127.0.0.1:8080')

    def test_dead_proxy_cache_skips_failed_rotating_proxy(self):
        """Proxy should skip rotating proxies marked dead during the current scan runtime."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        proxy = Proxy(
            cfg,
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=['http://dead:8080', 'http://alive:8080'],
            agent_list=['UA'],
        )

        getattr(proxy, '_Proxy__mark_proxy_dead')('http://dead:8080')

        with patch('src.core.http.proxy.random.randrange', return_value=0):
            actual = getattr(proxy, '_Proxy__get_random_proxy')()

        self.assertEqual(actual, 'http://alive:8080')

    def test_dead_proxy_cache_raises_when_all_rotating_proxies_are_dead(self):
        """Proxy should fail clearly when every rotating proxy is unavailable."""

        cfg = self.make_cfg(is_standalone_proxy=False)
        proxy = Proxy(
            cfg,
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=['http://dead:8080'],
            agent_list=['UA'],
        )

        getattr(proxy, '_Proxy__mark_proxy_dead')('http://dead:8080')

        with self.assertRaises(ProxyRequestError) as context:
            getattr(proxy, '_Proxy__get_random_proxy')()

        self.assertIn('All rotating proxies are unavailable', str(context.exception))

    def test_request_marks_rotating_proxy_dead_after_retry_failure(self):
        """Proxy.request() should add a failed rotating proxy to the runtime dead cache."""

        cfg = self.make_cfg(scan='directories', is_standalone_proxy=False)
        tpl = MagicMock()
        proxy = Proxy(cfg, self.make_debug(), tpl=tpl, proxy_list=['http://dead:8080'], agent_list=['UA'])
        proxy._Proxy__server = 'http://dead:8080'
        proxy._Proxy__proxy_pools['http://dead:8080'] = MagicMock()

        with patch.object(
            proxy,
            '_Proxy__pool_request',
            side_effect=[
                MaxRetryError(None, '/', None),
                MaxRetryError(None, '/', OSError('Connection refused')),
            ],
        ):
            self.assertIsNone(proxy.request('https://localhost/'))

        self.assertIn('http://dead:8080', proxy._Proxy__dead_proxies)
        self.assertNotIn('http://dead:8080', proxy._Proxy__proxy_pools)

    def test_mask_proxy_server_covers_invalid_ipv6_and_username_only_urls(self):
        """Proxy.__mask_proxy_server() should cover defensive URL parsing branches."""

        mask = getattr(Proxy, '_Proxy__mask_proxy_server')

        self.assertEqual(mask('http://[::1'), 'http://[::1')
        self.assertEqual(
            mask('http://user:pass@[2001:db8::1]/proxy'),
            'http://user:*****@[2001:db8::1]/proxy',
        )
        self.assertEqual(
            mask('http://:pass@proxy.example.com'),
            'http://*****@proxy.example.com',
        )

    def test_mark_proxy_dead_noops_for_standalone_or_missing_server(self):
        """Dead-proxy tracking should ignore standalone proxies and empty values."""

        standalone = Proxy(
            self.make_cfg(is_standalone_proxy=True),
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=['http://unused'],
            agent_list=['UA'],
        )
        rotating = Proxy(
            self.make_cfg(is_standalone_proxy=False),
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=['http://one:8080'],
            agent_list=['UA'],
        )

        getattr(standalone, '_Proxy__mark_proxy_dead')('http://one:8080')
        getattr(rotating, '_Proxy__mark_proxy_dead')(None)

        self.assertEqual(getattr(standalone, '_Proxy__dead_proxies'), set())
        self.assertEqual(getattr(rotating, '_Proxy__dead_proxies'), set())

    def test_get_available_proxies_raises_when_all_rotating_proxies_are_dead(self):
        """Rotating proxy mode should fail clearly when every proxy is quarantined."""

        proxy = Proxy(
            self.make_cfg(is_standalone_proxy=False),
            self.make_debug(),
            tpl=MagicMock(),
            proxy_list=['http://one:8080'],
            agent_list=['UA'],
        )
        getattr(proxy, '_Proxy__mark_proxy_dead')('http://one:8080')

        with self.assertRaisesRegex(ProxyRequestError, 'All rotating proxies are unavailable'):
            getattr(proxy, '_Proxy__get_available_proxies')()


if __name__ == '__main__':
    unittest.main()
