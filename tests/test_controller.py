# -*- coding: utf-8 -*-

import os
import io
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import src as src_module
from src import Controller, SrcError
from src.core.logger.logger import Logger
from src.lib import ArgumentsError, BrowserError, PackageError, ReporterError
from src.core.network.exceptions import NetworkTransportError
from src.lib.diff import DiffValidationError
from src.lib.reader import RemoteWordlistError

class TestController(unittest.TestCase):
    """TestController class."""

    def tearDown(self):
        logger = Logger.log()
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    def make_controller(self, ioargs=None):
        """Create a controller instance without running __init__."""

        controller = Controller.__new__(Controller)
        controller.ioargs = ioargs or {}
        return controller

    def test_init_sets_arguments_when_interpreter_is_supported(self):
        """Controller.__init__() should store parsed arguments when interpreter is supported."""

        arguments = MagicMock()
        arguments.get_arguments.return_value = {'version': True}

        with patch('src.controller.events.terminate') as terminate_mock, \
                patch('src.controller.package.check_interpreter', return_value=True), \
                patch('src.controller.args', return_value=arguments):
            controller = Controller()

        terminate_mock.assert_called_once_with()
        self.assertEqual(controller.ioargs, {'version': True})

    def test_init_raises_src_error_for_unsupported_interpreter(self):
        """Controller.__init__() should reject unsupported interpreter versions."""

        with patch('src.controller.events.terminate'), \
                patch('src.controller.package.check_interpreter', return_value={'actual': '3.11', 'expected': '3.12 -> 3.14'}), \
                patch('src.controller.tpl.error', return_value='unsupported runtime'):
            with self.assertRaises(SrcError):
                Controller()

    def test_init_wraps_argument_errors(self):
        """Controller.__init__() should wrap argument parsing errors into SrcError."""

        arguments = MagicMock()
        arguments.get_arguments.side_effect = ArgumentsError('bad arguments')

        with patch('src.controller.events.terminate'), \
                patch('src.controller.package.check_interpreter', return_value=True), \
                patch('src.controller.args', return_value=arguments), \
                patch('src.controller.tpl.error', return_value='formatted error'):
            with self.assertRaises(SrcError):
                Controller()

    def test_run_dispatches_to_scan_action_when_host_is_present(self):
        """Controller.run() should route host-based input to scan_action()."""

        controller = self.make_controller({'host': 'http://example.com'})

        with patch('src.controller.package.banner', return_value='banner') as banner_mock, \
                patch('src.controller.tpl.message') as message_mock, \
                patch.object(Controller, 'scan_action') as scan_mock, \
                patch('src.controller.tpl.debug'):
            controller.run()

        banner_mock.assert_not_called()
        message_mock.assert_not_called()
        scan_mock.assert_called_once_with({'host': 'http://example.com'}, show_banner=True)

    def test_run_dispatches_to_named_action(self):
        """Controller.run() should call the first matching action handler."""

        controller = self.make_controller({'version': True})
        arguments = MagicMock()
        arguments.is_arg_callable.return_value = True

        with patch('src.controller.package.banner', return_value='banner'), \
                patch('src.controller.tpl.message'), \
                patch('src.controller.args', return_value=arguments), \
                patch.object(Controller, 'version_action') as version_mock, \
                patch('src.controller.tpl.debug'):
            controller.run()

        version_mock.assert_called_once_with()

    def test_run_update_action_does_not_require_banner_assets(self):
        """Controller.run() should execute --update without reading scanner data assets."""

        controller = self.make_controller({'update': True})

        with patch('src.controller.package.banner', side_effect=PackageError('missing data')) as banner_mock, \
                patch.object(Controller, 'update_action') as update_mock, \
                patch('src.controller.tpl.debug'):
            result = controller.run()

        self.assertEqual(result, 0)
        banner_mock.assert_not_called()
        update_mock.assert_called_once_with()

    def test_run_skips_non_callable_actions(self):
        """Controller.run() should ignore actions rejected by args.is_arg_callable()."""

        controller = self.make_controller({'version': True})
        arguments = MagicMock()
        arguments.is_arg_callable.return_value = False

        with patch('src.controller.package.banner', return_value='banner'), \
                patch('src.controller.tpl.message'), \
                patch('src.controller.args', return_value=arguments), \
                patch.object(Controller, 'version_action') as version_mock, \
                patch('src.controller.tpl.debug'):
            controller.run()

        version_mock.assert_not_called()

    def test_run_wraps_action_errors(self):
        """Controller.run() should wrap package/browser errors into SrcError."""

        controller = self.make_controller({'version': True})

        with patch('src.controller.package.banner', side_effect=PackageError('boom')), \
                patch('src.controller.tpl.error', return_value='formatted boom'), \
                patch('src.controller.tpl.debug'):
            with self.assertRaises(SrcError):
                controller.run()

    def test_examples_action_prints_examples(self):
        """Controller.examples_action() should print package examples."""

        with patch('src.controller.package.examples', return_value='examples'), \
                patch('src.controller.tpl.message') as message_mock:
            Controller.examples_action()

        message_mock.assert_called_once_with('examples')

    def test_update_action_prints_update_message(self):
        """Controller.update_action() should print package update instructions."""

        with patch('src.controller.package.update', return_value='update'), \
                patch('src.controller.tpl.message') as message_mock:
            Controller.update_action()

        message_mock.assert_called_once_with('update')

    def test_update_action_wraps_package_errors(self):
        """Controller.update_action() should wrap package failures into SrcError."""

        with patch('src.controller.package.update', side_effect=PackageError('boom')):
            with self.assertRaises(SrcError):
                Controller.update_action()

    def test_docs_action_invokes_package_docs(self):
        """Controller.docs_action() should invoke package.docs()."""

        with patch('src.controller.package.docs') as docs_mock:
            Controller.docs_action()

        docs_mock.assert_called_once_with()

    def test_docs_action_wraps_package_errors(self):
        """Controller.docs_action() should wrap package failures into SrcError."""

        with patch('src.controller.package.docs', side_effect=PackageError('boom')):
            with self.assertRaises(SrcError):
                Controller.docs_action()

    def test_version_action_prints_version_message(self):
        """Controller.version_action() should print package version information."""

        with patch('src.controller.package.version', return_value='version'), \
                patch('src.controller.tpl.message') as message_mock:
            Controller.version_action()

        message_mock.assert_called_once_with('version')

    def test_version_action_wraps_package_errors(self):
        """Controller.version_action() should wrap package failures into SrcError."""

        with patch('src.controller.package.version', side_effect=PackageError('boom')):
            with self.assertRaises(SrcError):
                Controller.version_action()

    def test_local_version_action_prints_local_version(self):
        """Controller.local_version() should print the local version."""

        with patch('src.controller.package.local_version', return_value='5.0.1'), \
                patch('src.controller.tpl.message') as message_mock:
            Controller.local_version()

        message_mock.assert_called_once_with('5.0.1')

    def test_local_version_action_wraps_package_errors(self):
        """Controller.local_version() should wrap package failures into SrcError."""

        with patch('src.controller.package.local_version', side_effect=PackageError('boom')):
            with self.assertRaises(SrcError):
                Controller.local_version()

    def test_scan_action_runs_wizard_and_browser_flow(self):
        """Controller.scan_action() should resolve wizard params and run the browser flow."""

        browser_instance = MagicMock()
        resolved_params = {'host': 'http://example.com', 'reports': 'std'}

        with patch('src.controller.tpl.info') as info_mock, \
                patch('src.controller.package.wizard', return_value=resolved_params) as wizard_mock, \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({'wizard': 'setup.cfg'})

        info_mock.assert_any_call(key='load_wizard', config='setup.cfg')
        info_mock.assert_any_call(key='use_reports')
        wizard_mock.assert_called_once_with('setup.cfg')
        browser_mock.assert_called_once_with(resolved_params)
        browser_instance.ping.assert_called_once_with()
        browser_instance.scan.assert_called_once_with()
        browser_instance.done.assert_called_once_with()

    def test_scan_action_prompts_when_existing_report_is_detected(self):
        """Controller.scan_action() should prompt when a report already exists."""

        browser_instance = MagicMock()
        params = {'host': 'http://example.com', 'reports': 'txt'}

        with patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=True), \
                patch('src.controller.tpl.prompt') as prompt_mock, \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action(params)

        prompt_mock.assert_called_once_with(key='logged')
        browser_instance.ping.assert_called_once_with()
        browser_instance.scan.assert_called_once_with()
        browser_instance.done.assert_called_once_with()

    def test_scan_action_cancels_prompt_interrupt_and_continues(self):
        """Controller.scan_action() should cancel prompt interruption and continue the scan flow."""

        browser_instance = MagicMock()
        params = {'host': 'http://example.com', 'reports': 'txt'}

        with patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=True), \
                patch('src.controller.tpl.prompt', side_effect=KeyboardInterrupt), \
                patch('src.controller.tpl.cancel') as cancel_mock, \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action(params)

        cancel_mock.assert_called_once_with(key='abort')
        browser_instance.ping.assert_called_once_with()
        browser_instance.scan.assert_called_once_with()
        browser_instance.done.assert_called_once_with()

    def test_scan_action_wraps_reporter_and_browser_errors(self):
        """Controller.scan_action() should wrap browser and reporter failures into SrcError."""

        with patch('src.controller.browser', side_effect=BrowserError('boom')):
            with self.assertRaises(SrcError):
                Controller.scan_action({'host': 'http://example.com'})

        with patch('src.controller.browser', return_value=MagicMock()), \
                patch('src.controller.reporter.is_reported', side_effect=ReporterError('boom')):
            with self.assertRaises(SrcError):
                Controller.scan_action({'host': 'http://example.com'})

    def test_scan_action_cancels_on_keyboard_interrupt_from_browser(self):
        """Controller.scan_action() should cancel when the browser flow raises KeyboardInterrupt."""

        browser_instance = MagicMock()
        browser_instance.scan.side_effect = KeyboardInterrupt

        with patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.cancel') as cancel_mock, \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({'host': 'http://example.com', 'reports': 'txt'})

        cancel_mock.assert_called_once_with(key='abort')

    def test_run_calls_scan_action_when_targets_are_present(self):
        """Controller.run() should treat target lists as a scan action."""

        controller = self.make_controller({'targets': [{'host': 'example.com', 'scheme': 'http://', 'ssl': False}]})

        with patch('src.controller.package.banner', return_value='banner'),                 patch('src.controller.tpl.message'),                 patch.object(Controller, 'scan_action') as scan_mock,                 patch('src.controller.tpl.debug'):
            controller.run()

        scan_mock.assert_called_once_with(controller.ioargs, show_banner=True)

    def test_scan_action_runs_browser_flow_for_each_target(self):
        """Controller.scan_action() should scan each normalized target sequentially."""

        browser_first = MagicMock()
        browser_second = MagicMock()
        params = {
            'targets': [
                {'host': 'example.com', 'scheme': 'http://', 'ssl': False},
                {'host': 'secure.example.com', 'scheme': 'https://', 'ssl': True},
            ],
            'reports': 'std',
        }

        with patch('src.controller.tpl.info') as info_mock,                 patch('src.controller.browser', side_effect=[browser_first, browser_second]) as browser_mock,                 patch('src.controller.reporter.is_reported', return_value=False),                 patch('src.controller.reporter.default', 'std'):
            Controller.scan_action(params)

        info_mock.assert_called_once_with(key='use_reports')
        self.assertEqual(browser_mock.call_count, 2)
        browser_mock.assert_any_call({'targets': params['targets'], 'reports': 'std', 'host': 'example.com', 'scheme': 'http://', 'ssl': False})
        browser_mock.assert_any_call({'targets': params['targets'], 'reports': 'std', 'host': 'secure.example.com', 'scheme': 'https://', 'ssl': True})
        browser_first.ping.assert_called_once_with()
        browser_first.scan.assert_called_once_with()
        browser_first.done.assert_called_once_with()
        browser_second.ping.assert_called_once_with()
        browser_second.scan.assert_called_once_with()
        browser_second.done.assert_called_once_with()

    def test_scan_action_should_continue_after_batch_target_error(self):
        """Controller.scan_action() should continue multi-target scans after a target failure."""

        browser_second = MagicMock()
        browser_second.result = {'total': {'success': 1}}
        params = {
            'targets': [
                {'host': 'broken.example.com', 'scheme': 'http://', 'ssl': False},
                {'host': 'next.example.com', 'scheme': 'https://', 'ssl': True},
            ],
            'reports': 'std',
        }

        with patch('src.controller.browser', side_effect=[BrowserError('boom'), browser_second]) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.tpl.warning') as warning_mock, \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 1)
        self.assertEqual(browser_mock.call_count, 2)
        browser_second.scan.assert_called_once_with()
        browser_second.done.assert_called_once_with()
        self.assertEqual(warning_mock.call_count, 2)
        warning_mock.assert_any_call(msg='Target scan failed: broken.example.com. str: boom')

    def test_format_target_failures_should_handle_missing_values(self):
        """Controller._format_target_failures() should format batch scan failures."""

        self.assertEqual(
            Controller._format_target_failures([
                {'host': 'first.example.com', 'error': 'boom'},
                {'host': None, 'error': ''},
            ]),
            'first.example.com: boom; -: -'
        )

    def test_resolve_scan_targets_falls_back_to_single_host(self):
        """Controller._resolve_scan_targets() should preserve the single-host flow."""

        actual = Controller._resolve_scan_targets({
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
        })

        self.assertEqual(actual, [
            {'host': 'example.com', 'scheme': 'http://', 'ssl': False}
        ])

    def test_scan_action_loads_session_snapshot_and_runs_browser_once(self):
        """Controller.scan_action() should restore params from session snapshot."""

        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
            }
        }

        browser_mock = MagicMock()

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_mock), \
                patch('src.controller.reporter.is_reported', return_value=False):
            Controller.scan_action({'session_load': '/tmp/session.json'})

        browser_mock.ping.assert_called_once()
        browser_mock.scan.assert_called_once()
        browser_mock.done.assert_called_once()

    def test_run_returns_scan_action_exit_code(self):
        """Controller.run() should propagate scan_action() exit code."""

        controller = self.make_controller({'host': 'http://example.com'})

        with patch('src.controller.package.banner', return_value='banner'), \
                patch('src.controller.tpl.message'), \
                patch.object(Controller, 'scan_action', return_value=1) as scan_mock, \
                patch('src.controller.tpl.debug'):
            actual = controller.run()

        self.assertEqual(actual, 1)
        scan_mock.assert_called_once_with({'host': 'http://example.com'}, show_banner=True)

    def test_main_returns_controller_exit_code_for_installed_entrypoint(self):
        """src.main() should return Controller.run() exit code for console scripts."""

        controller = MagicMock()
        controller.run.return_value = 1

        with patch('src.Controller', return_value=controller):
            actual = src_module.main()

        self.assertEqual(actual, 1)
        controller.run.assert_called_once_with()

    def test_main_returns_zero_when_controller_returns_none(self):
        """src.main() should normalize missing controller return values to success."""

        controller = MagicMock()
        controller.run.return_value = None

        with patch('src.Controller', return_value=controller):
            actual = src_module.main()

        self.assertEqual(actual, 0)

    def test_main_returns_one_when_controller_raises_src_error(self):
        """src.main() should return failure instead of swallowing SrcError as success."""

        with patch('src.Controller', side_effect=SrcError('boom')):
            actual = src_module.main()

        self.assertEqual(actual, 1)

    def test_scan_action_returns_one_when_fail_on_bucket_matches(self):
        """Controller.scan_action() should return 1 when selected CI bucket is found."""

        browser_instance = MagicMock()
        browser_instance.result = {
            'total': {
                'success': 2,
                'auth': 1,
                'items': 10,
                'workers': 1,
            }
        }

        params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'fail_on_bucket': ['auth', 'blocked'],
        }

        with patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info') as info_mock, \
                patch('src.controller.tpl.warning') as warning_mock, \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 1)
        info_mock.assert_any_call(msg='CI/CD mode enabled: fail-on-bucket=auth,blocked')
        warning_mock.assert_called_once()
        browser_instance.ping.assert_called_once_with()
        browser_instance.scan.assert_called_once_with()
        browser_instance.done.assert_called_once_with()

    def test_scan_action_returns_zero_when_fail_on_bucket_has_no_matches(self):
        """Controller.scan_action() should return 0 when selected CI buckets are absent."""

        browser_instance = MagicMock()
        browser_instance.result = {
            'total': {
                'success': 2,
                'items': 10,
                'workers': 1,
            }
        }

        params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'fail_on_bucket': ['blocked', 'forbidden'],
        }

        with patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info') as info_mock, \
                patch('src.controller.tpl.warning') as warning_mock, \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 0)
        info_mock.assert_any_call(msg='CI/CD fail-on passed: no matched buckets. Exit code: 0')
        warning_mock.assert_not_called()

    def test_scan_action_scans_all_targets_before_ci_fail_exit(self):
        """Controller.scan_action() should finish all targets before returning CI failure."""

        browser_first = MagicMock()
        browser_first.result = {
            'total': {
                'success': 0,
            }
        }

        browser_second = MagicMock()
        browser_second.result = {
            'total': {
                'blocked': 3,
            }
        }

        params = {
            'targets': [
                {'host': 'first.example.com', 'scheme': 'http://', 'ssl': False},
                {'host': 'second.example.com', 'scheme': 'https://', 'ssl': True},
            ],
            'reports': 'std',
            'fail_on_bucket': ['blocked'],
        }

        with patch('src.controller.browser', side_effect=[browser_first, browser_second]) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.tpl.warning') as warning_mock, \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 1)
        self.assertEqual(browser_mock.call_count, 2)
        browser_first.done.assert_called_once_with()
        browser_second.done.assert_called_once_with()
        warning_mock.assert_called_once()

    def test_match_fail_on_buckets_should_ignore_missing_and_non_numeric_counts(self):
        """Controller._match_fail_on_buckets() should only return positive numeric bucket counts."""

        actual = Controller._match_fail_on_buckets(
            'example.com',
            {
                'total': {
                    'success': 2,
                    'blocked': 'bad',
                    'items': 10,
                }
            },
            ['success', 'blocked', 'auth']
        )

        self.assertEqual(actual, [
            {
                'host': 'example.com',
                'bucket': 'success',
                'count': 2,
            }
        ])

    def test_scan_action_runs_auto_calibration_before_scan(self):
        """Controller.scan_action() should run auto-calibration before scan when enabled."""

        browser_instance = MagicMock()
        params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'auto_calibrate': True,
        }

        with patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 0)
        browser_instance.ping.assert_called_once_with()
        browser_instance.calibrate.assert_called_once_with()
        browser_instance.scan.assert_called_once_with()
        browser_instance.done.assert_called_once_with()

    def test_scan_action_preserves_auto_calibration_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve auto-calibration CLI overrides for wizard flow."""

        browser_instance = MagicMock()
        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'auto_calibrate': True,
                'calibration_samples': 9,
                'calibration_threshold': 0.93,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['auto_calibrate'])
        self.assertEqual(passed_params['calibration_samples'], 9)
        self.assertEqual(passed_params['calibration_threshold'], 0.93)
        browser_instance.calibrate.assert_called_once_with()

    def test_scan_action_preserves_auto_calibration_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve auto-calibration CLI overrides for session resume."""

        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
            }
        }

        browser_instance = MagicMock()

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'auto_calibrate': True,
                'calibration_samples': 9,
                'calibration_threshold': 0.93,
            })

        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['auto_calibrate'])
        self.assertEqual(passed_params['calibration_samples'], 9)
        self.assertEqual(passed_params['calibration_threshold'], 0.93)
        browser_instance.calibrate.assert_called_once_with()

    def test_resolve_scan_targets_should_return_empty_list_without_target_source(self):
        """Controller._resolve_scan_targets() should return an empty list without target source."""

        actual = Controller._resolve_scan_targets({})

        self.assertEqual(actual, [])

    def test_scan_action_should_start_and_stop_transport_once_for_all_targets(self):
        """Controller.scan_action() should wrap all targets with one transport session."""

        browser_first = MagicMock()
        browser_first.result = {'total': {'success': 0}}

        browser_second = MagicMock()
        browser_second.result = {'total': {'success': 0}}

        transport = MagicMock()
        transport.transport = 'wireguard'
        transport.rotate_mode = 'none'
        transport.current_profile_name = 'nl.conf'

        params = {
            'targets': [
                {'host': 'first.example.com', 'scheme': 'http://', 'ssl': False},
                {'host': 'second.example.com', 'scheme': 'https://', 'ssl': True},
            ],
            'reports': 'std',
            'transport': 'wireguard',
            'transport_profile': '/tmp/nl.conf',
        }

        with patch('src.controller.NetworkTransportManager', return_value=transport), \
                patch('src.controller.browser', side_effect=[browser_first, browser_second]) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 0)
        transport.start.assert_called_once_with()
        transport.stop.assert_called_once_with()
        transport.rotate.assert_not_called()
        self.assertEqual(browser_mock.call_count, 2)
        browser_first.scan.assert_called_once_with()
        browser_second.scan.assert_called_once_with()

    def test_scan_action_should_rotate_transport_per_target(self):
        """Controller.scan_action() should rotate transport for each target in per-target mode."""

        browser_first = MagicMock()
        browser_first.result = {'total': {'success': 0}}

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
            'transport': 'wireguard',
            'transport_profiles': '/tmp/profiles.txt',
            'transport_rotate': 'per-target',
        }

        with patch('src.controller.NetworkTransportManager', return_value=transport), \
                patch('src.controller.browser', side_effect=[browser_first, browser_second]) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 0)
        self.assertEqual(transport.rotate.call_count, 2)
        self.assertEqual(transport.start.call_count, 2)
        self.assertEqual(transport.stop.call_count, 2)
        self.assertEqual(browser_mock.call_count, 2)

    def test_scan_action_should_continue_after_per_target_transport_error(self):
        """Controller.scan_action() should continue per-target transport batches after one failure."""

        browser_second = MagicMock()
        browser_second.result = {'total': {'success': 1}}

        transport = MagicMock()
        transport.transport = 'wireguard'
        transport.rotate_mode = 'per-target'
        transport.current_profile_name = 'nl.conf'
        transport.start.side_effect = [NetworkTransportError('wg failed'), None]

        params = {
            'targets': [
                {'host': 'first.example.com', 'scheme': 'http://', 'ssl': False},
                {'host': 'second.example.com', 'scheme': 'https://', 'ssl': True},
            ],
            'reports': 'std',
            'transport': 'wireguard',
            'transport_profiles': '/tmp/profiles.txt',
            'transport_rotate': 'per-target',
        }

        with patch('src.controller.NetworkTransportManager', return_value=transport), \
                patch('src.controller.browser', return_value=browser_second) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.tpl.warning') as warning_mock, \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 1)
        self.assertEqual(transport.rotate.call_count, 2)
        self.assertEqual(transport.start.call_count, 2)
        transport.stop.assert_called_once_with()
        browser_mock.assert_called_once()
        browser_second.scan.assert_called_once_with()
        warning_mock.assert_any_call(msg='Target scan failed: first.example.com. wg failed')

    def test_scan_action_should_stop_transport_when_scan_fails(self):
        """Controller.scan_action() should stop transport when browser scan fails."""

        browser_instance = MagicMock()
        browser_instance.scan.side_effect = BrowserError('scan failed')

        transport = MagicMock()
        transport.transport = 'openvpn'
        transport.rotate_mode = 'none'
        transport.current_profile_name = 'nl.ovpn'

        params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'transport': 'openvpn',
            'transport_profile': '/tmp/nl.ovpn',
        }

        with patch('src.controller.NetworkTransportManager', return_value=transport), \
                patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            with self.assertRaises(SrcError):
                Controller.scan_action(params)

        transport.start.assert_called_once_with()
        transport.stop.assert_called_once_with()

    def test_scan_action_should_not_scan_when_transport_start_fails(self):
        """Controller.scan_action() should abort before browser flow when transport start fails."""

        transport = MagicMock()
        transport.transport = 'wireguard'
        transport.rotate_mode = 'none'
        transport.current_profile_name = 'nl.conf'
        transport.start.side_effect = NetworkTransportError('wg failed')

        params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'transport': 'wireguard',
            'transport_profile': '/tmp/nl.conf',
        }

        with patch('src.controller.NetworkTransportManager', return_value=transport), \
                patch('src.controller.browser') as browser_mock, \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            with self.assertRaises(SrcError):
                Controller.scan_action(params)

        browser_mock.assert_not_called()
        transport.start.assert_called_once_with()
        transport.stop.assert_not_called()

    def test_scan_action_should_preserve_transport_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve explicit transport CLI overrides for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        transport = MagicMock()
        transport.transport = 'wireguard'
        transport.rotate_mode = 'none'
        transport.current_profile_name = 'nl.conf'

        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'transport': 'direct',
            'transport_rotate': 'none',
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.NetworkTransportManager', return_value=transport) as transport_mock, \
                patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'transport': 'wireguard',
                'transport_profile': '/tmp/nl.conf',
                'transport_rotate': 'none',
            })

        passed_params = transport_mock.call_args[0][0]
        self.assertEqual(passed_params['transport'], 'wireguard')
        self.assertEqual(passed_params['transport_profile'], '/tmp/nl.conf')
        self.assertEqual(passed_params['transport_rotate'], 'none')

    def test_scan_action_should_not_override_wizard_transport_with_default_direct(self):
        """Controller.scan_action() should not override wizard transport with default direct values."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        transport = MagicMock()
        transport.transport = 'wireguard'
        transport.rotate_mode = 'none'
        transport.current_profile_name = 'wizard.conf'

        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'transport': 'wireguard',
            'transport_profile': '/tmp/wizard.conf',
            'transport_rotate': 'none',
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.NetworkTransportManager', return_value=transport) as transport_mock, \
                patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'transport': 'direct',
                'transport_rotate': 'none',
            })

        passed_params = transport_mock.call_args[0][0]
        self.assertEqual(passed_params['transport'], 'wireguard')
        self.assertEqual(passed_params['transport_profile'], '/tmp/wizard.conf')

    def test_scan_action_should_preserve_transport_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit transport CLI overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        transport = MagicMock()
        transport.transport = 'openvpn'
        transport.rotate_mode = 'none'
        transport.current_profile_name = 'nl.ovpn'

        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'transport': 'direct',
                'transport_rotate': 'none',
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.NetworkTransportManager', return_value=transport) as transport_mock, \
                patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'transport': 'openvpn',
                'transport_profile': '/tmp/nl.ovpn',
                'transport_rotate': 'none',
                'transport_bin': '/usr/bin/openvpn',
                'openvpn_auth': '/tmp/auth.txt',
            })

        passed_params = transport_mock.call_args[0][0]
        self.assertEqual(passed_params['transport'], 'openvpn')
        self.assertEqual(passed_params['transport_profile'], '/tmp/nl.ovpn')
        self.assertEqual(passed_params['transport_bin'], '/usr/bin/openvpn')
        self.assertEqual(passed_params['openvpn_auth'], '/tmp/auth.txt')

    def test_scan_action_should_preserve_header_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve explicit --header overrides for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'header': ['X-Wizard: old'],
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'header': ['X-CLI: yes'],
            })

        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['header'], ['X-CLI: yes'])

    def test_scan_action_should_preserve_proxy_list_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve explicit proxy-list CLI overrides for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'proxy': 'http://wizard-proxy:8080',
            'proxy_pool': True,
            'proxy_list': None,
            'proxy_rotation': 'random',
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'proxy_list': '/tmp/cli-proxies.txt',
                'proxy_rotation': 'sequential',
            })

        passed_params = browser_mock.call_args[0][0]
        self.assertIsNone(passed_params.get('proxy'))
        self.assertIsNot(passed_params.get('proxy_pool'), True)
        self.assertEqual(passed_params['proxy_list'], '/tmp/cli-proxies.txt')
        self.assertEqual(passed_params['proxy_rotation'], 'sequential')

    def test_scan_action_should_not_override_wizard_proxy_with_default_values(self):
        """Controller.scan_action() should not clear wizard proxy settings with CLI defaults."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'proxy': 'socks5h://127.0.0.1:9050',
            'proxy_pool': False,
            'proxy_list': None,
            'proxy_rotation': 'random',
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'proxy_pool': False,
                'proxy_rotation': None,
            })

        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['proxy'], 'socks5h://127.0.0.1:9050')
        self.assertIs(passed_params.get('proxy_pool'), False)
        self.assertIsNone(passed_params.get('proxy_list'))
        self.assertEqual(passed_params['proxy_rotation'], 'random')

    def test_scan_action_should_preserve_standalone_proxy_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit standalone proxy CLI overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'proxy': None,
                'proxy_pool': True,
                'proxy_list': '/tmp/session-proxies.txt',
                'proxy_rotation': 'sequential',
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'proxy': 'socks5h://127.0.0.1:9050',
            })

        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['proxy'], 'socks5h://127.0.0.1:9050')
        self.assertIsNot(passed_params.get('proxy_pool'), True)
        self.assertIsNone(passed_params.get('proxy_list'))
        self.assertIsNone(passed_params.get('proxy_rotation'))

    def test_scan_action_should_preserve_proxy_pool_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit built-in proxy-pool CLI overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'proxy': 'http://session-proxy:8080',
                'proxy_pool': False,
                'proxy_list': '/tmp/session-proxies.txt',
                'proxy_rotation': 'sequential',
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'proxy_pool': True,
            })

        passed_params = browser_mock.call_args[0][0]
        self.assertIsNone(passed_params.get('proxy'))
        self.assertIs(passed_params.get('proxy_pool'), True)
        self.assertIsNone(passed_params.get('proxy_list'))
        self.assertIsNone(passed_params.get('proxy_rotation'))

    def test_scan_action_should_preserve_header_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit --header overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'header': ['X-Session: old'],
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'header': ['X-Resume: yes'],
            })

        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['header'], ['X-Resume: yes'])

    def test_scan_action_should_preserve_proxy_list_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit proxy-list CLI overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'proxy': 'http://session-proxy:8080',
                'proxy_pool': True,
                'proxy_list': None,
                'proxy_rotation': 'random',
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'proxy_list': '/tmp/cli-proxies.txt',
                'proxy_rotation': 'sequential',
            })

        passed_params = browser_mock.call_args[0][0]
        self.assertIsNone(passed_params.get('proxy'))
        self.assertIsNot(passed_params.get('proxy_pool'), True)
        self.assertEqual(passed_params['proxy_list'], '/tmp/cli-proxies.txt')
        self.assertEqual(passed_params['proxy_rotation'], 'sequential')

    def test_collect_proxy_cli_overrides_should_preserve_proxy_list_rotation(self):
        """Controller._collect_proxy_cli_overrides() should keep explicit proxy-list rotation."""

        actual = Controller._collect_proxy_cli_overrides({
            'proxy_list': '/tmp/proxies.txt',
            'proxy_rotation': 'sequential',
        })

        self.assertEqual(actual, {
            'proxy': None,
            'proxy_pool': False,
            'proxy_list': '/tmp/proxies.txt',
            'proxy_rotation': 'sequential',
        })

    def test_collect_proxy_cli_overrides_should_preserve_proxy_list_without_rotation(self):
        """Controller._collect_proxy_cli_overrides() should not invent proxy-list rotation."""

        actual = Controller._collect_proxy_cli_overrides({
            'proxy_list': '/tmp/proxies.txt',
        })

        self.assertEqual(actual, {
            'proxy': None,
            'proxy_pool': False,
            'proxy_list': '/tmp/proxies.txt',
        })

    def test_scan_action_should_emit_transport_debug_when_enabled(self):
        """Controller.scan_action() should expose transport lifecycle in debug mode."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        transport = MagicMock()
        transport.transport = 'wireguard'
        transport.rotate_mode = 'none'
        transport.current_profile_name = 'nl.conf'

        params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'debug': 1,
            'transport': 'wireguard',
            'transport_profile': '/tmp/nl.conf',
            'transport_healthcheck_url': 'https://ifconfig.me',
        }

        with patch('src.controller.NetworkTransportManager', return_value=transport), \
                patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.tpl.debug') as debug_mock, \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 0)
        messages = [call.kwargs.get('msg') for call in debug_mock.call_args_list]
        self.assertTrue(any('Network transport starting: mode=wireguard' in msg for msg in messages))
        self.assertTrue(any('healthcheck=https://ifconfig.me' in msg for msg in messages))
        self.assertTrue(any('Network transport stopped: mode=wireguard' in msg for msg in messages))

    def test_debug_transport_should_emit_path_details_at_debug_level_two(self):
        """Controller._debug_transport() should include transport paths at debug level two."""

        transport = MagicMock()
        transport.transport = 'openvpn'
        transport.current_profile_name = 'nl.ovpn'
        transport.rotate_mode = 'none'

        params = {
            'debug': 2,
            'transport_timeout': 11,
            'transport_healthcheck_url': 'https://ifconfig.me',
            'transport_profile': '/tmp/nl.ovpn',
            'transport_profiles': '/tmp/profiles.txt',
            'transport_bin': '/usr/sbin/openvpn',
        }

        with patch('src.controller.tpl.debug') as debug_mock:
            Controller._debug_transport(params, transport, 'started')

        messages = [call.kwargs.get('msg') for call in debug_mock.call_args_list]
        self.assertTrue(any('Network transport started: mode=openvpn' in msg for msg in messages))
        self.assertTrue(any('Network transport paths: profile=/tmp/nl.ovpn' in msg for msg in messages))
        self.assertTrue(any('profiles=/tmp/profiles.txt' in msg for msg in messages))
        self.assertTrue(any('bin=/usr/sbin/openvpn' in msg for msg in messages))

    def test_is_debug_enabled_should_reject_invalid_debug_values(self):
        """Controller._is_debug_enabled() should treat invalid debug values as disabled."""

        self.assertFalse(Controller._is_debug_enabled({'debug': 'bad'}, level=1))
        self.assertFalse(Controller._is_debug_enabled({'debug': object()}, level=1))

    def test_scan_action_should_not_emit_transport_debug_when_disabled(self):
        """Controller.scan_action() should keep transport diagnostics behind debug mode."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}

        transport = MagicMock()
        transport.transport = 'wireguard'
        transport.rotate_mode = 'none'
        transport.current_profile_name = 'nl.conf'

        params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'debug': 0,
            'transport': 'wireguard',
            'transport_profile': '/tmp/nl.conf',
        }

        with patch('src.controller.NetworkTransportManager', return_value=transport), \
                patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.tpl.debug') as debug_mock, \
                patch('src.controller.reporter.default', 'std'):
            actual = Controller.scan_action(params)

        self.assertEqual(actual, 0)
        debug_mock.assert_not_called()

    def test_collect_transport_cli_overrides_should_ignore_default_direct_values(self):
        """Controller._collect_transport_cli_overrides() should ignore default direct/none values."""

        actual = Controller._collect_transport_cli_overrides({
            'transport': 'direct',
            'transport_rotate': 'none',
        })

        self.assertEqual(actual, {})

    def test_collect_transport_cli_overrides_should_collect_explicit_vpn_values(self):
        """Controller._collect_transport_cli_overrides() should collect explicit VPN transport values."""

        actual = Controller._collect_transport_cli_overrides({
            'transport': 'wireguard',
            'transport_profile': '/tmp/nl.conf',
            'transport_rotate': 'none',
            'transport_timeout': 15,
            'transport_healthcheck_url': 'https://example.com/ip',
        })

        self.assertEqual(actual, {
            'transport': 'wireguard',
            'transport_profile': '/tmp/nl.conf',
            'transport_rotate': 'none',
            'transport_timeout': 15,
            'transport_healthcheck_url': 'https://example.com/ip',
        })

    def test_run_dispatches_to_diff_action_before_scan(self):
        """Controller.run() should route diff mode without starting a scan."""

        controller = self.make_controller({'diff': 'old.sqlite:new.sqlite', 'reports': 'std'})

        with patch('src.controller.package.banner', return_value='banner'), \
                patch('src.controller.tpl.message'), \
                patch.object(Controller, 'diff_action', return_value=0) as diff_mock, \
                patch.object(Controller, 'scan_action') as scan_mock, \
                patch('src.controller.tpl.debug'):
            actual = controller.run()

        self.assertEqual(actual, 0)
        diff_mock.assert_called_once_with(controller.ioargs)
        scan_mock.assert_not_called()

    def test_diff_action_prints_stdout_and_does_not_scan(self):
        """Controller.diff_action() should compare reports locally and print stdout output."""

        previous = MagicMock()
        current = MagicMock()
        result = MagicMock()

        with patch('src.controller.DiffReportReader') as reader_cls, \
                patch('src.controller.DiffReportComparator') as comparator_cls, \
                patch('src.controller.DiffStdoutFormatter') as formatter_cls, \
                patch('src.controller.tpl.message') as message_mock, \
                patch('src.controller.browser') as browser_mock:
            reader_cls.return_value.read_pair.return_value = (previous, current)
            comparator_cls.return_value.compare.return_value = result
            formatter_cls.return_value.format.return_value = 'diff output\n'

            actual = Controller.diff_action({'diff': 'old.sqlite:new.sqlite', 'reports': 'std'})

        self.assertEqual(actual, 0)
        reader_cls.return_value.read_pair.assert_called_once_with('old.sqlite:new.sqlite')
        comparator_cls.return_value.compare.assert_called_once_with(previous, current)
        message_mock.assert_called_once_with('diff output\n')
        browser_mock.assert_not_called()

    def test_diff_action_writes_json_when_requested(self):
        """Controller.diff_action() should write deterministic JSON when reports include json."""

        previous = MagicMock()
        current = MagicMock()
        result = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.controller.DiffReportReader') as reader_cls, \
                    patch('src.controller.DiffReportComparator') as comparator_cls, \
                    patch('src.controller.DiffStdoutFormatter') as formatter_cls, \
                    patch('src.controller.DiffResultSerializer') as serializer_cls, \
                    patch('src.controller.tpl.message'), \
                    patch('src.controller.tpl.info') as info_mock:
                reader_cls.return_value.read_pair.return_value = (previous, current)
                comparator_cls.return_value.compare.return_value = result
                formatter_cls.return_value.format.return_value = 'diff output\n'
                serializer_cls.return_value.serialize.return_value = {'summary': {'added': 1}, 'added': [], 'removed': [], 'changed': []}

                actual = Controller.diff_action({
                    'diff': 'old.sqlite:new.sqlite',
                    'reports': 'std,json',
                    'reports_dir': tmpdir,
                })

            self.assertEqual(actual, 0)
            output_path = os.path.join(tmpdir, 'opendoor-diff.json')
            with open(output_path, encoding='utf-8') as handler:
                self.assertIn('"added": 1', handler.read())
            info_mock.assert_called_once_with(msg='JsonDiffReport : {0}'.format(output_path))

    def test_diff_reports_dir_should_fallback_for_missing_or_empty_list_values(self):
        """Controller._diff_reports_dir() should fallback to cwd for missing and empty list values."""

        with patch('src.controller.os.getcwd', return_value='/tmp/opendoor-cwd'):
            self.assertEqual(
                Controller._diff_reports_dir({'reports_dir': []}),
                os.path.abspath('/tmp/opendoor-cwd')
            )
            self.assertEqual(
                Controller._diff_reports_dir({}),
                os.path.abspath('/tmp/opendoor-cwd')
            )

    def test_diff_action_wraps_validation_errors(self):
        """Controller.diff_action() should expose graceful diff validation errors."""

        with patch('src.controller.DiffReportReader') as reader_cls:
            reader_cls.return_value.read_pair.side_effect = DiffValidationError('bad diff')
            with self.assertRaises(SrcError):
                Controller.diff_action({'diff': 'bad', 'reports': 'std'})

    def test_controller_should_scan_targets_from_stdin_cli_flow(self):
        """CLI --stdin should read mixed targets from STDIN and scan each target."""

        controller = Controller.__new__(Controller)

        browser_first = MagicMock()
        browser_second = MagicMock()

        with patch('src.controller.package.check_interpreter', return_value=True), \
                patch('src.controller.events.terminate'), \
                patch('src.core.options.options.sys.argv', ['opendoor.py', '--stdin', '--reports', 'std']), \
                patch('src.core.options.filter.sys.stdin', io.StringIO('example.com\nhttps://secure.example.com\n')), \
                patch('src.controller.package.banner', return_value='banner'), \
                patch('src.controller.tpl.message'), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.browser', side_effect=[browser_first, browser_second]) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.reporter.default', 'std'):
            Controller.__init__(controller)
            actual = controller.run()

        self.assertEqual(actual, 0)
        self.assertEqual(browser_mock.call_count, 2)

        first_params = browser_mock.call_args_list[0].args[0]
        second_params = browser_mock.call_args_list[1].args[0]

        expected_targets = [
            {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'source': 'example.com',
            },
            {
                'host': 'secure.example.com',
                'scheme': 'https://',
                'ssl': True,
                'source': 'https://secure.example.com',
            },
        ]

        self.assertEqual(first_params['targets'], expected_targets)
        self.assertEqual(first_params['host'], 'example.com')
        self.assertEqual(first_params['scheme'], 'http://')
        self.assertFalse(first_params['ssl'])
        self.assertEqual(first_params['source'], 'example.com')

        self.assertEqual(second_params['targets'], expected_targets)
        self.assertEqual(second_params['host'], 'secure.example.com')
        self.assertEqual(second_params['scheme'], 'https://')
        self.assertTrue(second_params['ssl'])
        self.assertEqual(second_params['source'], 'https://secure.example.com')

        browser_first.ping.assert_called_once_with()
        browser_first.scan.assert_called_once_with()
        browser_first.done.assert_called_once_with()

        browser_second.ping.assert_called_once_with()
        browser_second.scan.assert_called_once_with()
        browser_second.done.assert_called_once_with()

    def test_prepare_remote_wordlist_downloads_into_managed_workspace(self):
        """Remote --wordlist should be resolved to a local runtime path before scanning."""

        workspace = MagicMock()
        workspace.get.return_value = '/tmp/opendoor-scan/remote-wordlist.tmp'
        result = MagicMock()
        result.path = '/tmp/opendoor-scan/remote-wordlist.tmp'
        result.bytes_downloaded = 12
        result.status = 200
        result.content_type = 'text/plain'
        downloader = MagicMock()
        downloader.download.return_value = result

        with patch('src.controller.ScanTempWorkspace', return_value=workspace), \
                patch('src.controller.RemoteWordlistDownloader', return_value=downloader), \
                patch('src.controller.tpl.info'):
            updated, returned_workspace = Controller._prepare_remote_wordlist({
                'scan': 'directories',
                'wordlist': 'https://example.test/list.txt',
                'timeout': 3,
            })

        self.assertIs(returned_workspace, workspace)
        workspace.get.assert_called_once_with('remote_wordlist')
        downloader.download.assert_called_once_with(
            'https://example.test/list.txt',
            '/tmp/opendoor-scan/remote-wordlist.tmp',
            timeout=3,
        )
        self.assertEqual(updated['wordlist'], 'https://example.test/list.txt')
        self.assertEqual(updated['wordlist_resolved_path'], '/tmp/opendoor-scan/remote-wordlist.tmp')
        self.assertEqual(updated['remote_wordlist_bytes'], 12)
        self.assertEqual(updated['remote_wordlist_status'], 200)
        self.assertEqual(updated['remote_wordlist_content_type'], 'text/plain')

    def test_prepare_remote_wordlist_logs_loaded_entry_count(self):
        """Remote --wordlist should log effective loaded entry count after download."""

        workspace = MagicMock()
        workspace.get.return_value = '/tmp/opendoor-scan/remote-wordlist.tmp'
        result = MagicMock()
        result.path = '/tmp/opendoor-scan/remote-wordlist.tmp'
        result.bytes_downloaded = 12
        result.status = 200
        result.content_type = 'text/plain'
        downloader = MagicMock()
        downloader.download.return_value = result

        with patch('src.controller.ScanTempWorkspace', return_value=workspace), \
                patch('src.controller.RemoteWordlistDownloader', return_value=downloader), \
                patch('src.controller.filesystem.count_lines', return_value=3), \
                patch('src.controller.tpl.info') as info_mock:
            Controller._prepare_remote_wordlist({
                'scan': 'directories',
                'wordlist': 'https://example.test/list.txt',
            })

        self.assertIn(
            unittest.mock.call(msg='Wordlist entries loaded: 3 (external)'),
            info_mock.call_args_list,
        )

    def test_prepare_remote_wordlist_debug_logs_are_debug_only(self):
        """Remote wordlist source/path diagnostics should only appear when debug is enabled."""

        workspace = MagicMock()
        workspace.get.return_value = '/tmp/opendoor-scan/remote-wordlist.tmp'
        result = MagicMock()
        result.path = '/tmp/opendoor-scan/remote-wordlist.tmp'
        result.bytes_downloaded = 12
        result.status = 200
        result.content_type = 'text/plain'
        downloader = MagicMock()
        downloader.download.return_value = result

        with patch('src.controller.ScanTempWorkspace', return_value=workspace), \
                patch('src.controller.RemoteWordlistDownloader', return_value=downloader) as downloader_cls, \
                patch('src.controller.tpl.debug') as debug_mock, \
                patch('src.controller.tpl.info') as info_mock:
            downloader_cls._format_bytes.return_value = '12B'
            Controller._prepare_remote_wordlist({
                'scan': 'directories',
                'wordlist': 'https://example.test/list.txt',
                'debug': 1,
            })

        messages = [call.kwargs.get('msg') for call in debug_mock.call_args_list]
        self.assertIn('Downloading remote wordlist: https://example.test/list.txt', messages)
        self.assertIn('Remote wordlist loaded: /tmp/opendoor-scan/remote-wordlist.tmp (12B)', messages)
        info_mock.assert_not_called()

    def test_prepare_remote_wordlist_skips_debug_logs_when_debug_disabled(self):
        """Remote wordlist diagnostics should not be printed as debug when debug=0."""

        workspace = MagicMock()
        workspace.get.return_value = '/tmp/opendoor-scan/remote-wordlist.tmp'
        result = MagicMock()
        result.path = '/tmp/opendoor-scan/remote-wordlist.tmp'
        result.bytes_downloaded = 12
        result.status = 200
        result.content_type = 'text/plain'
        downloader = MagicMock()
        downloader.download.return_value = result

        with patch('src.controller.ScanTempWorkspace', return_value=workspace), \
                patch('src.controller.RemoteWordlistDownloader', return_value=downloader), \
                patch('src.controller.tpl.debug') as debug_mock, \
                patch('src.controller.tpl.info') as info_mock:
            Controller._prepare_remote_wordlist({
                'scan': 'directories',
                'wordlist': 'https://example.test/list.txt',
                'debug': 0,
            })

        debug_mock.assert_not_called()
        info_mock.assert_not_called()

    def test_remote_wordlist_progress_renders_single_line_until_done(self):
        """Remote wordlist progress should rotate in-place and persist only the final info row."""

        Controller._remote_wordlist_progress_active = False
        Controller._remote_wordlist_progress_last_length = 0

        with patch('src.controller.output.writels') as writels_mock, \
                patch('src.controller.output.mark_dynamic_line') as mark_mock, \
                patch('src.controller.output.clear_dynamic_line') as clear_mock, \
                patch('src.controller.tpl.info') as info_mock, \
                patch('sys.stdout') as stdout_mock:
            Controller._remote_wordlist_progress(50, total_bytes=100, done=False)
            Controller._remote_wordlist_progress(100, total_bytes=100, done=True)

        writels_mock.assert_called_once()
        rendered = writels_mock.call_args.args[0]
        self.assertIn('info:', rendered)
        self.assertIn('Wordlist download [############------------] 50.0% 50B/100B', rendered)
        mark_mock.assert_called_once_with(len(rendered))
        stdout_mock.write.assert_called_once_with('\r{0}\r'.format(' ' * len(rendered)))
        clear_mock.assert_called_once_with()
        info_mock.assert_called_once_with(msg='Wordlist download [########################] 100.0% 100B/100B done')

    def test_prepare_remote_wordlist_cleans_workspace_on_download_error(self):
        """Failed remote downloads should not leave the managed workspace behind."""

        workspace = MagicMock()
        workspace.get.return_value = '/tmp/opendoor-scan/remote-wordlist.tmp'
        downloader = MagicMock()
        downloader.download.side_effect = RemoteWordlistError('too large')

        with patch('src.controller.ScanTempWorkspace', return_value=workspace), \
                patch('src.controller.RemoteWordlistDownloader', return_value=downloader), \
                patch('src.controller.tpl.info'):
            with self.assertRaises(BrowserError):
                Controller._prepare_remote_wordlist({
                    'scan': 'directories',
                    'wordlist': 'https://example.test/huge.txt',
                })

        workspace.cleanup.assert_called_once_with()

    def test_prepare_remote_wordlist_skips_local_wordlist(self):
        """Local wordlists should not allocate remote download workspace."""

        params = {'scan': 'directories', 'wordlist': '/tmp/local.txt'}

        with patch('src.controller.ScanTempWorkspace') as workspace_mock:
            updated, workspace = Controller._prepare_remote_wordlist(params)

        self.assertIs(updated, params)
        self.assertIsNone(workspace)
        workspace_mock.assert_not_called()

    def test_scan_action_prints_banner_before_remote_wordlist_resolution(self):
        """Scan banner should be printed before remote wordlist download progress."""

        events = []
        browser_instance = MagicMock()
        resolved = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'txt',
            'wordlist': 'https://example.test/list.txt',
            'wordlist_resolved_path': '/tmp/opendoor-scan/remote-wordlist.tmp',
        }
        params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'txt',
            'wordlist': 'https://example.test/list.txt',
        }

        def render_banner(received):
            events.append(('banner', dict(received)))
            return 'banner'

        def prepare_wordlist(received):
            events.append(('prepare', dict(received)))
            return resolved, None

        with patch.object(Controller, '_prepare_remote_wordlist', side_effect=prepare_wordlist) as prepare_mock, \
                patch('src.controller.package.banner', side_effect=render_banner) as banner_mock, \
                patch('src.controller.tpl.message') as message_mock, \
                patch('src.controller.browser', return_value=browser_instance), \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action(params, show_banner=True)

        prepare_mock.assert_called_once()
        banner_mock.assert_called_once_with(params)
        message_mock.assert_called_once_with('banner')
        self.assertEqual([name for name, _payload in events], ['banner', 'prepare'])
        browser_instance.scan.assert_called_once_with()

    def test_prepare_remote_wordlist_skips_already_resolved_remote_wordlist(self):
        """Already resolved remote wordlists should not allocate a second workspace."""

        params = {
            'scan': 'directories',
            'wordlist': 'https://example.test/list.txt',
            'wordlist_resolved_path': '/tmp/opendoor-scan/remote-wordlist.tmp',
        }

        with patch('src.controller.ScanTempWorkspace') as workspace_mock:
            updated, workspace = Controller._prepare_remote_wordlist(params)

        self.assertIs(updated, params)
        self.assertIsNone(workspace)
        workspace_mock.assert_not_called()

    def test_cleanup_remote_wordlist_workspace_ignores_missing_workspace(self):
        """Cleanup helper should be a no-op when no remote workspace exists."""

        Controller._cleanup_remote_wordlist_workspace(None)

    def test_cleanup_remote_wordlist_workspace_delegates_to_workspace(self):
        """Cleanup helper should remove remote wordlist workspace after scan."""

        workspace = MagicMock()

        Controller._cleanup_remote_wordlist_workspace(workspace)

        workspace.cleanup.assert_called_once_with()

    def test_scan_action_cleans_remote_wordlist_workspace_on_keyboard_interrupt(self):
        """Controller.scan_action() should cleanup downloaded wordlists after abort."""

        workspace = MagicMock()
        transport = MagicMock()
        transport.rotate_mode = 'none'
        params = {
            'host': 'example.com',
            'scheme': 'http://',
            'reports': 'std',
            'wordlist': 'https://example.test/list.txt',
        }
        resolved = dict(params, wordlist_resolved_path='/tmp/opendoor-scan/list.tmp')

        with patch.object(Controller, '_prepare_remote_wordlist', return_value=(resolved, workspace)), \
                patch.object(Controller, '_resolve_scan_targets', return_value=[{'host': 'example.com'}]), \
                patch.object(Controller, '_scan_target', side_effect=KeyboardInterrupt()), \
                patch('src.controller.NetworkTransportManager', return_value=transport), \
                patch('src.controller.tpl.cancel') as cancel_mock:
            exit_code = Controller.scan_action(params)

        self.assertEqual(exit_code, 0)
        transport.start.assert_called_once_with()
        transport.stop.assert_called_once_with()
        workspace.cleanup.assert_called_once_with()
        cancel_mock.assert_called_once_with(key='abort')


    def test_remote_wordlist_progress_handles_invalid_values_without_total(self):
        """Progress renderer should tolerate defensive invalid values and unknown totals."""

        Controller._remote_wordlist_progress_active = False
        Controller._remote_wordlist_progress_last_length = 0

        with patch('src.controller.output.writels') as writels_mock, \
                patch('src.controller.output.mark_dynamic_line') as mark_mock:
            Controller._remote_wordlist_progress('bad', total_bytes='bad', done=False)

        rendered = writels_mock.call_args.args[0]
        self.assertIn('Wordlist download 0B', rendered)
        mark_mock.assert_called_once_with(len(rendered))

    def test_clear_remote_wordlist_progress_line_ignores_inactive_state(self):
        """Clearing progress should not touch stdout when no dynamic row is active."""

        Controller._remote_wordlist_progress_active = False
        Controller._remote_wordlist_progress_last_length = 10

        with patch('sys.stdout') as stdout_mock:
            Controller._clear_remote_wordlist_progress_line()

        stdout_mock.write.assert_not_called()

    def test_clear_remote_wordlist_progress_line_tolerates_stdout_errors(self):
        """Stdout cleanup errors should not break remote wordlist resolution."""

        Controller._remote_wordlist_progress_active = True
        Controller._remote_wordlist_progress_last_length = 10

        with patch('sys.stdout') as stdout_mock:
            stdout_mock.write.side_effect = ValueError('closed')
            Controller._clear_remote_wordlist_progress_line()

        self.assertFalse(Controller._remote_wordlist_progress_active)
        self.assertEqual(Controller._remote_wordlist_progress_last_length, 0)

    def test_clear_remote_wordlist_progress_line_resets_active_row_without_last_length(self):
        """Progress cleanup should reset state even when there is no recorded line length."""

        Controller._remote_wordlist_progress_active = True
        Controller._remote_wordlist_progress_last_length = 0

        with patch('sys.stdout') as stdout_mock:
            Controller._clear_remote_wordlist_progress_line()

        stdout_mock.write.assert_not_called()
        self.assertFalse(Controller._remote_wordlist_progress_active)
        self.assertEqual(Controller._remote_wordlist_progress_last_length, 0)

    def test_remote_wordlist_progress_done_without_active_row(self):
        """Final progress row should still be printed when no transient row was active."""

        Controller._remote_wordlist_progress_active = False
        Controller._remote_wordlist_progress_last_length = 0

        with patch('src.controller.output.clear_dynamic_line') as clear_mock, \
                patch('src.controller.tpl.info') as info_mock:
            Controller._remote_wordlist_progress(5, total_bytes=None, done=True)

        clear_mock.assert_called_once_with()
        info_mock.assert_called_once_with(msg='Wordlist download 5B done')
    def test_scan_action_should_preserve_delay_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve explicit --delay overrides for wizard flow."""

        browser_instance = MagicMock()
        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'reports': 'std',
            'delay': 2.0,
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'delay': 0.1,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['delay'], 0.1)

    def test_scan_action_should_preserve_delay_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit --delay overrides for session resume."""

        browser_instance = MagicMock()
        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'delay': 2.0,
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'delay': 0.0,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['delay'], 0.0)

    def test_scan_action_should_preserve_port_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve explicit --port overrides for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'port': 80,
            'reports': 'std',
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'port': 8443,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['port'], 8443)

    def test_scan_action_should_preserve_port_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit --port overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'port': 8443,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['port'], 8443)

    def test_scan_action_should_preserve_method_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve explicit --method overrides for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'port': 80,
            'method': 'HEAD',
            'reports': 'std',
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'method': 'GET',
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['method'], 'GET')

    def test_scan_action_should_preserve_method_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit --method overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'method': 'HEAD',
                'reports': 'std',
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'method': 'OPTIONS',
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['method'], 'OPTIONS')


    def test_scan_action_should_preserve_crawl_cli_override_for_wizard(self):
        """Controller.scan_action() should preserve explicit --crawl overrides for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'port': 80,
            'reports': 'std',
            'crawl': False,
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'crawl': True,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['crawl'])

    def test_scan_action_should_preserve_crawl_cli_override_for_session_load(self):
        """Controller.scan_action() should preserve explicit --crawl overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'crawl': False,
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'crawl': True,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['crawl'])

    def test_scan_action_should_preserve_tls_legacy_cli_override_for_wizard(self):
        """Controller.scan_action() should preserve explicit --tls-legacy override for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        wizard_params = {
            'host': 'example.com',
            'scheme': 'https://',
            'ssl': True,
            'port': 443,
            'reports': 'std',
            'tls_legacy': False,
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'tls_legacy': True,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['tls_legacy'])

    def test_scan_action_should_preserve_threads_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve explicit --threads overrides for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'port': 80,
            'threads': 12,
            'reports': 'std',
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'threads': 4,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['threads'], 4)

    def test_scan_action_should_preserve_threads_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit --threads overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'threads': 12,
                'reports': 'std',
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'threads': 6,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['threads'], 6)


    def test_scan_action_should_preserve_report_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve explicit report CLI overrides for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'port': 80,
            'reports': 'html',
            'reports_dir': '/wizard/reports',
        }

        with patch('src.controller.package.wizard', return_value=wizard_params),                 patch('src.controller.browser', return_value=browser_instance) as browser_mock,                 patch('src.controller.reporter.is_reported', return_value=False),                 patch('src.controller.tpl.info'),                 patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'reports': 'csv,json',
                'reports_dir': '/cli/reports',
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['reports'], 'csv,json')
        self.assertEqual(passed_params['reports_dir'], '/cli/reports')

    def test_scan_action_should_preserve_report_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit report CLI overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'html',
                'reports_dir': '/session/reports',
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot),                 patch('src.controller.browser', return_value=browser_instance) as browser_mock,                 patch('src.controller.reporter.is_reported', return_value=False),                 patch('src.controller.tpl.info'),                 patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'reports': 'sqlite,sarif',
                'reports_dir': '/cli/reports',
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertEqual(passed_params['reports'], 'sqlite,sarif')
        self.assertEqual(passed_params['reports_dir'], '/cli/reports')

    def test_scan_action_should_preserve_recursive_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve explicit recursive CLI overrides for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'port': 80,
            'reports': 'std',
            'recursive': False,
            'recursive_depth': 1,
            'recursive_status': ['200'],
            'recursive_exclude': ['jpg'],
        }

        with patch('src.controller.package.wizard', return_value=wizard_params),                 patch('src.controller.browser', return_value=browser_instance) as browser_mock,                 patch('src.controller.reporter.is_reported', return_value=False),                 patch('src.controller.tpl.info'),                 patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'recursive': True,
                'recursive_depth': 3,
                'recursive_status': ['200', '403'],
                'recursive_exclude': ['png', 'css'],
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['recursive'])
        self.assertEqual(passed_params['recursive_depth'], 3)
        self.assertEqual(passed_params['recursive_status'], ['200', '403'])
        self.assertEqual(passed_params['recursive_exclude'], ['png', 'css'])

    def test_scan_action_should_preserve_recursive_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit recursive CLI overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'recursive': False,
                'recursive_depth': 1,
                'recursive_status': ['200'],
                'recursive_exclude': ['jpg'],
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot),                 patch('src.controller.browser', return_value=browser_instance) as browser_mock,                 patch('src.controller.reporter.is_reported', return_value=False),                 patch('src.controller.tpl.info'),                 patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'recursive': True,
                'recursive_depth': 2,
                'recursive_status': ['301', '302'],
                'recursive_exclude': ['gif'],
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['recursive'])
        self.assertEqual(passed_params['recursive_depth'], 2)
        self.assertEqual(passed_params['recursive_status'], ['301', '302'])
        self.assertEqual(passed_params['recursive_exclude'], ['gif'])



    def test_scan_action_should_preserve_fingerprint_cli_override_for_wizard(self):
        """Controller.scan_action() should preserve explicit --fingerprint for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'port': 80,
            'reports': 'std',
            'fingerprint': False,
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'fingerprint': True,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['fingerprint'])

    def test_scan_action_should_preserve_fingerprint_cli_override_for_session_load(self):
        """Controller.scan_action() should preserve explicit --fingerprint for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'fingerprint': False,
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'fingerprint': True,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['fingerprint'])


    def test_scan_action_should_preserve_waf_cli_overrides_for_wizard(self):
        """Controller.scan_action() should preserve explicit WAF CLI overrides for wizard flow."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        wizard_params = {
            'host': 'example.com',
            'scheme': 'http://',
            'ssl': False,
            'port': 80,
            'reports': 'std',
            'waf_detect': False,
            'waf_safe_mode': False,
            'waf_guard': False,
        }

        with patch('src.controller.package.wizard', return_value=wizard_params), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'wizard': 'opendoor.conf',
                'waf_safe_mode': True,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['waf_safe_mode'])
        self.assertTrue(passed_params['waf_detect'])
        self.assertFalse(passed_params['waf_guard'])

    def test_scan_action_should_preserve_waf_cli_overrides_for_session_load(self):
        """Controller.scan_action() should preserve explicit WAF CLI overrides for session resume."""

        browser_instance = MagicMock()
        browser_instance.result = {'total': {'success': 0}}
        snapshot = {
            'params': {
                'host': 'example.com',
                'scheme': 'http://',
                'ssl': False,
                'port': 80,
                'reports': 'std',
                'waf_detect': False,
                'waf_safe_mode': False,
                'waf_guard': False,
            }
        }

        with patch('src.controller.SessionManager.load', return_value=snapshot), \
                patch('src.controller.browser', return_value=browser_instance) as browser_mock, \
                patch('src.controller.reporter.is_reported', return_value=False), \
                patch('src.controller.tpl.info'), \
                patch('src.controller.reporter.default', 'std'):
            Controller.scan_action({
                'session_load': '/tmp/session.json',
                'waf_guard': True,
            })

        browser_mock.assert_called_once()
        passed_params = browser_mock.call_args[0][0]
        self.assertTrue(passed_params['waf_guard'])
        self.assertTrue(passed_params['waf_detect'])
        self.assertFalse(passed_params['waf_safe_mode'])


if __name__ == '__main__':
    unittest.main()
