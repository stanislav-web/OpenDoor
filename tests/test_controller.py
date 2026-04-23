# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch

from src import Controller, SrcError
from src.core.logger.logger import Logger
from src.lib import ArgumentsError, BrowserError, PackageError, ReporterError


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

if __name__ == '__main__':
    unittest.main()
