# -*- coding: utf-8 -*-

import os
import io
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src import Controller, SrcError
from src.core.logger.logger import Logger
from src.lib import ArgumentsError, BrowserError, PackageError, ReporterError
from src.core.network.exceptions import NetworkTransportError
from src.lib.diff import DiffValidationError


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

        with patch('src.controller.package.banner', return_value='banner'), \
                patch('src.controller.tpl.message') as message_mock, \
                patch.object(Controller, 'scan_action') as scan_mock, \
                patch('src.controller.tpl.debug'):
            controller.run()

        message_mock.assert_called_once_with('banner')
        scan_mock.assert_called_once_with({'host': 'http://example.com'})

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

        scan_mock.assert_called_once_with(controller.ioargs)

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
                patch.object(Controller, 'scan_action', return_value=1), \
                patch('src.controller.tpl.debug'):
            actual = controller.run()

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

if __name__ == '__main__':
    unittest.main()
