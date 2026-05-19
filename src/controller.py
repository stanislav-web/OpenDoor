# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development: Stanislav WEB
"""

import json
import os

from src.core.decorators import execution_time
from src.lib import ArgumentsError
from src.lib import BrowserError
from src.lib import PackageError
from src.lib import ReporterError
from src.lib import TplError
from src.lib import args
from src.lib import browser
from src.lib import events
from src.lib import package
from src.lib import reporter
from src.lib import tpl
from src.lib.browser.workspace import ScanTempWorkspace
from src.lib.reader import RemoteWordlistDownloader, RemoteWordlistError, WordlistSource
from src.lib.diff import DiffReportComparator, DiffReportReader, DiffResultSerializer, DiffStdoutFormatter, DiffValidationError
from src.lib.browser.session import SessionManager, SessionError
from src.core.network import NetworkTransportManager, NetworkTransportError
from src.core import FileSystemError
from src.core import filesystem
from src.core import helper
from src.core import sys as output
from .exceptions import SrcError


class Controller(object):

    """Controller class"""

    def __init__(self):
        """
        Init constructor
        :raise SrcError
        """

        events.terminate()

        try:
            interpreter = package.check_interpreter()

            if interpreter is not True:
                raise SrcError(
                    tpl.error(
                        key='unsupported',
                        actual=interpreter.get('actual'),
                        expected=interpreter.get('expected')
                    )
                )
            else:
                self.ioargs = args().get_arguments()
        except ArgumentsError as error:
            raise SrcError(tpl.error(error))

    @execution_time(log=tpl)
    def run(self):
        """
        Bootstrap action
        :raise SrcError
        :return: int
        """

        try:
            if True is self.ioargs.get('update'):
                getattr(self, 'update_action')()
                return 0

            if 'host' in self.ioargs or 'targets' in self.ioargs or 'wizard' in self.ioargs or 'session_load' in self.ioargs:
                return getattr(self, 'scan_action')(self.ioargs, show_banner=True) or 0

            tpl.message(package.banner(self.ioargs))

            if 'diff' in self.ioargs:
                return getattr(self, 'diff_action')(self.ioargs) or 0

            for action in self.ioargs.keys():
                if hasattr(self, '{0}_action'.format(action)) \
                        and args().is_arg_callable(getattr(self, '{0}_action'.format(action))):
                    getattr(self, '{func}_action'.format(func=action))()
                    return 0

            return 0

        except (SrcError, PackageError, BrowserError, AttributeError) as error:
            raise SrcError(tpl.error(error))

    @classmethod
    def diff_action(cls, params):
        """
        Compare two OpenDoor reports without running a scan.

        :param dict params: console input args
        :raise SrcError:
        :return: int
        """

        try:
            previous, current = DiffReportReader().read_pair(params.get('diff'))
            result = DiffReportComparator().compare(previous, current)
            tpl.message(DiffStdoutFormatter().format(result))

            if cls._diff_should_write_json(params):
                output_path = cls._write_diff_json(params, result)
                tpl.info(msg='JsonDiffReport : {0}'.format(output_path))

            return 0
        except (DiffValidationError, OSError, TypeError, ValueError) as error:
            raise SrcError(error)

    @staticmethod
    def _diff_should_write_json(params):
        """
        Check whether diff JSON output was requested.

        :param dict params:
        :return: bool
        """

        reports = params.get('reports') or 'std'
        return 'json' in [item.strip().lower() for item in str(reports).split(',')]

    @staticmethod
    def _diff_reports_dir(params):
        """
        Resolve diff output directory.

        :param dict params:
        :return: str
        """

        reports_dir = params.get('reports_dir')
        if isinstance(reports_dir, list):
            reports_dir = reports_dir[0] if reports_dir else None

        if reports_dir is None:
            reports_dir = os.getcwd()

        return os.path.abspath(str(reports_dir))

    @classmethod
    def _write_diff_json(cls, params, result):
        """
        Write deterministic JSON diff output.

        :param dict params:
        :param DiffResult result:
        :raise OSError:
        :return: str
        """

        output_dir = cls._diff_reports_dir(params)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'opendoor-diff.json')

        with open(output_path, 'w', encoding='utf-8') as handler:
            json.dump(DiffResultSerializer().serialize(result), handler, indent=2, sort_keys=True)
            handler.write('\n')

        return output_path

    @staticmethod
    def examples_action():
        """
        Show examples action
        :return: None
        """

        tpl.message(package.examples())

    @staticmethod
    def update_action():
        """
        App update action
        :raise SrcError
        :return: None
        """

        try:
            tpl.message(package.update())
        except (AttributeError, PackageError) as error:
            raise SrcError(error)

    @staticmethod
    def docs_action():
        """
        Displays the user guide for the app.

        :raises SrcError: If there is an error with the package or attribute.
        :return: None
        """

        try:
            package.docs()
        except (AttributeError, PackageError) as error:
            raise SrcError(error)

    @staticmethod
    def version_action():
        """
        Show app version action

        :raise SrcError
        :return: None
        """

        try:
            tpl.message(package.version())
        except (AttributeError, PackageError) as error:
            raise SrcError(error)

    @staticmethod
    def local_version():
        """
        Returns the local version of the app.

        :raises SrcError: If there is an error retrieving the local version.
        :return: None
        """

        try:
            tpl.message(package.local_version())
        except (AttributeError, PackageError) as error:
            raise SrcError(error)

    @classmethod
    def scan_action(cls, params, show_banner=False):
        """
        URL scan action
        :param dict params: console input args
        :param bool show_banner: print banner after runtime scan inputs are resolved
        :raise SrcError
        :return: int
        """

        remote_workspace = None

        try:
            cli_fail_on_bucket = params.get('fail_on_bucket')
            cli_auto_calibrate = params.get('auto_calibrate')
            cli_calibration_samples = params.get('calibration_samples')
            cli_calibration_threshold = params.get('calibration_threshold')
            cli_response_filter_overrides = cls._collect_response_filter_cli_overrides(params)
            cli_transport_overrides = cls._collect_transport_cli_overrides(params)
            cli_proxy_overrides = cls._collect_proxy_cli_overrides(params)
            cli_header_overrides = cls._collect_header_cli_overrides(params)
            cli_recursive_overrides = cls._collect_recursive_cli_overrides(params)
            cli_delay = params.get('delay')
            cli_port = params.get('port')
            cli_method = params.get('method')
            cli_tls_legacy = params.get('tls_legacy')

            if 'wizard' in params:
                tpl.info(key='load_wizard', config=params['wizard'])
                params = package.wizard(params['wizard'])

                if cli_fail_on_bucket is not None:
                    params['fail_on_bucket'] = cli_fail_on_bucket

                if cli_auto_calibrate is not None:
                    params['auto_calibrate'] = cli_auto_calibrate

                if cli_calibration_samples is not None:
                    params['calibration_samples'] = cli_calibration_samples

                if cli_calibration_threshold is not None:
                    params['calibration_threshold'] = cli_calibration_threshold

                if cli_delay is not None:
                    params['delay'] = cli_delay

                if cli_port is not None:
                    params['port'] = cli_port

                if cli_method is not None:
                    params['method'] = cli_method

                if cli_tls_legacy is True:
                    params['tls_legacy'] = True

                params.update(cli_response_filter_overrides)
                params.update(cli_transport_overrides)
                params.update(cli_proxy_overrides)
                params.update(cli_header_overrides)
                params.update(cli_recursive_overrides)

            if params.get('session_load'):
                snapshot = SessionManager.load(params.get('session_load'))
                restored = dict(snapshot.get('params') or {})
                restored['session_snapshot'] = snapshot
                restored['session_save'] = params.get('session_load')

                if params.get('session_autosave_sec') is not None:
                    restored['session_autosave_sec'] = params.get('session_autosave_sec')

                if params.get('session_autosave_items') is not None:
                    restored['session_autosave_items'] = params.get('session_autosave_items')

                if cli_fail_on_bucket is not None:
                    restored['fail_on_bucket'] = cli_fail_on_bucket

                if cli_auto_calibrate is not None:
                    restored['auto_calibrate'] = cli_auto_calibrate

                if cli_calibration_samples is not None:
                    restored['calibration_samples'] = cli_calibration_samples

                if cli_calibration_threshold is not None:
                    restored['calibration_threshold'] = cli_calibration_threshold

                if cli_delay is not None:
                    restored['delay'] = cli_delay

                if cli_port is not None:
                    restored['port'] = cli_port

                if cli_method is not None:
                    restored['method'] = cli_method

                if cli_tls_legacy is True:
                    restored['tls_legacy'] = True

                restored.update(cli_response_filter_overrides)
                restored.update(cli_transport_overrides)
                restored.update(cli_proxy_overrides)
                restored.update(cli_header_overrides)
                restored.update(cli_recursive_overrides)

                params = restored
                tpl.info(msg='Loaded session checkpoint from {0}'.format(
                    snapshot.get('_loaded_from', restored['session_save'])))

            if show_banner is True:
                tpl.message(package.banner(params))

            params, remote_workspace = cls._prepare_remote_wordlist(params)

            targets = cls._resolve_scan_targets(params)

            if params.get('session_save') and len(targets) > 1:
                raise BrowserError(Exception('Persistent sessions currently support one target per run'))

            fail_on_buckets = params.get('fail_on_bucket') or []
            ci_mode_enabled = len(fail_on_buckets) > 0
            fail_on_matches = []

            if ci_mode_enabled is True:
                tpl.info(msg='CI/CD mode enabled: fail-on-bucket={0}'.format(','.join(fail_on_buckets)))

            if reporter.default == params.get('reports'):
                tpl.info(key='use_reports')

            transport = NetworkTransportManager(params)

            target_failures = []

            if transport.rotate_mode == 'per-target':
                for target in targets:
                    target_params = dict(params)
                    target_params.update(target)

                    transport.rotate()
                    cls._log_transport_start(transport)
                    cls._debug_transport(params, transport, 'starting')

                    transport_started = False
                    try:
                        transport.start()
                        transport_started = True
                        cls._debug_transport(params, transport, 'started')

                        scan_result = cls._scan_target(target_params)

                        if ci_mode_enabled is True:
                            fail_on_matches.extend(
                                cls._match_fail_on_buckets(
                                    target_params.get('host'),
                                    scan_result,
                                    fail_on_buckets
                                )
                            )
                    except (AttributeError, BrowserError, ReporterError, TplError, NetworkTransportError) as error:
                        if len(targets) <= 1:
                            raise
                        target_failures.append(cls._record_target_failure(target_params, error))
                    finally:
                        if transport_started is True:
                            cls._debug_transport(params, transport, 'stopping')
                            transport.stop()
                            cls._log_transport_stop(transport)
                            cls._debug_transport(params, transport, 'stopped')

            else:
                cls._log_transport_start(transport)
                cls._debug_transport(params, transport, 'starting')

                transport_started = False
                try:
                    transport.start()
                    transport_started = True
                    cls._debug_transport(params, transport, 'started')

                    for target in targets:
                        target_params = dict(params)
                        target_params.update(target)

                        try:
                            scan_result = cls._scan_target(target_params)
                        except (AttributeError, BrowserError, ReporterError, TplError, NetworkTransportError) as error:
                            if len(targets) <= 1:
                                raise
                            target_failures.append(cls._record_target_failure(target_params, error))
                            continue

                        if ci_mode_enabled is True:
                            fail_on_matches.extend(
                                cls._match_fail_on_buckets(
                                    target_params.get('host'),
                                    scan_result,
                                    fail_on_buckets
                                )
                            )
                finally:
                    if transport_started is True:
                        cls._debug_transport(params, transport, 'stopping')
                        transport.stop()
                        cls._log_transport_stop(transport)
                        cls._debug_transport(params, transport, 'stopped')

            if ci_mode_enabled is True:
                if len(fail_on_matches) > 0:
                    tpl.warning(
                        msg='CI/CD fail-on matched: {0}. Exit code: 1'.format(
                            cls._format_fail_on_matches(fail_on_matches)
                        )
                    )
                    return 1

                tpl.info(msg='CI/CD fail-on passed: no matched buckets. Exit code: 0')

            if len(target_failures) > 0:
                tpl.warning(msg='Completed with target errors: {0}. Exit code: 1'.format(
                    cls._format_target_failures(target_failures)
                ))
                return 1

            return 0

        except (AttributeError, BrowserError, ReporterError, TplError, SessionError, NetworkTransportError) as error:
            raise SrcError(error)
        except (KeyboardInterrupt, SystemExit):
            tpl.cancel(key='abort')
            return 0
        finally:
            cls._cleanup_remote_wordlist_workspace(remote_workspace)

    @classmethod
    def _prepare_remote_wordlist(cls, params):
        """Download remote HTTP(S) wordlist into a managed local file.

        The original ``wordlist`` value is preserved for session/reproducibility.
        The scan engine reads ``wordlist_resolved_path`` like any other local
        external wordlist.

        :param dict params: Effective scan params after wizard/session resolution.
        :raise BrowserError: When the remote source cannot be resolved safely.
        :return: Updated params and optional workspace.
        :rtype: tuple[dict, ScanTempWorkspace | None]
        """

        source = WordlistSource.from_value(
            params.get('wordlist'),
            resolved_value=params.get('wordlist_resolved_path') or params.get('resolved_wordlist'),
        )

        if source.is_remote is not True:
            return params, None

        if source.runtime_path is not None:
            return params, None

        workspace = ScanTempWorkspace()
        output_path = workspace.get('remote_wordlist')
        downloader = RemoteWordlistDownloader(progress_callback=cls._remote_wordlist_progress)

        try:
            if cls._is_debug_enabled(params):
                tpl.debug(msg='Downloading remote wordlist: {0}'.format(source.value))
            result = downloader.download(source.value, output_path, timeout=params.get('timeout'))
            updated = dict(params)
            updated['wordlist_resolved_path'] = result.path
            updated['remote_wordlist_bytes'] = result.bytes_downloaded
            updated['remote_wordlist_status'] = result.status
            updated['remote_wordlist_content_type'] = result.content_type
            cls._log_remote_wordlist_loaded(result.path)
            if cls._is_debug_enabled(params):
                tpl.debug(
                    msg='Remote wordlist loaded: {0} ({1})'.format(
                        result.path,
                        RemoteWordlistDownloader._format_bytes(result.bytes_downloaded),
                    )
                )
            return updated, workspace
        except RemoteWordlistError as error:
            workspace.cleanup()
            raise BrowserError(error)

    @classmethod
    def _log_remote_wordlist_loaded(cls, path):
        """Log the effective remote wordlist entry count after download.

        :param str path: Downloaded runtime wordlist path.
        :return: None
        """

        try:
            entries = filesystem.count_lines(path)
        except (FileSystemError, OSError, TypeError, ValueError):
            return

        tpl.info(msg='Wordlist entries loaded: {0} (external)'.format(entries))

    @classmethod
    def _cleanup_remote_wordlist_workspace(cls, workspace):
        """Cleanup remote wordlist temporary workspace.

        :param ScanTempWorkspace | None workspace: Workspace to cleanup.
        :return: None
        """

        if workspace is None:
            return

        workspace.cleanup()

    @classmethod
    def _remote_wordlist_progress(cls, downloaded, total_bytes=None, done=False):
        """Render remote wordlist download progress as a dynamic CLI row.

        :param int downloaded: Downloaded bytes.
        :param int | None total_bytes: Total bytes if known.
        :param bool done: Whether download has finished.
        :return: None
        """

        try:
            downloaded = int(downloaded or 0)
        except (TypeError, ValueError):
            downloaded = 0

        try:
            total = int(total_bytes or 0)
        except (TypeError, ValueError):
            total = 0

        if total > 0:
            bar = cls._render_progress_bar(downloaded, total)
            message = 'Wordlist download {0} {1}/{2}'.format(
                bar,
                RemoteWordlistDownloader._format_bytes(downloaded),
                RemoteWordlistDownloader._format_bytes(total),
            )
        else:
            message = 'Wordlist download {0}'.format(
                RemoteWordlistDownloader._format_bytes(downloaded)
            )

        if done is True:
            cls._clear_remote_wordlist_progress_line()
            output.clear_dynamic_line()
            tpl.info(msg=message + ' done')
            return

        rendered = cls._format_dynamic_info(message)
        output.writels(rendered)
        output.mark_dynamic_line(len(rendered))
        cls._remote_wordlist_progress_active = True
        cls._remote_wordlist_progress_last_length = len(rendered)

    @classmethod
    def _clear_remote_wordlist_progress_line(cls):
        """Clear the transient remote-wordlist progress row before final output.

        :return: None
        """

        import sys

        if getattr(cls, '_remote_wordlist_progress_active', False) is not True:
            return

        last_length = getattr(cls, '_remote_wordlist_progress_last_length', 0)
        if last_length > 0:
            try:
                sys.stdout.write('\r{0}\r'.format(' ' * last_length))
                sys.stdout.flush()
            except (AttributeError, OSError, ValueError):
                pass

        cls._remote_wordlist_progress_active = False
        cls._remote_wordlist_progress_last_length = 0

    @staticmethod
    def _render_progress_bar(current, total, width=24):
        """Render a simple ASCII progress bar.

        :param int current: Current byte count.
        :param int total: Total byte count.
        :param int width: Bar width.
        :return: Progress bar.
        :rtype: str
        """

        safe_total = max(int(total or 1), 1)
        safe_current = min(max(int(current or 0), 0), safe_total)
        filled = int(round(width * safe_current / float(safe_total)))
        empty = max(width - filled, 0)
        return '[{0}{1}] {2}'.format('#' * filled, '-' * empty, helper.percent(safe_current, safe_total))

    @staticmethod
    def _format_dynamic_info(message):
        """Format a dynamic info line like regular logger output.

        :param str message: Message body.
        :return: Rendered row.
        :rtype: str
        """

        from datetime import datetime

        return '[{0}] info:    {1}'.format(datetime.now().strftime('%H:%M:%S'), message)

    @classmethod
    def _scan_target(cls, target_params):
        """
        Run scan flow for one resolved target.

        :param dict target_params:
        :raise BrowserError:
        :return: dict
        """

        brows = browser(target_params)

        try:
            if True is reporter.is_reported(target_params.get('host')):
                try:
                    tpl.prompt(key='logged')
                except KeyboardInterrupt:
                    tpl.cancel(key='abort')

            brows.ping()

            if target_params.get('fingerprint') is True:
                brows.fingerprint()

            if target_params.get('auto_calibrate') is True:
                brows.calibrate()

            brows.scan()
            brows.done()

            return brows.result
        finally:
            close = getattr(brows, 'close', None)
            if callable(close):
                close()

    @staticmethod
    def _collect_response_filter_cli_overrides(params):
        """Collect explicit response-filter options for wizard/session overrides.

        Session and wizard params restore a previous scan configuration. When a
        user passes response filters together with --session-load or --wizard,
        those explicit CLI values must override restored filters the same way
        CI, calibration and transport overrides do.

        :param dict params: filtered CLI params
        :return: dict
        """

        override_keys = (
            'include_status',
            'exclude_status',
            'exclude_size',
            'exclude_size_range',
            'match_text',
            'exclude_text',
            'match_regex',
            'exclude_regex',
            'min_response_length',
            'max_response_length',
        )

        return {
            key: params.get(key)
            for key in override_keys
            if params.get(key) is not None
        }

    @staticmethod
    def _collect_transport_cli_overrides(params):
        """
        Collect explicit transport options that should override wizard/session params.

        Defaults inserted by option filtering must not accidentally override
        transport settings restored from wizard or session configuration.

        :param dict params:
        :return: dict
        """

        overrides = {}

        transport = params.get('transport')
        if transport in ['proxy', 'openvpn', 'wireguard']:
            overrides['transport'] = transport

        if params.get('transport_profile') is not None:
            overrides['transport_profile'] = params.get('transport_profile')

        if params.get('transport_profiles') is not None:
            overrides['transport_profiles'] = params.get('transport_profiles')

        if params.get('transport_timeout') is not None:
            overrides['transport_timeout'] = params.get('transport_timeout')

        if params.get('transport_healthcheck_url') is not None:
            overrides['transport_healthcheck_url'] = params.get('transport_healthcheck_url')

        if params.get('transport_bin') is not None:
            overrides['transport_bin'] = params.get('transport_bin')

        if params.get('openvpn_auth') is not None:
            overrides['openvpn_auth'] = params.get('openvpn_auth')

        if params.get('transport_rotate') is not None:
            if params.get('transport_rotate') != 'none' \
                    or overrides.get('transport') in ['proxy', 'openvpn', 'wireguard'] \
                    or overrides.get('transport_profiles') is not None:
                overrides['transport_rotate'] = params.get('transport_rotate')

        return overrides

    @staticmethod
    def _collect_header_cli_overrides(params):
        """Collect explicit request-header options for wizard/session overrides.

        :param dict params: filtered CLI params
        :return: dict
        """

        if params.get('header') is None:
            return {}

        return {'header': params.get('header')}

    @staticmethod
    def _collect_recursive_cli_overrides(params):
        """Collect explicit recursive scan options for wizard/session overrides.

        Parser defaults must not replace wizard/session recursive settings, but
        explicit recursive CLI values should override restored scan settings.

        :param dict params: filtered CLI params
        :return: dict
        """

        override_keys = (
            'recursive',
            'recursive_depth',
            'recursive_status',
            'recursive_exclude',
        )

        return {
            key: params.get(key)
            for key in override_keys
            if params.get(key) is not None
        }

    @staticmethod
    def _collect_proxy_cli_overrides(params):
        """
        Collect explicit proxy options that should override wizard/session params.

        Wizard and session restore can contain a different proxy source than the
        one selected on the command line. Proxy sources are mutually exclusive,
        so an explicit CLI proxy source must also clear the restored alternatives.
        Default parser values, such as proxy_pool=False or proxy_rotation=None,
        must not clear wizard/session proxy configuration.

        :param dict params:
        :return: dict
        """

        if params.get('proxy') is not None:
            return {
                'proxy': params.get('proxy'),
                'proxy_pool': False,
                'proxy_list': None,
                'proxy_rotation': None,
            }

        if params.get('proxy_list') is not None:
            overrides = {
                'proxy': None,
                'proxy_pool': False,
                'proxy_list': params.get('proxy_list'),
            }

            if params.get('proxy_rotation') is not None:
                overrides['proxy_rotation'] = params.get('proxy_rotation')

            return overrides

        if params.get('proxy_pool') is True:
            return {
                'proxy': None,
                'proxy_pool': True,
                'proxy_list': None,
                'proxy_rotation': None,
            }

        return {}

    @staticmethod
    def _match_fail_on_buckets(host, result, buckets):
        """
        Match CI/CD fail-on buckets against a scan result.

        :param str host:
        :param dict result:
        :param list[str] buckets:
        :return: list[dict]
        """

        if not isinstance(result, dict):
            return []

        totals = result.get('total') or {}
        matches = []

        for bucket in buckets:
            try:
                count = int(totals.get(bucket, 0))
            except (TypeError, ValueError):
                count = 0

            if count > 0:
                matches.append({
                    'host': host,
                    'bucket': bucket,
                    'count': count,
                })

        return matches

    @staticmethod
    def _record_target_failure(target_params, error):
        """
        Record and log a failed target without aborting a batch scan.

        :param dict target_params:
        :param Exception error:
        :return: dict
        """

        failure = {
            'host': target_params.get('host') or '-',
            'error': str(error),
        }

        tpl.warning(msg='Target scan failed: {0}. {1}'.format(
            failure.get('host'),
            failure.get('error')
        ))

        return failure

    @staticmethod
    def _format_target_failures(failures):
        """
        Format target failures for terminal output.

        :param list[dict] failures:
        :return: str
        """

        return '; '.join([
            '{0}: {1}'.format(
                item.get('host') or '-',
                item.get('error') or '-'
            )
            for item in failures
        ])

    @staticmethod
    def _format_fail_on_matches(matches):
        """
        Format CI/CD fail-on matches for terminal output.

        :param list[dict] matches:
        :return: str
        """

        return '; '.join([
            '{0} {1}={2}'.format(
                item.get('host') or '-',
                item.get('bucket'),
                item.get('count')
            )
            for item in matches
        ])

    @staticmethod
    def _resolve_scan_targets(params):
        """
        Build the list of scan targets from filtered params.

        :param dict params:
        :return: list[dict]
        """

        targets = params.get('targets')
        if targets:
            return targets

        if params.get('host'):
            target = {'host': params.get('host')}

            if params.get('scheme') is not None:
                target['scheme'] = params.get('scheme')

            if params.get('ssl') is not None:
                target['ssl'] = params.get('ssl')

            if params.get('port') is not None:
                target['port'] = params.get('port')

            return [target]

        return []


    @classmethod
    def _debug_transport(cls, params, transport, state):
        """
        Print debug-level transport diagnostics.

        :param dict params:
        :param NetworkTransportManager transport:
        :param str state:
        :return: None
        """

        if cls._is_transport_loggable(transport) is not True:
            return

        if cls._is_debug_enabled(params, level=1) is not True:
            return

        tpl.debug(msg='Network transport {0}: mode={1} profile={2} rotate={3} timeout={4}s healthcheck={5}'.format(
            state,
            transport.transport,
            transport.current_profile_name,
            getattr(transport, 'rotate_mode', 'none'),
            params.get('transport_timeout') or 30,
            params.get('transport_healthcheck_url') or '-'
        ))

        if cls._is_debug_enabled(params, level=2) is True:
            tpl.debug(msg='Network transport paths: profile={0} profiles={1} bin={2}'.format(
                params.get('transport_profile') or '-',
                params.get('transport_profiles') or '-',
                params.get('transport_bin') or '-'
            ))

    @staticmethod
    def _is_debug_enabled(params, level=1):
        """
        Check current debug level.

        :param dict params:
        :param int level:
        :return: bool
        """

        try:
            return int(params.get('debug') or 0) >= level
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _is_transport_loggable(transport):
        """
        Check if transport should be shown in terminal logs.

        :param NetworkTransportManager transport:
        :return: bool
        """

        return getattr(transport, 'transport', 'direct') != 'direct'

    @classmethod
    def _log_transport_start(cls, transport):
        """
        Print transport startup message.

        :param NetworkTransportManager transport:
        :return: None
        """

        if cls._is_transport_loggable(transport) is not True:
            return

        tpl.info(msg='Network transport enabled: {0} profile={1}'.format(
            transport.transport,
            transport.current_profile_name
        ))

    @classmethod
    def _log_transport_stop(cls, transport):
        """
        Print transport stop message.

        :param NetworkTransportManager transport:
        :return: None
        """

        if cls._is_transport_loggable(transport) is not True:
            return

        tpl.info(msg='Network transport stopped: {0} profile={1}'.format(
            transport.transport,
            transport.current_profile_name
        ))
