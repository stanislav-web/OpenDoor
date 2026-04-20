# -*- coding: utf-8 -*-

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from urllib.error import URLError

from src.core import CoreSystemError, FileSystemError
from src.core.logger.logger import Logger
from src.lib.package import Package, PackageError


class TestPackage(unittest.TestCase):
    """TestPackage class."""

    def tearDown(self):
        Package.remote_version = None
        logger = Logger.log()
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    def test_check_interpreter_returns_true_for_supported_version(self):
        """Package.check_interpreter() should accept versions within the configured range."""

        info = {'required_versions': {'minor': '3.12', 'major': '3.14'}}

        with patch.dict('src.lib.package.package.CoreConfig', {'info': info}, clear=False), \
                patch('src.lib.package.package.py_sys.version_info', new=SimpleNamespace(major=3, minor=14)):
            self.assertTrue(Package.check_interpreter())

    def test_check_interpreter_returns_status_payload_for_unsupported_version(self):
        """Package.check_interpreter() should return mismatch details when version is unsupported."""

        info = {'required_versions': {'minor': '3.12', 'major': '3.14'}}

        with patch.dict('src.lib.package.package.CoreConfig', {'info': info}, clear=False), \
                patch('src.lib.package.package.py_sys.version_info', new=SimpleNamespace(major=3, minor=11)):
            result = Package.check_interpreter()

        self.assertEqual(result, {'status': False, 'actual': '3.11', 'expected': '3.12 -> 3.14'})

    def test_examples_returns_core_config_examples(self):
        """Package.examples() should proxy the configured examples string."""

        with patch.dict('src.lib.package.package.CoreConfig', {'examples': 'examples block'}, clear=False):
            self.assertEqual(Package.examples(), 'examples block')

    def test_banner_renders_expected_information(self):
        """Package.banner() should render the banner with all summary lines."""

        with patch('src.lib.package.package.Package._Package__directories_count', return_value=10), \
                patch('src.lib.package.package.Package._Package__subdomains_count', return_value=20), \
                patch('src.lib.package.package.Package._Package__browsers_count', return_value=30), \
                patch('src.lib.package.package.Package._Package__proxies_count', return_value=40), \
                patch('src.lib.package.package.Package._Package__license', return_value='License: GPL'):
            banner = Package.banner()

        self.assertIn('Directories: 10', banner)
        self.assertIn('Subdomains: 20', banner)
        self.assertIn('Browsers: 30', banner)
        self.assertIn('Proxies: 40', banner)
        self.assertIn('License: GPL', banner)
        self.assertTrue(banner.startswith('#'))

    def test_banner_wraps_internal_errors(self):
        """Package.banner() should wrap package/file errors into PackageError."""

        with patch('src.lib.package.package.Package._Package__directories_count', side_effect=PackageError('boom')):
            with self.assertRaises(PackageError):
                Package.banner()

    def test_version_formats_all_version_metadata(self):
        """Package.version() should render version metadata using the configured format."""

        with patch.dict('src.lib.package.package.CoreConfig', {'version': '{0}|{1}|{2}|{3}|{4}'}, clear=False), \
                patch('src.lib.package.package.Package._Package__app_name', return_value='OpenDoor'), \
                patch('src.lib.package.package.Package._Package__current_version', return_value='5.0.1'), \
                patch('src.lib.package.package.Package._Package__remote_version', return_value='5.0.2'), \
                patch('src.lib.package.package.Package._Package__repo', return_value='repo-url'), \
                patch('src.lib.package.package.Package._Package__license', return_value='GPL'):
            version = Package.version()

        self.assertEqual(version, 'OpenDoor|5.0.1|5.0.2|repo-url|GPL')

    def test_version_wraps_internal_errors(self):
        """Package.version() should wrap package/file errors into PackageError."""

        with patch('src.lib.package.package.Package._Package__app_name', side_effect=PackageError('broken')):
            with self.assertRaises(PackageError):
                Package.version()

    def test_wizard_normalizes_values_from_cfg(self):
        """Package.wizard() should normalize integers, booleans, None and strings."""

        fake_config = SimpleNamespace(
            _sections={
                'general': {
                    'threads': '10',
                    'debug': 'True',
                    'reports': ' std,txt ',
                    'delay': 'None',
                    'host': ' http://example.com ',
                }
            }
        )

        with patch('src.lib.package.package.filesystem.readcfg', return_value=fake_config):
            params = Package.wizard('setup.cfg')

        self.assertEqual(params['threads'], 10)
        self.assertIs(params['debug'], True)
        self.assertEqual(params['reports'], 'std,txt')
        self.assertIsNone(params['delay'])
        self.assertEqual(params['host'], 'http://example.com')

    def test_wizard_wraps_readcfg_errors(self):
        """Package.wizard() should wrap configuration read errors into PackageError."""

        with patch('src.lib.package.package.filesystem.readcfg', side_effect=FileSystemError('missing')):
            with self.assertRaises(PackageError):
                Package.wizard('missing.cfg')

    def test_docs_opens_documentation_url(self):
        """Package.docs() should delegate to helper.openbrowser()."""

        with patch.dict('src.lib.package.package.CoreConfig', {'info': {'documentation': 'https://docs'}}, clear=False), \
                patch('src.lib.package.package.helper.openbrowser', return_value=True) as open_mock:
            result = Package.docs()

        self.assertTrue(result)
        open_mock.assert_called_once_with('https://docs')

    def test_update_returns_unix_message(self):
        """Package.update() should format the Unix update instructions."""

        with patch.dict(
            'src.lib.package.package.CoreConfig',
            {
                'command': {'cvsupdate': '/usr/bin/env python3 -m pip install --upgrade opendoor'},
                'update': 'STATUS: {status}',
            },
            clear=False,
        ), \
                patch('src.lib.package.package.sys', return_value=SimpleNamespace(is_windows=False)), \
                patch('src.lib.package.package.tpl.line', side_effect=lambda msg='', **kwargs: msg):
            message = Package.update()

        self.assertIn('Automatic in-place update is disabled.', message)
        self.assertIn('/usr/bin/env python3 -m pip install --upgrade opendoor', message)

    def test_update_returns_windows_message(self):
        """Package.update() should use the Windows status template on Windows."""

        with patch.dict('src.lib.package.package.CoreConfig', {'update': 'STATUS: {status}'}, clear=False), \
                patch('src.lib.package.package.sys', return_value=SimpleNamespace(is_windows=True)), \
                patch('src.lib.package.package.tpl.line', return_value='WINDOWS-STATUS') as line_mock:
            message = Package.update()

        self.assertEqual(message, 'STATUS: WINDOWS-STATUS')
        line_mock.assert_called_once_with(key='upd_win_stat')

    def test_update_wraps_core_system_errors(self):
        """Package.update() should wrap core system errors into PackageError."""

        with patch('src.lib.package.package.sys', return_value=SimpleNamespace(is_windows=False)), \
                patch.dict('src.lib.package.package.CoreConfig', {}, clear=True):
            with self.assertRaises(PackageError):
                Package.update()

    def test_local_version_returns_configured_version(self):
        """Package.local_version() should return the local version string."""

        with patch.dict('src.lib.package.package.CoreConfig', {'info': {'version': '5.0.1'}}, clear=False):
            self.assertEqual(Package.local_version(), '5.0.1')

    def test_local_version_wraps_filesystem_errors(self):
        """Package.local_version() should wrap filesystem-originated config errors."""

        class BrokenConfig(object):
            @staticmethod
            def get(_key):
                raise FileSystemError('boom')

        with patch('src.lib.package.package.CoreConfig', BrokenConfig):
            with self.assertRaises(PackageError):
                Package.local_version()

    def test_remote_version_reads_remote_value_and_caches_it(self):
        """Package.__remote_version() should cache the first successful remote lookup."""

        response = MagicMock()
        response.read.return_value = b'5.0.2\nextra'
        context = MagicMock()
        context.__enter__.return_value = response
        context.__exit__.return_value = None

        with patch.dict('src.lib.package.package.CoreConfig', {'info': {'remote_version': 'https://example.test/VERSION'}}, clear=False), \
                patch('src.lib.package.package.urlopen', return_value=context) as urlopen_mock:
            first = Package._Package__remote_version()
            second = Package._Package__remote_version()

        self.assertEqual(first, '5.0.2')
        self.assertEqual(second, '5.0.2')
        urlopen_mock.assert_called_once_with('https://example.test/VERSION', timeout=5)

    def test_remote_version_returns_unavailable_on_network_error(self):
        """Package.__remote_version() should fall back to unavailable on URL errors."""

        with patch.dict('src.lib.package.package.CoreConfig', {'info': {'remote_version': 'https://example.test/VERSION'}}, clear=False), \
                patch('src.lib.package.package.urlopen', side_effect=URLError('offline')):
            self.assertEqual(Package._Package__remote_version(), 'unavailable')

    def test_current_version_uses_green_when_remote_is_unavailable(self):
        """Package.__current_version() should keep the current version green when remote lookup fails."""

        with patch('src.lib.package.package.Package.local_version', return_value='5.0.1'), \
                patch('src.lib.package.package.Package._Package__remote_version', return_value='unavailable'), \
                patch('src.lib.package.package.tpl.line', side_effect=lambda msg, color='white': f'{color}:{msg}'):
            self.assertEqual(Package._Package__current_version(), 'green:5.0.1')

    def test_current_version_uses_red_when_local_is_older(self):
        """Package.__current_version() should colorize local version red when remote is newer."""

        with patch('src.lib.package.package.Package.local_version', return_value='5.0.1'), \
                patch('src.lib.package.package.Package._Package__remote_version', return_value='5.0.2'), \
                patch('src.lib.package.package.helper.is_less', return_value=True), \
                patch('src.lib.package.package.tpl.line', side_effect=lambda msg, color='white': f'{color}:{msg}'):
            self.assertEqual(Package._Package__current_version(), 'red:5.0.1')

    def test_current_version_uses_green_when_local_is_current(self):
        """Package.__current_version() should colorize local version green when it is current."""

        with patch('src.lib.package.package.Package.local_version', return_value='5.0.2'), \
                patch('src.lib.package.package.Package._Package__remote_version', return_value='5.0.2'), \
                patch('src.lib.package.package.helper.is_less', return_value=False), \
                patch('src.lib.package.package.tpl.line', side_effect=lambda msg, color='white': f'{color}:{msg}'):
            self.assertEqual(Package._Package__current_version(), 'green:5.0.2')

    def test_current_version_wraps_package_errors(self):
        """Package.__current_version() should wrap package errors into PackageError."""

        with patch('src.lib.package.package.Package.local_version', side_effect=PackageError('broken')):
            with self.assertRaises(PackageError):
                Package._Package__current_version()

    def test_private_metadata_helpers_return_expected_values(self):
        """Package private metadata helpers should read values from the info config."""

        info = {
            'name': 'OpenDoor',
            'repository': 'https://repo',
            'license': 'GNU General Public License',
        }

        with patch.dict('src.lib.package.package.CoreConfig', {'info': info}, clear=False):
            self.assertEqual(Package._Package__app_name(), 'OpenDoor')
            self.assertEqual(Package._Package__repo(), 'https://repo')
            self.assertEqual(Package._Package__license(), 'GNU General Public License')

    def test_private_metadata_helpers_wrap_filesystem_errors(self):
        """Package private metadata helpers should wrap filesystem-originated lookup errors."""

        class BrokenConfig(object):
            @staticmethod
            def get(_key):
                raise FileSystemError('boom')

        with patch('src.lib.package.package.CoreConfig', BrokenConfig):
            with self.assertRaises(PackageError):
                Package._Package__app_name()
            with self.assertRaises(PackageError):
                Package._Package__repo()
            with self.assertRaises(PackageError):
                Package._Package__license()

    def test_private_counters_read_expected_data_sources(self):
        """Package private counters should read the expected data files."""

        data = {
            'directories': 'dir.dat',
            'subdomains': 'sub.dat',
            'useragents': 'ua.dat',
            'proxies': 'proxy.dat',
        }

        with patch.dict('src.lib.package.package.CoreConfig', {'data': data}, clear=False), \
                patch('src.lib.package.package.filesystem.count_lines', side_effect=[1, 2, 3, 4]) as count_mock:
            self.assertEqual(Package._Package__directories_count(), 1)
            self.assertEqual(Package._Package__subdomains_count(), 2)
            self.assertEqual(Package._Package__browsers_count(), 3)
            self.assertEqual(Package._Package__proxies_count(), 4)

        self.assertEqual(
            count_mock.call_args_list,
            [
                unittest.mock.call('dir.dat'),
                unittest.mock.call('sub.dat'),
                unittest.mock.call('ua.dat'),
                unittest.mock.call('proxy.dat'),
            ]
        )

    def test_private_counters_wrap_errors(self):
        """Package private counters should wrap filesystem errors into PackageError."""

        with patch.dict('src.lib.package.package.CoreConfig', {'data': {'directories': 'dir.dat'}}, clear=False), \
                patch('src.lib.package.package.filesystem.count_lines', side_effect=FileSystemError('boom')):
            with self.assertRaises(PackageError):
                Package._Package__directories_count()

    def test_render_banner_returns_framed_banner(self):
        """Package.__render_banner() should render a framed multi-line banner."""

        banner = Package._Package__render_banner(['Line A', 'Line B'])
        lines = banner.splitlines()

        self.assertGreaterEqual(len(lines), 8)
        self.assertTrue(all(line.startswith('#') and line.endswith('#') for line in lines))
        self.assertIn('Line A', banner)
        self.assertIn('Line B', banner)

    def test_parse_version_boundary_supports_major_minor_and_major_only(self):
        """Package.__parse_version_boundary() should parse both dotted and major-only values."""

        self.assertEqual(Package._Package__parse_version_boundary('3.14'), (3, 14))
        self.assertEqual(Package._Package__parse_version_boundary('4'), (4, 0))


if __name__ == '__main__':
    unittest.main()