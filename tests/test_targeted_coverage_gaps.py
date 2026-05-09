# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib3.exceptions import ProxySchemeUnknown

from src import Controller, SrcError
from src.core.filesystem.exceptions import FileSystemError
from src.core.decorators.timer import execution_time
from src.core.http.exceptions import ProxyRequestError
from src.core.http.proxy import Proxy
from src.core.network.exceptions import NetworkTransportError
from src.lib import BrowserError
from src.lib.package import Package, PackageError


class TestPackageTargetedCoverage(unittest.TestCase):
    """Targeted coverage for Package private counter and version parsing branches."""

    def setUp(self):
        """Reset cached remote version state."""

        Package.remote_version = None

    def test_should_wrap_each_counter_filesystem_error(self):
        """Package counters should wrap FileSystemError for every data source."""

        sources = {
            'directories': 'dir.dat',
            'subdomains': 'sub.dat',
            'useragents': 'ua.dat',
            'proxies': 'proxy.dat',
        }

        counter_methods = [
            Package._Package__directories_count,
            Package._Package__subdomains_count,
            Package._Package__browsers_count,
            Package._Package__proxies_count,
        ]

        for method in counter_methods:
            with self.subTest(method=method.__name__):
                with patch.dict('src.lib.package.package.CoreConfig', {'data': sources}, clear=False), \
                        patch('src.lib.package.package.filesystem.count_lines', side_effect=FileSystemError('boom')):
                    with self.assertRaises(PackageError):
                        method()

    def test_should_parse_trimmed_multi_part_and_major_only_versions(self):
        """Package version boundary parser should use only major/minor numeric parts."""

        self.assertEqual(Package._Package__parse_version_boundary(' 3.14.9 '), (3, 14))
        self.assertEqual(Package._Package__parse_version_boundary('4'), (4, 0))

    def test_should_raise_value_error_for_invalid_version_boundary(self):
        """Package parser should keep invalid configured boundaries explicit."""

        with self.assertRaises(ValueError):
            Package._Package__parse_version_boundary('not-a-version')

    def test_should_render_banner_with_info_lines(self):
        """Package banner renderer should include info lines and terminator."""

        banner = Package._Package__render_banner(['Directories: 1', 'License: GPL'])

        self.assertIsInstance(banner, str)
        self.assertIn('Directories: 1', banner)
        self.assertIn('License: GPL', banner)
        self.assertIn('======================================================================', banner)
        self.assertGreater(len(banner.splitlines()), 3)

    def test_should_return_true_when_interpreter_is_inside_supported_range(self):
        """Package.check_interpreter() should accept configured supported Python range."""

        version_info = SimpleNamespace(major=3, minor=14)

        with patch.dict(
            'src.lib.package.package.CoreConfig',
            {'info': {'required_versions': {'minor': '3.12', 'major': '3.14'}}},
            clear=False,
        ), patch('src.lib.package.package.py_sys.version_info', version_info):
            self.assertTrue(Package.check_interpreter())

    def test_should_return_details_when_interpreter_is_outside_supported_range(self):
        """Package.check_interpreter() should return mismatch details for unsupported Python versions."""

        version_info = SimpleNamespace(major=3, minor=15)

        with patch.dict(
            'src.lib.package.package.CoreConfig',
            {'info': {'required_versions': {'minor': '3.12', 'major': '3.14'}}},
            clear=False,
        ), patch('src.lib.package.package.py_sys.version_info', version_info):
            result = Package.check_interpreter()

        self.assertEqual(result, {
            'status': False,
            'actual': '3.15',
            'expected': '3.12 -> 3.14',
        })

    def test_should_return_cached_remote_version_without_network_call(self):
        """Package.__remote_version() should reuse cached remote version."""

        Package.remote_version = '9.9.9'

        with patch('src.lib.package.package.urlopen') as urlopen_mock:
            self.assertEqual(Package._Package__remote_version(), '9.9.9')

        urlopen_mock.assert_not_called()

    def test_should_return_unavailable_when_remote_version_body_is_empty(self):
        """Package.__remote_version() should normalize an empty remote response."""

        class Response(object):
            """Minimal context-manager response."""

            def __enter__(self):
                """Return response object."""

                return self

            def __exit__(self, exc_type, exc, traceback):
                """Do not suppress exceptions."""

                return False

            def read(self):
                """Return an empty response body."""

                return b''

        Package.remote_version = None

        with patch.dict(
            'src.lib.package.package.CoreConfig',
            {'info': {'remote_version': 'https://example.com/VERSION'}},
            clear=False,
        ), patch('src.lib.package.package.urlopen', return_value=Response()):
            self.assertEqual(Package._Package__remote_version(), 'unavailable')

    def test_should_color_current_version_when_remote_is_unavailable(self):
        """Package.__current_version() should keep local version green when remote is unavailable."""

        with patch.object(Package, 'local_version', return_value='5.15.1'), \
                patch.object(Package, '_Package__remote_version', return_value='unavailable'), \
                patch('src.lib.package.package.tpl.line', side_effect=lambda value, color=None: '{0}:{1}'.format(color, value)) as line_mock:
            rendered = Package._Package__current_version()

        self.assertIn('green:5.15.1', rendered)
        line_mock.assert_any_call('5.15.1', color='green')

    def test_should_color_current_version_red_when_update_exists(self):
        """Package.__current_version() should mark outdated local versions red."""

        with patch.object(Package, 'local_version', return_value='5.15.1'), \
                patch.object(Package, '_Package__remote_version', return_value='5.15.2'), \
                patch('src.lib.package.package.helper.is_less', return_value=True) as is_less_mock, \
                patch('src.lib.package.package.tpl.line', side_effect=lambda value, color=None: '{0}:{1}'.format(color, value)) as line_mock:
            rendered = Package._Package__current_version()

        self.assertIn('red:5.15.1', rendered)
        is_less_mock.assert_called_once_with('5.15.1', '5.15.2')
        line_mock.assert_any_call('5.15.1', color='red')

    def test_should_color_current_version_green_when_local_is_current(self):
        """Package.__current_version() should keep current local versions green."""

        with patch.object(Package, 'local_version', return_value='5.15.2'), \
                patch.object(Package, '_Package__remote_version', return_value='5.15.2'), \
                patch('src.lib.package.package.helper.is_less', return_value=False) as is_less_mock, \
                patch('src.lib.package.package.tpl.line', side_effect=lambda value, color=None: '{0}:{1}'.format(color, value)) as line_mock:
            rendered = Package._Package__current_version()

        self.assertIn('green:5.15.2', rendered)
        is_less_mock.assert_called_once_with('5.15.2', '5.15.2')
        line_mock.assert_any_call('5.15.2', color='green')


class TestProxyTargetedCoverage(unittest.TestCase):
    """Targeted coverage for proxy manager edge branches."""

    @staticmethod
    def make_cfg(**overrides):
        """Create a minimal proxy config namespace."""

        data = {
            'keep_alive': False,
            'is_standalone_proxy': True,
            'proxy': 'http://127.0.0.1:8080',
            'threads': 1,
            'timeout': 30,
            'method': 'GET',
            'retries': 0,
            'accept_cookies': False,
            'DEFAULT_SCAN': 'directories',
            'scan': 'directories',
            'headers': [],
            'cookies': [],
            'request_body': None,
        }
        data.update(overrides)
        return SimpleNamespace(**data)

    @staticmethod
    def make_debug(level=0):
        """Create a minimal proxy debug object."""

        return SimpleNamespace(
            level=level,
            debug_proxy_pool=MagicMock(),
            debug_request=MagicMock(),
        )

    def test_should_use_existing_socks_manager_without_importing_again(self):
        """Proxy.__proxy_pool() should reuse a prepared SOCKSProxyManager class."""

        cfg = self.make_cfg(proxy='socks5://127.0.0.1:9050')
        pool = MagicMock()
        socks_manager = MagicMock(return_value=pool)
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])
        proxy._Proxy__pm = socks_manager

        with patch('src.core.http.proxy.importlib.import_module') as import_mock:
            actual = getattr(proxy, '_Proxy__proxy_pool')()

        self.assertIs(actual, pool)
        import_mock.assert_not_called()
        socks_manager.assert_called_once()

    def test_should_wrap_generic_import_error_for_non_socks_proxy_pool(self):
        """Proxy.__proxy_pool() should wrap generic ImportError from non-SOCKS pool creation."""

        cfg = self.make_cfg(proxy='http://127.0.0.1:8080')
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch('src.core.http.proxy.ProxyManager', side_effect=ImportError('generic import error')):
            with self.assertRaises(ProxyRequestError) as context:
                getattr(proxy, '_Proxy__proxy_pool')()

        self.assertIn('generic import error', str(context.exception))

    def test_should_wrap_proxy_scheme_unknown_for_socks_manager(self):
        """Proxy.__proxy_pool() should wrap SOCKS manager scheme failures."""

        cfg = self.make_cfg(proxy='socks5://127.0.0.1:9050')
        package_module = SimpleNamespace(SOCKSProxyManager=MagicMock(side_effect=ProxySchemeUnknown('bad')))
        proxy = Proxy(cfg, self.make_debug(), tpl=MagicMock(), proxy_list=['http://unused'], agent_list=['UA'])

        with patch('src.core.http.proxy.importlib.import_module', return_value=package_module):
            with self.assertRaises(ProxyRequestError):
                getattr(proxy, '_Proxy__proxy_pool')()



class TestTimerTargetedCoverage(unittest.TestCase):
    """Targeted coverage for execution_time decorator branches."""

    def test_execution_time_without_positional_args_does_not_log_when_debug_is_disabled(self):
        """execution_time() should handle wrapped functions without positional arguments."""

        log = MagicMock()

        @execution_time(log=log)
        def wrapped():
            return 'ok'

        with patch('src.core.decorators.timer.time.time', side_effect=[10.0, 12.0]):
            self.assertEqual(wrapped(), 'ok')

        log.debug.assert_not_called()


class TestControllerTargetedCoverage(unittest.TestCase):
    """Targeted coverage for Controller branch gaps."""

    def test_should_preserve_fail_on_bucket_cli_override_for_wizard(self):
        """Controller.scan_action() should carry fail-on overrides into wizard params."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        wizard_params = {'host': 'example.com', 'scheme': 'http://', 'ssl': False, 'reports': 'std'}

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action({'wizard': 'setup.cfg', 'fail_on_bucket': ['blocked']})

        self.assertEqual(actual, 0)
        self.assertEqual(browser_mock.call_args.args[0]['fail_on_bucket'], ['blocked'])

    def test_should_preserve_fail_on_bucket_cli_override_for_session_load(self):
        """Controller.scan_action() should carry fail-on overrides into restored session params."""

        snapshot = {
            'params': {'host': 'example.com', 'scheme': 'http://', 'ssl': False, 'reports': 'std'},
            '_loaded_from': '/tmp/session.json',
        }
        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action({'session_load': '/tmp/session.json', 'fail_on_bucket': ['blocked']})

        self.assertEqual(actual, 0)
        self.assertEqual(browser_mock.call_args.args[0]['fail_on_bucket'], ['blocked'])

    def test_should_collect_fail_on_matches_in_per_target_rotation_mode(self):
        """Controller.scan_action() should apply CI fail-on checks in per-target mode."""

        browser_first = MagicMock()
        browser_first.result = {'total': {'blocked': 1}}
        browser_second = MagicMock()
        browser_second.result = {'total': {'blocked': 0}}
        transport = MagicMock()
        transport.transport = 'wireguard'
        transport.rotate_mode = 'per-target'
        transport.current_profile_name = 'nl.conf'

        params = {
            'targets': [
                {'host': 'first.example.com', 'scheme': 'http://', 'ssl': False},
                {'host': 'second.example.com', 'scheme': 'https://', 'ssl': True},
            ],
            'reports': 'std',
            'fail_on_bucket': ['blocked'],
            'transport': 'wireguard',
            'transport_profiles': '/tmp/profiles.txt',
            'transport_rotate': 'per-target',
        }

        with patch('src.controller.NetworkTransportManager', return_value=transport), \
                patch('src.controller.browser', side_effect=[browser_first, browser_second]), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.tpl.warning') as warning_mock, \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 1)
        self.assertEqual(transport.rotate.call_count, 2)
        warning_mock.assert_called_with(
            msg='CI/CD fail-on matched: first.example.com blocked=1. Exit code: 1'
        )

    def test_should_reraise_single_target_error_in_per_target_mode(self):
        """Controller.scan_action() should not swallow a single target failure in per-target mode."""

        transport = MagicMock()
        transport.transport = 'wireguard'
        transport.rotate_mode = 'per-target'
        transport.current_profile_name = 'nl.conf'

        params = {
            'targets': [{'host': 'only.example.com', 'scheme': 'http://', 'ssl': False}],
            'reports': 'std',
            'transport': 'wireguard',
            'transport_profiles': '/tmp/profiles.txt',
            'transport_rotate': 'per-target',
        }

        with patch('src.controller.NetworkTransportManager', return_value=transport), \
                patch('src.controller.browser', side_effect=BrowserError('scan failed')), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            with self.assertRaises(SrcError):
                Controller.scan_action(params)

        transport.stop.assert_called_once_with()

    def test_should_return_empty_fail_on_matches_for_non_dict_result(self):
        """Controller._match_fail_on_buckets() should ignore non-dict scan results."""

        self.assertEqual(Controller._match_fail_on_buckets('example.com', None, ['blocked']), [])

    def test_should_record_target_failure_with_missing_host_fallback(self):
        """Controller._record_target_failure() should use '-' when host is absent."""

        with patch('src.controller.tpl.warning') as warning_mock:
            failure = Controller._record_target_failure({}, RuntimeError('boom'))

        self.assertEqual(failure, {'host': '-', 'error': 'boom'})
        warning_mock.assert_called_once_with(msg='Target scan failed: -. boom')


if __name__ == '__main__':
    unittest.main()
