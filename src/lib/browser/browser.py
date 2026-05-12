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

import copy
import socket as net_socket
import threading
import time
import uuid
from .session import SessionManager, SessionError
from src.core import HttpRequestError, HttpsRequestError, ProxyRequestError, ResponseError
from src.core import SocketError
from src.core import helper
from src.core import request_http
from src.core import request_proxy
from src.core import request_https
from src.core import response
from src.core import socket
from src.lib.reader import Reader, ReaderError
from src.lib.reporter import Reporter, ReporterError
from src.lib.tpl import Tpl as tpl
from .config import Config
from .debug import Debug
from .calibration import Calibration
from .exceptions import BrowserError
from .fingerprint import Fingerprint
from .filter import Filter
from .header_bypass import HeaderBypassProbe
from .open_redirect import OpenRedirectProbe
from .shadow import ShadowProbe
from .sniffers import SnifferEngine, SnifferResult
from .threadpool import ThreadPool


class Browser(Filter):
    """ Browser class """

    ADDITIVE_SNIFFER_BUCKETS = (
        'file',
        'secret',
        'indexof',
        'stacktrace',
    )
    BASE_SUPPRESSOR_BUCKETS = (
        'skip',
    )
    BASE_NORMAL_BUCKETS = (
        'success',
    )

    WAF_SAFE_MIN_DELAY = 0.75
    WAF_SAFE_MAX_DELAY = 8.0
    WAF_SAFE_BACKOFF_FACTOR = 2.0
    WAF_SAFE_RECOVERY_FACTOR = 2.0
    WAF_SAFE_RECOVERY_THRESHOLD = 5
    WAF_SAFE_ACTIVATION_BLOCK_THRESHOLD = 3
    WAF_SAFE_ACTIVATION_WINDOW_SEC = 120.0
    WAF_SAFE_IMMEDIATE_SIGNAL_MARKERS = (
        'challenge',
        'captcha',
        'proof-of-work',
        'checking your browser',
        'just a moment',
        'cf-browser-verification',
        'cf-chl-',
    )
    WAF_SAFE_RATE_LIMIT_STATUSES = (429,)
    WAF_SAFE_RETRY_AFTER_STATUSES = (429, 503)
    WAF_SAFE_RETRY_AFTER_HEADER = 'retry-after'
    WAF_SAFE_RECOVERY_STATUSES = ('success', 'redirect', 'auth', 'forbidden', 'bad', 'certificate')

    def __init__(self, params):
        """
        Browser constructor
        :param dict params: filtered input params
        :raise BrowserError
        """

        try:
            self.__client = None
            self.__shared_cookie_header = None
            self.__config = Config(params)
            self.__debug = Debug(self.__config)
            self.__session_lock = threading.RLock()
            self.__session = None
            self.__session_dirty = False
            self.__completed_requests = set()
            self.__pending_requests = {}
            self.__seen_scan_urls = set()
            self.__processed_offset = 0
            self.__session_snapshot = params.get('session_snapshot')
            self.__waf_safe_lock = threading.RLock()
            self.__progress_output_lock = threading.RLock()
            self.__waf_safe_active = False
            self.__waf_safe_next_at = 0.0
            self.__waf_safe_delay = self.WAF_SAFE_MIN_DELAY
            self.__waf_safe_recovery_count = 0
            self.__waf_safe_vendor = None
            self.__waf_safe_confidence = None
            self.__waf_safe_block_events = []
            self.__calibration = None
            self.__header_bypass = HeaderBypassProbe(self.__config)
            self.__active_sniffer_names = SnifferEngine.active_names_from_config(self.__config)
            self.__open_redirect_probe = OpenRedirectProbe() if self.__is_active_sniffer_enabled('openredirect') is True else None
            self.__shadow_probe = None

            requested_method = str(getattr(self.__config, '_method', '') or '').upper()
            effective_method = str(getattr(self.__config, 'method', '') or '').upper()

            if requested_method == 'HEAD' and effective_method == 'GET':
                method_override_items = self.__config.method_override_items

                if len(method_override_items) > 0:
                    tpl.warning(
                        key='method_override',
                        sniffers=', '.join(method_override_items)
                    )
            self.__result = {'total': {}, 'items': {}, 'report_items': {}}
            self.__visited_recursive = set()
            self.__queued_recursive = set()
            self.__reader = Reader(browser_config={
                'list': self.__config.scan,
                'proxy_list': self.__config.proxy_list,
                'use_random': self.__config.is_random_list,
                'use_extensions': self.__config.is_extension_filter,
                'use_ignore_extensions': self.__config.is_ignore_extension_filter,
                'is_external_wordlist': self.__config.is_external_wordlist,
                'wordlist': self.__config.wordlist,
                'is_standalone_proxy': self.__config.is_standalone_proxy,
                'is_external_proxy_list': self.__config.is_external_proxy_list,
                'prefix': self.__config.prefix
            })

            if True is self.__config.is_external_reports_dir:
                Reporter.external_directory = self.__config.reports_dir

            if self.__config.scan == self.__config.DEFAULT_SCAN:
                if True is self.__config.is_extension_filter:
                    self.__reader.filter_by_extension(target=self.__config.scan,
                                                      output='extensionlist',
                                                      extensions=self.__config.extensions
                                                      )
                elif True is self.__config.is_ignore_extension_filter:
                    self.__reader.filter_by_ignore_extension(target=self.__config.scan,
                                                             output='ignore_extensionlist',
                                                             extensions=self.__config.ignore_extensions
                                                             )
            self.__reader.count_total_lines()

            Filter.__init__(self, self.__config, self.__reader.total_lines)

            self.__pool = ThreadPool(num_threads=self.__config.threads, total_items=self.__reader.total_lines,
                                     timeout=self.__config.delay)

            self.__result = {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()}

            self.__response = response(config=self.__config, debug=self.__debug, tpl=tpl)

            if self.__is_active_sniffer_enabled('shadow') is True:
                self.__shadow_probe = ShadowProbe(
                    self.__request_with_waf_safe_mode,
                    self.__handle_shadow_match,
                    self.__emit_shadow_probe_progress
                )

            if True is getattr(self.__config, 'is_session_enabled', False):
                self.__session = SessionManager(
                    self.__config.session_save,
                    autosave_sec=self.__config.session_autosave_sec,
                    autosave_items=self.__config.session_autosave_items
                )

            if self.__session_snapshot is not None:
                self.__restore_session_state(self.__session_snapshot)

        except (ResponseError, ReaderError) as error:
            raise BrowserError(error)

    def ping(self):
        """
        Check remote host for available
        :raise: BrowserError
        :return: None
        """

        try:
            tpl.info(key='checking_connect', host=self.__config.host, port=self.__config.port)
            socket.ping(self.__config.host, self.__config.port, self.__config.DEFAULT_SOCKET_TIMEOUT)
            tpl.info(key='online', host=self.__config.host, port=self.__config.port,
                     ip=socket.get_ip_address(self.__config.host))

        except SocketError as error:
            raise BrowserError(error)

    def scan(self):
        """
        Scanner
        :raise BrowserError
        :return: None
        """

        self.__debug.debug_user_agents()
        self.__debug.debug_header_bypass()
        self.__debug.debug_list(total_lines=self.__pool.total_items_size)
        self.__ensure_session_runtime_state()

        try:  # beginning scan processes
            if True is self.__config.is_random_list:
                if self.__config.scan == self.__config.DEFAULT_SCAN:
                    if True is self.__config.is_extension_filter:
                        setattr(self.__config, 'scan', 'extensionlist')
                    elif True is self.__config.is_ignore_extension_filter:
                        setattr(self.__config, 'scan', 'ignore_extensionlist')

                self.__reader.randomize_list(target=self.__config.scan, output='tmplist')

            self.__verify_active_scan_list_size()

            tpl.info(key='scanning', host=self.__config.host)
            self.__warn_filtered_progress_mode()
            self.__start_request_provider()

            if self.__session_snapshot is not None and len(self.__pending_requests) > 0:
                self.__resume_pending_requests()
                self.__pool.join()
            elif True is self.__pool.is_started:
                self.__reader.get_lines(
                    params={
                        'host': self.__config.host,
                        'port': self.__config.port,
                        'scheme': self.__config.scheme
                    },
                    loader=getattr(self, '_add_urls'.format())
                )

        except (ProxyRequestError, HttpRequestError, HttpsRequestError, ReaderError) as error:
            raise BrowserError(error)

        except (SystemExit, KeyboardInterrupt):
            try:
                self.__save_session(reason='signal', force=True)
            except SessionError as error:
                tpl.warning(msg='Session checkpoint failed during interruption: {0}'.format(error))
            raise

    def __verify_active_scan_list_size(self):
        """
        Verify the runtime scan list size before streaming requests.

        The thread pool is initialized before runtime transformations such as
        randomization. If the active temporary wordlist is shorter than the
        planned total, continuing would silently skip entries while the summary
        still displays the original item count. That must fail loudly instead of
        producing a partial scan that looks complete.

        :raise BrowserError:
        :return: None
        """

        if True is not self.__config.is_random_list:
            return

        if self.__session_snapshot is not None and len(self.__pending_requests) > 0:
            return

        try:
            active_total = int(self.__reader.count_active_lines())
            planned_total = int(self.__pool.total_items_size)
        except (AttributeError, ReaderError, TypeError, ValueError) as error:
            tpl.warning(msg='Unable to verify active scan list size: {0}'.format(error))
            return

        if active_total == planned_total:
            return

        message = (
            'Active scan list size mismatch: planned {planned} item(s), '
            'active runtime list has {active}. Aborting to avoid a partial scan.'
        ).format(planned=planned_total, active=active_total)
        tpl.warning(msg=message)
        raise BrowserError(message)

    def __warn_if_scan_finished_early(self):
        """
        Warn when the queue is drained before all planned items were submitted.

        :return: None
        """

        try:
            submitted = int(self.__pool.submitted_size)
            planned = int(self.__pool.total_items_size)
        except (AttributeError, TypeError, ValueError):
            return

        if submitted >= planned:
            return

        tpl.warning(
            msg=(
                'Scan finished after submitting {submitted}/{planned} planned item(s). '
                'The active wordlist ended early or was changed during streaming.'
            ).format(submitted=submitted, planned=planned)
        )

    @staticmethod
    def __render_fingerprint_bar(current, total, width=24):
        """
        Render an ASCII progress bar for fingerprinting.

        :param int current: current progress position
        :param int total: total progress positions
        :param int width: bar width in characters
        :return: str
        """

        safe_total = max(int(total or 1), 1)
        safe_current = min(max(int(current or 0), 0), safe_total)
        filled = int(round(width * safe_current / float(safe_total)))
        empty = max(width - filled, 0)
        return '[{0}{1}] {2}'.format('#' * filled, '-' * empty, helper.percent(safe_current, safe_total))

    def __fingerprint_progress(self, current, total, label):
        """
        Render fingerprint progress as rotating single-line output.

        Intermediate fingerprint stages are transient progress and should update
        in-place. The final "done" stage is printed as a persistent logger line.

        :param int current: current progress position
        :param int total: total progress positions
        :param str label: current fingerprint stage
        :return: None
        """

        import shutil
        import sys
        from datetime import datetime

        try:
            current_value = int(current or 0)
            total_value = int(total or 0)
        except (TypeError, ValueError):
            current_value = 0
            total_value = 0

        percent = 0.0
        if total_value > 0:
            percent = min(100.0, max(0.0, (float(current_value) / float(total_value)) * 100.0))

        bar_width = 24
        filled = int(round((percent / 100.0) * bar_width))
        filled = min(bar_width, max(0, filled))
        bar = '[{0}{1}] {2:.1f}%'.format('#' * filled, '-' * (bar_width - filled), percent)

        progress_message = 'Fingerprint {0} {1}'.format(bar, label)

        if str(label) == 'done':
            if getattr(self, '_Browser__fingerprint_progress_active', False) is True:
                last_length = getattr(self, '_Browser__fingerprint_progress_last_length', 0)
                if last_length > 0:
                    sys.stdout.write('\r{0}\r'.format(' ' * last_length))
                    sys.stdout.flush()

            self.__fingerprint_progress_active = False
            self.__fingerprint_progress_last_length = 0
            tpl.info(msg=progress_message)
            return

        message = '[{0}] info:    {1}'.format(
            datetime.now().strftime('%H:%M:%S'),
            progress_message
        )

        try:
            terminal_width = shutil.get_terminal_size((120, 24)).columns
        except (AttributeError, OSError, ValueError):
            terminal_width = 120

        max_length = max(40, int(terminal_width) - 1)
        if len(message) > max_length:
            message = '{0}...'.format(message[:max_length - 3])

        last_length = getattr(self, '_Browser__fingerprint_progress_last_length', 0)
        clear_length = max(last_length, len(message))

        sys.stdout.write('\r{0}\r{1}'.format(' ' * clear_length, message))
        sys.stdout.flush()

        self.__fingerprint_progress_last_length = len(message)
        self.__fingerprint_progress_active = True


    @staticmethod
    def __normalize_fingerprint_summary_value(value, default='unknown'):
        """
        Normalize optional fingerprint metadata for compact console output.

        :param mixed value: raw fingerprint value
        :param str default: fallback value
        :return: str
        """

        normalized = str(value or '').strip()
        if not normalized:
            return default
        return normalized

    @classmethod
    def __build_fingerprint_stack_summary(cls, fingerprint):
        """
        Build a short application/runtime/infrastructure summary.

        :param dict fingerprint: fingerprint result
        :return: str
        """

        if not isinstance(fingerprint, dict):
            return 'unknown'

        app_name = cls.__normalize_fingerprint_summary_value(fingerprint.get('name'))
        runtime = cls.__normalize_fingerprint_summary_value(
            fingerprint.get('runtime', {}).get('name') if isinstance(fingerprint.get('runtime'), dict) else None
        )
        infrastructure = cls.__normalize_fingerprint_summary_value(
            fingerprint.get('infrastructure', {}).get('provider')
            if isinstance(fingerprint.get('infrastructure'), dict) else None
        )

        values = []
        for value in (app_name, runtime, infrastructure):
            if value not in values:
                values.append(value)

        return ' | '.join(values) if values else 'unknown'

    @classmethod
    def __build_fingerprint_security_summary(cls, fingerprint):
        """
        Build a short security posture summary from fingerprint metadata.

        :param dict fingerprint: fingerprint result
        :return: str
        """

        if not isinstance(fingerprint, dict):
            return 'unknown'

        security_headers = fingerprint.get('security_headers')
        if not isinstance(security_headers, dict):
            return 'unknown'

        hsts = security_headers.get('hsts')
        if not isinstance(hsts, dict):
            return 'unknown'

        grade = cls.__normalize_fingerprint_summary_value(hsts.get('grade'))
        if grade == 'preload-ready':
            return 'HSTS preload-ready'
        return 'HSTS {0}'.format(grade)

    @classmethod
    def __render_fingerprint_summary_lines(cls, fingerprint):
        """
        Build compact post-fingerprint lines for early scan visibility.

        :param dict fingerprint: fingerprint result
        :return: list[str]
        """

        return [
            'Web stack: {0}'.format(cls.__build_fingerprint_stack_summary(fingerprint)),
            'Security posture: {0}'.format(cls.__build_fingerprint_security_summary(fingerprint)),
        ]

    @classmethod
    def __print_fingerprint_summary(cls, fingerprint):
        """
        Print compact fingerprint summary lines before dictionary enumeration starts.

        :param dict fingerprint: fingerprint result
        :return: None
        """

        for line in cls.__render_fingerprint_summary_lines(fingerprint):
            tpl.info(msg=line)

    @classmethod
    def __print_privacy_risk_warnings(cls, fingerprint):
        """
        Print medium/high privacy-risk warnings found during fingerprinting.

        :param dict fingerprint: fingerprint result
        :return: None
        """

        if not isinstance(fingerprint, dict):
            return

        privacy_risks = fingerprint.get('privacy_risks')
        if not isinstance(privacy_risks, dict):
            return

        supercookie = privacy_risks.get('supercookie')
        if not isinstance(supercookie, dict):
            return

        risk = str(supercookie.get('risk', 'none')).lower()
        if risk not in ('medium', 'high'):
            return

        warnings = supercookie.get('warnings')
        if not isinstance(warnings, (list, tuple)):
            return

        for warning in warnings:
            if warning:
                tpl.warning(msg='Possible supercookie tracking surface: {0}'.format(warning))

    def fingerprint(self):
        """
        Run heuristic technology fingerprinting before the main scan.

        :return: dict | None
        """

        self.__ensure_session_runtime_state()

        if self.__result.get('fingerprint') is not None:
            return self.__result.get('fingerprint')

        if True is not self.__config.is_fingerprint:
            return None

        try:
            tpl.info(msg='Fingerprinting {0} before the scan ...'.format(self.__config.host))

            if self.__client is None:
                self.__start_request_provider()

            result = Fingerprint(
                config=self.__config,
                client=self.__client,
                progress_callback=self.__fingerprint_progress,
            ).detect()
            self.__result['fingerprint'] = result

            tpl.info(
                msg='Fingerprint result: {category}/{name} ({confidence}%)'.format(
                    category=result.get('category', 'custom'),
                    name=result.get('name', 'Unknown custom stack'),
                    confidence=result.get('confidence', 0),
                )
            )

            self.__print_fingerprint_summary(result)
            self.__print_privacy_risk_warnings(result)

            if result.get('signals'):
                evidence = ', '.join([signal.get('value', '') for signal in result.get('signals', [])[:4]])
                tpl.info(msg='Fingerprint evidence: {0}'.format(evidence))

            return result

        except ProxyRequestError as error:
            if self.__is_standalone_proxy_mode() is True:
                raise BrowserError(error)

            tpl.warning(msg='Fingerprint skipped: {0}'.format(error))
            result = dict(Fingerprint.DEFAULT_RESULT)
            self.__result['fingerprint'] = result
            return result

        except (HttpRequestError, HttpsRequestError, AttributeError, TypeError, ValueError) as error:
            tpl.warning(msg='Fingerprint skipped: {0}'.format(error))
            result = dict(Fingerprint.DEFAULT_RESULT)
            self.__result['fingerprint'] = result
            return result

    def calibrate(self):
        """
        Build smart auto-calibration baseline before scan.

        :return: Calibration|None
        """

        self.__ensure_session_runtime_state()

        if True is not getattr(self.__config, 'is_auto_calibrate', False):
            return None

        if self.__calibration is not None and self.__calibration.is_enabled is True:
            tpl.info(msg='Auto-calibration baseline restored from session checkpoint')
            return self.__calibration

        try:
            if self.__client is None:
                self.__start_request_provider()

            getattr(getattr(self, '_Browser__debug', None), 'debug_auto_calibration_enabled', lambda *args, **kwargs: True)()

            dns_wildcard_addresses = self.__build_dns_wildcard_addresses()
            signatures = []
            for url in self.__build_calibration_urls():
                try:
                    response_object = self.__request_with_waf_safe_mode(url)
                    response_data = self.__response.handle(
                        response_object,
                        request_url=url,
                        items_size=0,
                        total_size=self.__config.calibration_samples,
                        ignore_list=[]
                    )

                    if response_data is None:
                        continue

                    if response_data[0] == 'blocked':
                        tpl.warning(
                            msg='Auto-calibration probe skipped because it was classified as blocked: {0}'.format(url))
                        continue

                    signatures.append(Calibration.build_signature(response_object, response_data))

                except ProxyRequestError as error:
                    if self.__is_standalone_proxy_mode() is True:
                        raise BrowserError(error)

                    tpl.warning(msg='Auto-calibration probe failed: {0}'.format(error))

                except (HttpRequestError, HttpsRequestError, ResponseError) as error:
                    tpl.warning(msg='Auto-calibration probe failed: {0}'.format(error))

            self.__calibration = Calibration(
                signatures=signatures,
                threshold=self.__config.calibration_threshold,
                dns_wildcard_addresses=dns_wildcard_addresses
            )

            if self.__calibration.has_dns_wildcard is True:
                tpl.info(
                    msg='DNS wildcard calibration ready: addresses={0}'.format(
                        ','.join(self.__calibration.dns_wildcard_addresses)
                    )
                )

            if self.__calibration.is_enabled is True:
                tpl.info(
                    msg='Auto-calibration baseline ready: stored signatures={0}, DNS wildcard addresses={1}'.format(
                        len(signatures),
                        len(self.__calibration.dns_wildcard_addresses)
                    )
                )
                self.__mark_session_dirty()
                return self.__calibration

            tpl.warning(msg='Auto-calibration disabled: no usable baseline signatures')
            return None

        except (AttributeError, TypeError, ValueError) as error:
            tpl.warning(msg='Auto-calibration skipped: {0}'.format(error))
            return None

    def __is_active_sniffer_enabled(self, name):
        """Return True when a built-in active sniffer is enabled.

        :param str name: public sniffer alias
        :return: bool
        """

        active_names = getattr(self, '_Browser__active_sniffer_names', None)
        if active_names is None:
            active_names = SnifferEngine.active_names_from_config(getattr(self, '_Browser__config', None))
            self.__active_sniffer_names = active_names

        return str(name).lower() in active_names

    def __is_standalone_proxy_mode(self):
        """Return True when the scan uses one explicit proxy endpoint."""

        return True is getattr(self.__config, 'is_standalone_proxy', False)

    def __is_subdomain_dns_calibration_enabled(self):
        """Return True when DNS wildcard calibration should run."""

        return (
            getattr(self.__config, 'is_auto_calibrate', False) is True
            and self.__config.scan == self.__config.SUBDOMAINS_SCAN
        )

    def __resolve_dns_addresses(self, hostname):
        """
        Resolve hostname addresses for DNS wildcard calibration.

        :param str hostname:
        :return: list[str]
        """

        try:
            records = net_socket.getaddrinfo(str(hostname), None)
        except (OSError, TypeError, UnicodeError, ValueError):
            return []

        addresses = []
        for record in records:
            try:
                address = record[4][0]
            except (IndexError, TypeError):
                continue

            if address:
                addresses.append(str(address))

        return Calibration._normalize_dns_addresses(addresses)

    def __build_dns_wildcard_hosts(self):
        """
        Build impossible subdomain names for DNS wildcard baseline probes.

        :return: list[str]
        """

        sample_count = max(2, min(int(self.__config.calibration_samples or 2), 5))
        token = uuid.uuid4().hex[:12]
        base_host = str(self.__config.host).strip().strip('.')

        return [
            'cdn-{0}-{1}.{2}'.format(token, index, base_host)
            for index in range(sample_count)
        ]

    def __build_dns_wildcard_addresses(self):
        """
        Resolve random subdomains and build DNS wildcard address baseline.

        :return: list[str]
        """

        if self.__is_subdomain_dns_calibration_enabled() is not True:
            return []

        resolved_samples = []
        for hostname in self.__build_dns_wildcard_hosts():
            addresses = self.__resolve_dns_addresses(hostname)
            if len(addresses) > 0:
                resolved_samples.append(addresses)

        if len(resolved_samples) < 2:
            return []

        wildcard_addresses = []
        for addresses in resolved_samples:
            wildcard_addresses.extend(addresses)

        return Calibration._normalize_dns_addresses(wildcard_addresses)

    def __build_calibration_urls(self):
        """
        Build random impossible URLs for calibration probes.

        Calibration probes must cover multiple URL shapes. Some targets return a
        normal 404 for static asset-like paths while serving a soft-200 catch-all
        page for root-level or application-like paths.

        :return: list[str]
        """

        urls = []
        token = uuid.uuid4().hex[:12]
        path_templates = (
            '{token}-{index}',
            'assets/{token}-{index}.map',
            '{token}-{index}.php',
            '{token}-{index}.html',
            'api/{token}-{index}',
            'static/{token}-{index}.js',
            'wp-content/uploads/{token}-{index}.php',
            'admin/{token}-{index}',
        )

        for index in range(self.__config.calibration_samples):
            template = path_templates[index % len(path_templates)]
            path = template.format(token=token, index=index)
            urls.append(self.__build_calibration_url(path))

        return urls

    def __build_calibration_url(self, path):
        """
        Build a calibration URL under the configured scan prefix.

        :param str path:
        :return: str
        """

        prefix = str(getattr(self.__config, 'prefix', '') or '').strip('/')
        clean_path = str(path).strip().lstrip('/')

        if prefix:
            clean_path = '{0}/{1}'.format(prefix, clean_path)

        port = self.__config.port
        port_suffix = ''

        if self.__config.scheme == 'http://' and port not in [None, 80]:
            port_suffix = ':{0}'.format(port)

        if self.__config.scheme == 'https://' and port not in [None, 443]:
            port_suffix = ':{0}'.format(port)

        return '{0}{1}{2}/{3}'.format(
            self.__config.scheme,
            self.__config.host,
            port_suffix,
            clean_path
        )

    def __sync_shared_cookies_from_client(self):
        """
        Capture accepted cookies from the current request provider.

        Request providers own the low-level cookie extraction, while Browser owns
        the scan lifecycle. Keeping this small shared snapshot lets cookies
        survive provider recreation between fingerprint, calibration and the
        main dictionary scan.

        :return: None
        """

        if True is not getattr(self.__config, 'accept_cookies', False):
            return

        if self.__client is None:
            return

        try:
            cookies = self.__client._push_cookies()
        except AttributeError:
            return

        cookies = str(cookies or '').strip()
        if cookies:
            self.__shared_cookie_header = cookies

    def __apply_shared_cookies_to_client(self):
        """
        Apply captured cookies to a freshly created request provider.

        :return: None
        """

        if True is not getattr(self.__config, 'accept_cookies', False):
            return

        if self.__client is None:
            return

        cookies = str(self.__shared_cookie_header or '').strip()
        if not cookies:
            return

        if '\r' in cookies or '\n' in cookies:
            return

        try:
            self.__client.add_header('Cookie', cookies)
            setattr(self.__client, '_cookies', cookies)
        except AttributeError:
            pass

    def __start_request_provider(self):
        """
        Start selected request provider

        :return: None
        """

        self.__sync_shared_cookies_from_client()

        if True is self.__config.is_proxy:
            self.__client = request_proxy(self.__config, proxy_list=self.__reader.get_proxies(),
                                          agent_list=self.__reader.get_user_agents(), debug=self.__debug, tpl=tpl)
        else:

            if True is self.__config.is_ssl:
                self.__client = request_https(self.__config, agent_list=self.__reader.get_user_agents(),
                                              debug=self.__debug, tpl=tpl)
            else:
                self.__client = request_http(self.__config, agent_list=self.__reader.get_user_agents(),
                                             debug=self.__debug, tpl=tpl)

        self.__apply_shared_cookies_to_client()

    def __request_with_waf_safe_mode(self, url, extra_headers=None):
        """
        Serialize outbound requests when WAF safe mode is active.

        :param str url: request URL
        :param dict | None extra_headers: temporary per-request headers
        :return: urllib3.HTTPResponse | None
        """

        self.__ensure_session_runtime_state()

        def request_once():
            """
            Execute one request while preserving the old request call shape.

            :return: urllib3.HTTPResponse | None
            """

            if extra_headers is None:
                response = self.__client.request(url)
            else:
                response = self.__client.request(url, extra_headers=extra_headers)

            self.__sync_shared_cookies_from_client()
            return response

        if True is not getattr(self.__config, 'is_waf_safe_mode', False):
            return request_once()

        if True is not self.__waf_safe_active:
            return request_once()

        with self.__waf_safe_lock:
            now = time.monotonic()
            if now < self.__waf_safe_next_at:
                time.sleep(self.__waf_safe_next_at - now)

            response = request_once()
            self.__waf_safe_next_at = time.monotonic() + self.__waf_safe_delay
            return response

    def __is_explicit_waf_safe_activation_detection(self, detection):
        """
        Detect challenge/captcha-style WAF signals that must enable safe mode immediately.

        Ordinary WAF 403 responses are counted by threshold instead.

        :param dict|None detection:
        :return: bool
        """

        if False is isinstance(detection, dict):
            return False

        for signal in detection.get('signals', []):
            normalized = str(signal).lower()
            for marker in self.WAF_SAFE_IMMEDIATE_SIGNAL_MARKERS:
                if marker in normalized:
                    return True

        return False

    def __should_activate_waf_safe_mode_from_block(self):
        """
        Return True after repeated blocked responses in a short rolling window.

        :return: bool
        """

        now = time.monotonic()
        oldest_allowed = now - self.WAF_SAFE_ACTIVATION_WINDOW_SEC
        self.__waf_safe_block_events = [
            event_at for event_at in self.__waf_safe_block_events
            if event_at >= oldest_allowed
        ]
        self.__waf_safe_block_events.append(now)

        return len(self.__waf_safe_block_events) >= self.WAF_SAFE_ACTIVATION_BLOCK_THRESHOLD

    def __activate_waf_safe_mode(self, detection, immediate=False):
        """
        Activate cautious scan profile after explicit or repeated WAF detections.

        :param dict|None detection:
        :param bool immediate:
        :return: None
        """

        self.__ensure_session_runtime_state()

        if True is not getattr(self.__config, 'is_waf_safe_mode', False):
            return

        if False is isinstance(detection, dict):
            return

        with self.__waf_safe_lock:
            if True is self.__waf_safe_active:
                return

            if immediate is not True and False is self.__should_activate_waf_safe_mode_from_block():
                return

            self.__waf_safe_active = True
            self.__waf_safe_vendor = detection.get('name')
            self.__waf_safe_confidence = detection.get('confidence')
            self.__waf_safe_next_at = time.monotonic() + self.__waf_safe_delay

        self.__finish_filtered_progress_line()
        tpl.warning(
            key='waf_safe_mode_activated',
            vendor=self.__waf_safe_vendor or 'Generic WAF',
            confidence=self.__waf_safe_confidence if self.__waf_safe_confidence is not None else '-',
            delay=self.__waf_safe_delay
        )

    @staticmethod
    def __extract_response_code(response, response_data):
        """
        Resolve numeric HTTP response code from response object or handled response data.

        :param urllib3.response.HTTPResponse|object response:
        :param tuple|None response_data:
        :return: int | None
        """

        try:
            return int(response.status)
        except (AttributeError, TypeError, ValueError):
            pass

        try:
            return int(response_data[3])
        except (IndexError, TypeError, ValueError):
            return None

    @classmethod
    def __get_header_value(cls, response, header_name):
        """
        Resolve response header value using case-insensitive lookup.

        :param urllib3.response.HTTPResponse|object response:
        :param str header_name:
        :return: str | None
        """

        try:
            headers = response.headers
        except AttributeError:
            return None

        expected = str(header_name).lower()

        try:
            value = headers.get(header_name)
            if value is not None:
                return str(value)
        except AttributeError:
            pass

        try:
            value = headers.get(expected)
            if value is not None:
                return str(value)
        except AttributeError:
            pass

        try:
            for key, value in headers.items():
                if str(key).lower() == expected:
                    return str(value)
        except AttributeError:
            return None

        return None

    def __get_retry_after_delay(self, response):
        """
        Resolve Retry-After delay in seconds.

        This intentionally supports only numeric Retry-After values.
        HTTP-date based Retry-After values are ignored to keep safe-mode behaviour predictable.

        :param urllib3.response.HTTPResponse|object response:
        :return: float | None
        """

        value = self.__get_header_value(response, self.WAF_SAFE_RETRY_AFTER_HEADER)
        if value is None:
            return None

        try:
            delay = float(str(value).strip())
        except (TypeError, ValueError):
            return None

        if delay < 0:
            return None

        return delay

    def __is_explicit_waf_safe_backoff_signal(self, response, response_data):
        """
        Detect explicit rate-limit / temporary-response signals that can activate WAF safe mode.

        Plain 403 is intentionally not treated as a backoff signal.

        :param urllib3.response.HTTPResponse|object response:
        :param tuple response_data:
        :return: bool
        """

        response_code = self.__extract_response_code(response, response_data)

        if response_code in self.WAF_SAFE_RATE_LIMIT_STATUSES:
            return True

        if response_code in self.WAF_SAFE_RETRY_AFTER_STATUSES:
            return self.__get_retry_after_delay(response) is not None

        return False

    def __build_waf_safe_backoff_detection(self, response, response_data):
        """
        Build synthetic safe-mode activation metadata for rate-limit / temporary responses.

        :param urllib3.response.HTTPResponse|object response:
        :param tuple response_data:
        :return: dict
        """

        response_code = self.__extract_response_code(response, response_data)
        signals = ['status:{0}'.format(response_code)]

        if self.__get_retry_after_delay(response) is not None:
            signals.append('header:retry-after')

        if response_code == 429:
            name = 'Rate limit'
            confidence = 85
        else:
            name = 'Temporary response'
            confidence = 75

        return {
            'name': name,
            'confidence': confidence,
            'signals': signals,
        }

    def __should_penalize_waf_safe_backoff(self, response, response_status, response_code):
        """
        Decide whether current response should increase WAF safe-mode cooldown.

        Plain 403 Forbidden is not a penalty. It becomes a penalty only when response
        classification is already "blocked", meaning WAF/challenge detection matched.

        :param urllib3.response.HTTPResponse|object response:
        :param str response_status:
        :param int|None response_code:
        :return: bool
        """

        if response_status == 'blocked':
            return True

        if response_code in self.WAF_SAFE_RATE_LIMIT_STATUSES:
            return True

        if response_code in self.WAF_SAFE_RETRY_AFTER_STATUSES:
            return self.__get_retry_after_delay(response) is not None

        return False

    def __increase_waf_safe_backoff(self, response):
        """
        Increase WAF safe-mode cooldown using exponential backoff or Retry-After.

        :param urllib3.response.HTTPResponse|object response:
        :return: None
        """

        retry_after_delay = self.__get_retry_after_delay(response)

        if retry_after_delay is not None:
            next_delay = retry_after_delay
        else:
            next_delay = self.__waf_safe_delay * self.WAF_SAFE_BACKOFF_FACTOR

        self.__waf_safe_delay = min(
            max(float(next_delay), self.WAF_SAFE_MIN_DELAY),
            self.WAF_SAFE_MAX_DELAY
        )
        self.__waf_safe_recovery_count = 0
        self.__waf_safe_next_at = time.monotonic() + self.__waf_safe_delay

    def __recover_waf_safe_backoff(self):
        """
        Gradually reduce WAF safe-mode cooldown after clean responses.

        :return: None
        """

        if self.__waf_safe_delay <= self.WAF_SAFE_MIN_DELAY:
            self.__waf_safe_recovery_count = 0
            return

        self.__waf_safe_recovery_count += 1

        if self.__waf_safe_recovery_count < self.WAF_SAFE_RECOVERY_THRESHOLD:
            return

        self.__waf_safe_delay = max(
            self.__waf_safe_delay / self.WAF_SAFE_RECOVERY_FACTOR,
            self.WAF_SAFE_MIN_DELAY
        )
        self.__waf_safe_recovery_count = 0

    def __should_recover_waf_safe_backoff(self, response_status):
        """
        Decide whether current response can be treated as a clean recovery signal.

        :param str response_status:
        :return: bool
        """

        return response_status in self.WAF_SAFE_RECOVERY_STATUSES

    def __update_waf_safe_backoff(self, response, response_data):
        """
        Update adaptive WAF safe-mode cooldown after response classification.

        :param urllib3.response.HTTPResponse|object response:
        :param tuple|None response_data:
        :return: None
        """

        self.__ensure_session_runtime_state()

        if True is not getattr(self.__config, 'is_waf_safe_mode', False):
            return

        if response_data is None:
            return

        response_status = str(response_data[0])
        response_code = self.__extract_response_code(response, response_data)

        with self.__waf_safe_lock:
            if True is not self.__waf_safe_active:
                return

            if self.__should_penalize_waf_safe_backoff(response, response_status, response_code):
                self.__increase_waf_safe_backoff(response)
                return

            if self.__should_recover_waf_safe_backoff(response_status):
                self.__recover_waf_safe_backoff()

    def __should_suspend_recursive_expansion(self, response_status):
        """
        Do not let blocked responses amplify recursive scans in WAF safe mode.

        :param str response_status:
        :return: bool
        """

        self.__ensure_session_runtime_state()

        return (
            getattr(self.__config, 'is_waf_safe_mode', False) is True
            and response_status == 'blocked'
        )

    def __match_dns_wildcard_response(self, url):
        """
        Match subdomain URL hostname against active DNS wildcard baseline.

        :param str url:
        :return: dict|None
        """

        self.__ensure_session_runtime_state()

        if self.__is_subdomain_dns_calibration_enabled() is not True:
            return None

        if self.__calibration is None or self.__calibration.has_dns_wildcard is not True:
            return None

        parsed = helper.parse_url(url)
        hostname = getattr(parsed, 'hostname', None)

        if not hostname:
            return None

        if str(hostname).strip('.').lower() == str(self.__config.host).strip('.').lower():
            return None

        addresses = self.__resolve_dns_addresses(hostname)
        return self.__calibration.match_dns_wildcard(hostname, addresses)

    def __match_calibrated_response(self, response_object, response_data):
        """
        Match response against active calibration baseline.

        :param object response_object:
        :param tuple response_data:
        :return: dict|None
        """

        self.__ensure_session_runtime_state()

        if True is not getattr(self.__config, 'is_auto_calibrate', False):
            return None

        if self.__calibration is None:
            return None

        if response_data is not None and len(response_data) > 0 and response_data[0] == 'stacktrace':
            return None

        return self.__calibration.match(response_object, response_data)


    def __probe_open_redirect(self, url):
        """Run controlled open redirect verification for eligible query parameters.

        :param str url: original scan request URL
        :return: True when a confirmed finding was persisted
        :rtype: bool
        """

        self.__ensure_session_runtime_state()

        open_redirect_probe = getattr(self, '_Browser__open_redirect_probe', None)
        if open_redirect_probe is None:
            return False

        for variant in open_redirect_probe.filter_new_variants(url):
            response_object = self.__request_with_waf_safe_mode(variant.get('url'))

            if response_object is None:
                continue

            if OpenRedirectProbe.is_confirmed(response_object) is not True:
                continue

            metadata = OpenRedirectProbe.metadata(url, variant, response_object)
            self.__handle_open_redirect_match(variant.get('url'), response_object, metadata)
            return True

        return False

    def __handle_open_redirect_match(self, url, response_object, metadata):
        """Persist and render one confirmed open redirect finding.

        :param str url: controlled probe URL
        :param object response_object: matching redirect response
        :param dict metadata: open redirect detection metadata
        :return: True
        :rtype: bool
        """

        finding = SnifferResult(
            bucket='openredirect',
            url=str(url),
            code=str(getattr(response_object, 'status', '-')),
            size=self.__response._get_content_size(response_object),
            metadata=metadata,
        )

        self.__emit_sniffer_finding(finding, response_object=response_object)
        self.__catch_sniffer_finding(finding)
        return True

    def __probe_header_bypass(self, url, base_response_data):
        """
        Run controlled header-injection bypass probes for blocked responses.

        :param str url: original blocked request URL
        :param tuple base_response_data: original handled response data
        :return: None
        """

        self.__ensure_session_runtime_state()

        if self.__header_bypass is None:
            return

        if True is not self.__header_bypass.should_probe(base_response_data):
            if (
                getattr(self.__config, 'is_header_bypass', False) is True
                and HeaderBypassProbe.response_status(base_response_data) == 'blocked'
            ):
                getattr(getattr(self, '_Browser__debug', None), 'debug_header_bypass_skipped', lambda *args, **kwargs: True)(
                    HeaderBypassProbe.response_code(base_response_data) or '-'
                )
            return

        variants = self.__header_bypass.build_variants(url)
        getattr(getattr(self, '_Browser__debug', None), 'debug_header_bypass_probing', lambda *args, **kwargs: True)(
            HeaderBypassProbe.response_code(base_response_data) or '-',
            len(variants)
        )

        for variant in variants:
            probe_url = variant.get('url') if variant.get('type') == 'path' else url
            extra_headers = None

            if variant.get('type') != 'path':
                extra_headers = {variant.get('header'): variant.get('value')}

            response_object = self.__request_with_waf_safe_mode(probe_url, extra_headers=extra_headers)

            if response_object is None:
                continue

            probe_response_data = self.__response.handle(
                response_object,
                request_url=probe_url,
                items_size=self.__pool.items_size,
                total_size=self.__pool.total_items_size,
                ignore_list=self.__reader.get_ignored_list()
            )

            if probe_response_data is None:
                continue

            if HeaderBypassProbe.is_promising(base_response_data, probe_response_data):
                metadata = HeaderBypassProbe.metadata(variant, base_response_data, probe_response_data)
                getattr(getattr(self, '_Browser__debug', None), 'debug_header_bypass_candidate', lambda *args, **kwargs: True)(metadata)
                self.__catch_report_data(
                    'bypass',
                    probe_response_data[1],
                    probe_response_data[2],
                    probe_response_data[3],
                    metadata=metadata
                )
                return

        getattr(getattr(self, '_Browser__debug', None), 'debug_header_bypass_finished', lambda *args, **kwargs: True)()

    def __get_progress_output_lock(self):
        """Return the shared lock for rotating progress and persistent log output."""

        if not hasattr(self, '_Browser__progress_output_lock'):
            self.__progress_output_lock = threading.RLock()

        return self.__progress_output_lock

    def __clear_filtered_progress(self):
        """
        Clear active rotating filtered-progress line before printing real findings.

        Uses only carriage return and spaces, so it works on macOS, Linux and Windows
        without relying on ANSI escape support.

        :return: None
        """

        import sys

        with self.__get_progress_output_lock():
            if getattr(self, '_Browser__filtered_progress_active', False) is not True:
                return

            last_length = getattr(self, '_Browser__filtered_progress_last_length', 0)
            if last_length > 0:
                sys.stdout.write('\r{0}\r'.format(' ' * last_length))
                sys.stdout.flush()

            self.__filtered_progress_active = False
            self.__filtered_progress_last_length = 0

    def __finish_filtered_progress_line(self):
        """Terminate an active rotating progress line before normal logger output.

        Warnings and other logger lines are persistent output. They must start on
        a fresh line, but we should not clear the previous progress text because
        clearing resets the terminal state and can make the next rotating update
        visually reuse stale URL fragments while only the counter changes.

        :return: None
        """

        import sys

        with self.__get_progress_output_lock():
            if getattr(self, '_Browser__filtered_progress_active', False) is not True:
                return

            sys.stdout.write('\n')
            sys.stdout.flush()

            self.__filtered_progress_active = False
            self.__filtered_progress_last_length = 0

    def __emit_filtered_progress(self, bucket, response_data, metadata=None, request_url=None):
        """
        Emit one-line rotating progress for responses suppressed by filters/calibration.

        Suppressed responses are not findings and must not pollute stdout as persistent
        lines. The rendered line is truncated to terminal width to avoid wrapping; wrapped
        carriage-return progress can visually concatenate lines on macOS/Linux/Windows.

        :param str bucket: suppressed result bucket
        :param tuple response_data: classified response tuple
        :param dict metadata: optional suppression metadata
        :param str request_url: original request URL, used for redirect responses
        :return: whether a progress line was emitted
        :rtype: bool
        """

        import shutil
        import sys
        from datetime import datetime

        items_size = getattr(self.__pool, 'items_size', 0)
        total_size = getattr(self.__pool, 'total_items_size', 0)

        percent = 0.0
        if total_size:
            percent = (float(items_size) / float(total_size)) * 100.0

        response_url = request_url if request_url else (response_data[1] if len(response_data) > 1 else '-')
        content_size = response_data[2] if len(response_data) > 2 else '-'
        response_code = response_data[3] if len(response_data) > 3 else '-'

        details = ''
        if metadata:
            score = metadata.get('calibration_score')
            if score is not None:
                details = ' - score={0}'.format(
                    '{0:.2f}'.format(float(score)) if isinstance(score, (int, float)) else score
                )

        message = '[{0}] info:    {1:.1f}% [{2:06d}/{3}] - {4} - {5} - {6}{7} {8}'.format(
            datetime.now().strftime('%H:%M:%S'),
            percent,
            items_size,
            total_size,
            bucket,
            response_code,
            content_size,
            details,
            response_url
        )

        try:
            terminal_width = shutil.get_terminal_size((120, 24)).columns
        except (AttributeError, OSError, ValueError):
            terminal_width = 120

        max_length = max(40, int(terminal_width) - 1)
        if len(message) > max_length:
            message = '{0}...'.format(message[:max_length - 3])

        with self.__get_progress_output_lock():
            last_length = getattr(self, '_Browser__filtered_progress_last_length', 0)
            clear_length = max(last_length, len(message))

            sys.stdout.write('\r{0}\r{1}'.format(' ' * clear_length, message))
            sys.stdout.flush()

            self.__filtered_progress_last_length = len(message)
            self.__filtered_progress_active = True

        return True

    def __http_request(self, url, depth=0):
        """
        Make HTTP request
        :param str url: received url
        :param int depth: current recursion depth
        :return: None
        """

        self.__ensure_session_runtime_state()

        try:
            dns_calibration_match = self.__match_dns_wildcard_response(url)
            if dns_calibration_match is not None:
                self.__catch_report_data(
                    'calibrated',
                    url,
                    '0B',
                    'DNS',
                    metadata=dns_calibration_match
                )
                return

            resp = self.__request_with_waf_safe_mode(url)

            response_data = self.__response.handle(
                resp,
                request_url=url,
                items_size=self.__pool.items_size,
                total_size=self.__pool.total_items_size,
                ignore_list=self.__reader.get_ignored_list(),
                emit_debug=False
            )

            if None is response_data:
                self.__catch_report_data('ignored', url)
                return

            passive_sniffer_findings = self.__collect_passive_sniffer_findings(resp, response_data)

            waf_detection = None
            stacktrace_detection = getattr(resp, 'opendoor_stacktrace_detection', None)
            secret_detection = getattr(resp, 'opendoor_secret_detection', None)

            primary_suppressed = self.__should_suppress_primary_response(
                resp,
                response_data,
                passive_sniffer_findings,
            )

            if response_data[0] == 'blocked':
                waf_detection = getattr(self.__response, 'waf_detection', None)
                self.__activate_waf_safe_mode(
                    waf_detection,
                    immediate=self.__is_explicit_waf_safe_activation_detection(waf_detection)
                )
            elif self.__is_explicit_waf_safe_backoff_signal(resp, response_data):
                self.__activate_waf_safe_mode(
                    self.__build_waf_safe_backoff_detection(resp, response_data),
                    immediate=True
                )

            self.__update_waf_safe_backoff(resp, response_data)
            self.__probe_header_bypass(url, response_data)
            self.__run_inline_active_sniffers(url, response_data, resp)

            calibration_match = self.__match_calibrated_response(resp, response_data)
            if calibration_match is not None:
                self.__emit_passive_sniffer_findings(passive_sniffer_findings, resp)
                self.__emit_filtered_progress('calibrated', response_data, calibration_match, request_url=url)
                self.__catch_report_data(
                    'calibrated',
                    response_data[1],
                    response_data[2],
                    response_data[3],
                    metadata=calibration_match
                )
                return
            debug_response_data = getattr(self.__response, 'debug_response_data', None)
            if callable(debug_response_data) and primary_suppressed is not True:
                self.__clear_filtered_progress()
                debug_response_data(
                    response_data,
                    request_url=url,
                    items_size=self.__pool.items_size,
                    total_size=self.__pool.total_items_size,
                    response=resp
                )

            if False is self.__is_response_allowed(resp, response_data):
                self.__emit_passive_sniffer_findings(passive_sniffer_findings, resp)
                if primary_suppressed is not True:
                    self.__catch_report_data('ignored', response_data[1], response_data[2], response_data[3])
            else:
                metadata = {}
                if isinstance(waf_detection, dict):
                    metadata.update(waf_detection)
                if isinstance(stacktrace_detection, dict):
                    metadata['stacktrace_detection'] = dict(stacktrace_detection)
                if isinstance(secret_detection, dict):
                    metadata['secret_detection'] = dict(secret_detection)
                if len(metadata) == 0:
                    metadata = None

                if primary_suppressed is not True:
                    self.__catch_report_data(
                        response_data[0],
                        response_data[1],
                        response_data[2],
                        response_data[3],
                        metadata=metadata,
                    )

                self.__emit_passive_sniffer_findings(passive_sniffer_findings, resp)

                self.__run_deferred_active_sniffers(response_data, resp)

                if False is self.__should_suspend_recursive_expansion(response_data[0]):
                    if self.__should_expand_recursively(response_data[3], response_data[1], depth):
                        if response_data[1] not in self.__visited_recursive:
                            self.__visited_recursive.add(response_data[1])
                            self.__enqueue_recursive_children(response_data[1], depth)

        except (HttpRequestError, HttpsRequestError, ProxyRequestError, ResponseError) as error:
            raise BrowserError(error)
        finally:
            self.__finalize_processed_request(url, depth)

    def __should_suppress_primary_response(self, response_object, response_data, passive_findings):
        """
        Decide whether the base response bucket should be suppressed.

        Suppressor sniffers such as skipempty/skipsizes and soft404 collation
        suppress only base reporting/progress. Additive security findings still
        render and persist through their own buckets.

        :param object response_object: raw response object
        :param tuple response_data: legacy classified response tuple
        :param list passive_findings: collected additive sniffer findings
        :return: True when the base response should not be rendered or reported
        :rtype: bool
        """

        try:
            primary_bucket = str(response_data[0])
            response_code = str(response_data[3])
        except (TypeError, IndexError):
            return False

        if primary_bucket in self.BASE_SUPPRESSOR_BUCKETS:
            return True

        if self.__is_soft404_suppressor_response(response_object, primary_bucket, response_code):
            return True

        if primary_bucket in self.BASE_NORMAL_BUCKETS:
            for finding in passive_findings or []:
                if isinstance(finding, SnifferResult) and finding.suppress_normal is True:
                    return True

        return False

    @staticmethod
    def __is_soft404_suppressor_response(response_object, primary_bucket, response_code):
        """
        Return True when collation converted a 2xx response into a failed soft404.

        The legacy collation plugin uses the public ``failed`` bucket. A real 404
        should keep legacy behaviour, while a 2xx soft404 should act as a
        suppressor for base reporting only.

        :param object response_object: raw response object
        :param str primary_bucket: legacy classified bucket
        :param str response_code: normalized response code
        :return: bool
        """

        if primary_bucket != 'failed':
            return False

        try:
            status = int(response_code)
        except (TypeError, ValueError):
            try:
                status = int(getattr(response_object, 'status', 0))
            except (TypeError, ValueError):
                return False

        return 200 <= status < 300

    def __collect_passive_sniffer_findings(self, response_object, response_data):
        """
        Collect additional additive sniffer findings without first-match conflicts.

        The legacy response classifier still decides the primary bucket. This helper
        only adds secondary additive findings for enabled sniffers that would have
        been skipped by the legacy first-match chain.

        :param object response_object: raw HTTP response object
        :param tuple response_data: legacy classified response tuple
        :return: list[SnifferResult]
        """

        if response_object is None or response_data is None:
            return []

        try:
            primary_bucket = response_data[0]
            request_url = response_data[1]
            content_size = response_data[2]
            response_code = response_data[3]
        except (TypeError, IndexError):
            return []

        findings = []
        seen_buckets = {primary_bucket}

        for plugin in self.__passive_additive_plugins():
            bucket = self.__plugin_bucket(plugin)
            if bucket in seen_buckets:
                continue

            try:
                detected_bucket = plugin.process(response_object)
            except Exception:
                continue

            if detected_bucket != bucket:
                continue

            findings.append(SnifferResult(
                bucket=bucket,
                url=request_url,
                code=response_code,
                size=content_size,
                metadata=self.__metadata_for_sniffer_bucket(bucket, response_object),
                suppress_normal=True,
                evidence_key=bucket,
            ))
            seen_buckets.add(bucket)

        return findings

    def __passive_additive_plugins(self):
        """
        Return enabled additive response plugins in deterministic engine order.

        :return: list
        """

        plugins = list(getattr(self.__response, '_response_plugins', []) or [])
        additive_order = {name: index for index, name in enumerate(self.ADDITIVE_SNIFFER_BUCKETS)}
        selected = []

        for plugin in plugins:
            bucket = self.__plugin_bucket(plugin)
            if bucket in additive_order:
                selected.append(plugin)

        return sorted(selected, key=lambda plugin: additive_order.get(self.__plugin_bucket(plugin), 100))

    @staticmethod
    def __plugin_bucket(plugin):
        """
        Return normalized response plugin bucket name.

        :param object plugin: response plugin instance
        :return: str
        """

        return str(getattr(plugin, 'RESPONSE_INDEX', '')).lower()

    @staticmethod
    def __metadata_for_sniffer_bucket(bucket, response_object):
        """
        Build report metadata for a passive sniffer finding.

        :param str bucket: sniffer bucket name
        :param object response_object: raw HTTP response object
        :return: dict
        """

        if bucket == 'secret':
            detection = getattr(response_object, 'opendoor_secret_detection', None)
            if isinstance(detection, dict):
                return {'secret_detection': dict(detection)}

        if bucket == 'stacktrace':
            detection = getattr(response_object, 'opendoor_stacktrace_detection', None)
            if isinstance(detection, dict):
                return {'stacktrace_detection': dict(detection)}

        return {}

    def __emit_passive_sniffer_findings(self, findings, response_object):
        """
        Render and persist collected passive sniffer findings.

        :param list findings: SnifferResult values
        :param object response_object: raw HTTP response object
        :return: int
        """

        emitted = 0
        for finding in findings or []:
            if self.__emit_sniffer_finding(finding, response_object=response_object) is True:
                emitted += 1
            self.__catch_sniffer_finding(finding)

        return emitted

    def __run_inline_active_sniffers(self, url, response_data, response_object):
        """
        Run active sniffers that complete within the current request lifecycle.

        Active sniffers are enabled through the sniffer catalog. This helper keeps
        Browser orchestration independent from individual sniffer aliases and
        gives future inline active sniffers one common entrypoint.

        :param str url: original request URL
        :param tuple response_data: legacy classified response tuple
        :param object response_object: raw HTTP response object
        :return: number of active findings emitted during this request
        :rtype: int
        """

        emitted = 0

        if self.__is_active_sniffer_enabled('openredirect') is True:
            emitted += 1 if self.__probe_open_redirect(url) is True else 0

        return emitted

    def __run_deferred_active_sniffers(self, response_data, response_object):
        """
        Queue active sniffers that drain later in the scan lifecycle.

        :param tuple response_data: legacy classified response tuple
        :param object response_object: raw HTTP response object
        :return: number of active probe jobs submitted
        :rtype: int
        """

        submitted = 0

        if self.__is_active_sniffer_enabled('shadow') is True:
            submitted += self.__enqueue_shadow_probes(response_data, response_object)

        return submitted

    def __enqueue_shadow_probes(self, response_data, response_object):
        """Queue active shadow postfix probes for eligible success responses."""

        shadow_probe = getattr(self, '_Browser__shadow_probe', None)
        if shadow_probe is None:
            return 0

        try:
            status, request_url = response_data[0], response_data[1]
        except (TypeError, IndexError):
            return 0

        if status != 'success':
            return 0

        return shadow_probe.enqueue(request_url, response_object, status)

    def __emit_shadow_probe_progress(self, url, response_object, current, total):
        """Emit rotating progress for a completed non-matching shadow probe."""

        try:
            response_data = (
                'shadow-probe',
                str(url),
                self.__response._get_content_size(response_object),
                str(getattr(response_object, 'status', '-'))
            )
        except (TypeError, ValueError, AttributeError):
            response_data = ('shadow-probe', str(url), '-', '-')

        self.__emit_filtered_progress('shadow-probe', response_data, {
            'calibration_score': '{0}/{1}'.format(current, total)
        })
        return True

    def __handle_shadow_match(self, url, response_object, metadata):
        """Persist and render one confirmed shadow-copy finding."""

        finding = SnifferResult(
            bucket='shadow',
            url=str(url),
            code=str(getattr(response_object, 'status', '-')),
            size=self.__response._get_content_size(response_object),
            metadata=metadata,
        )

        self.__emit_sniffer_finding(finding, response_object=response_object)
        self.__catch_sniffer_finding(finding)
        return True

    def __drain_shadow_probes(self):
        """Drain active shadow probes before summary and reports are generated."""

        shadow_probe = getattr(self, '_Browser__shadow_probe', None)
        if shadow_probe is None:
            return True

        shadow_probe.drain()
        submitted = shadow_probe.submitted
        if submitted > 0:
            self.__result['total'].update({'shadow_probes': submitted})
        return True

    def __get_response_length(self, response):
        """Resolve response size in bytes for response filters."""

        try:
            if hasattr(response, 'headers') and response.headers.get('Content-Length') is not None:
                return int(response.headers.get('Content-Length'))
        except (TypeError, ValueError, AttributeError):
            pass

        try:
            return len(response.data)
        except AttributeError:
            return 0

    def __get_response_body(self, response):
        """Decode response body to text for text and regex filters."""

        try:
            return helper.decode(response.data)
        except AttributeError:
            return ''

    def __is_response_allowed(self, response, response_data):
        """Apply response filters without altering default behaviour when disabled."""

        if True is not self.__config.is_response_filtering:
            return True

        response_code = str(response_data[3])
        response_size = self.__get_response_length(response)

        include_status = set(self.__config.include_status)
        if len(include_status) > 0 and response_code not in include_status:
            return False

        exclude_status = set(self.__config.exclude_status)
        if response_code in exclude_status:
            return False

        if response_size in set(self.__config.exclude_size):
            return False

        for minimum, maximum in self.__config.exclude_size_range:
            if minimum <= response_size <= maximum:
                return False

        if self.__config.min_response_length is not None and response_size < self.__config.min_response_length:
            return False

        if self.__config.max_response_length is not None and response_size > self.__config.max_response_length:
            return False

        response_body = None

        def body():
            nonlocal response_body
            if response_body is None:
                response_body = self.__get_response_body(response)
            return response_body

        for needle in self.__config.match_text:
            if needle not in body():
                return False

        for needle in self.__config.exclude_text:
            if needle in body():
                return False

        if len(self.__config.match_regex) > 0 or len(self.__config.exclude_regex) > 0:
            return self.__apply_regex_filters(body())

        return True

    def __apply_regex_filters(self, response_body):
        """Apply regex-based response filters."""

        import re

        for pattern in self.__config.match_regex:
            if re.search(pattern, response_body) is None:
                return False

        for pattern in self.__config.exclude_regex:
            if re.search(pattern, response_body) is not None:
                return False

        return True

    def __should_expand_recursively(self, status, url, depth):
        """
        Decide whether the current response can be used for recursive expansion.

        :param str status: actual response code
        :param str url: current resolved url
        :param int depth: current recursion depth
        :return: bool
        """

        if True is not self.__config.is_recursive:
            return False

        if self.__config.scan != self.__config.DEFAULT_SCAN:
            return False

        if depth >= self.__config.recursive_depth:
            return False

        if str(status) not in self.__config.recursive_status:
            return False

        path = helper.parse_url(url).path or ''
        last_part = path.rstrip('/').rsplit('/', 1)[-1].lower()

        if '.' in last_part:
            extension = last_part.rsplit('.', 1)[-1]
            if extension in self.__config.recursive_exclude:
                return False

        return True

    def __build_recursive_url(self, base_url, suffix):
        """
        Build nested url for recursive scans.

        :param str base_url: parent url
        :param str suffix: child path suffix
        :return: str | None
        """

        suffix = str(suffix).strip().lstrip('/')
        if not suffix:
            return None

        parsed = helper.parse_url(base_url)
        base_path = (parsed.path or '').rstrip('/')

        if base_path:
            new_path = '{0}/{1}'.format(base_path, suffix)
        else:
            new_path = '/{0}'.format(suffix)

        return '{0}://{1}{2}'.format(parsed.scheme, parsed.netloc, new_path)

    def __enqueue_recursive_children(self, parent_url, depth):
        """
        Enqueue nested dictionary items under discovered parent path.

        :param str parent_url: current parent url
        :param int depth: current recursion depth
        :return: None
        """

        if depth >= self.__config.recursive_depth:
            return

        child_urls = []
        prefix = self.__config.prefix.strip('/')

        def loader(batch):
            for candidate in batch:
                suffix = helper.parse_url(candidate).path.lstrip('/')

                if prefix and suffix.startswith(prefix):
                    suffix = suffix[len(prefix):].lstrip('/')

                child_url = self.__build_recursive_url(parent_url, suffix)
                if child_url is None:
                    continue

                if child_url in self.__queued_recursive:
                    continue

                self.__queued_recursive.add(child_url)
                child_urls.append((child_url, depth + 1))

        self.__reader.get_lines(
            params={
                'host': self.__config.host,
                'port': self.__config.port,
                'scheme': self.__config.scheme
            },
            loader=loader
        )

        if child_urls:
            getattr(getattr(self, '_Browser__debug', None), 'debug_recursive_expansion', lambda *args, **kwargs: True)(parent_url, len(child_urls), depth + 1)
            self.__pool.extend_total_items(len(child_urls))
            for child_url, child_depth in child_urls:
                if self.__register_pending_request(child_url, child_depth):
                    self.__pool.add(self.__http_request, child_url, child_depth)

    def __is_ignored(self, url):
        """
        Check if the path will be ignored
        :param str url: received url
        :return: bool
        """

        path = helper.parse_url(url).path.strip("/")
        return path in self.__reader.get_ignored_list()

    def __is_subdomains_scan(self):
        """
        Return True when the active scan mode is subdomain enumeration.

        :return: bool
        """

        config = getattr(self, '_Browser__config', None)
        return getattr(config, 'scan', None) == getattr(config, 'SUBDOMAINS_SCAN', 'subdomains')

    def __shrink_planned_total_for_deduplicated_url(self):
        """
        Keep planned scan totals aligned when a duplicate subdomain candidate is dropped.

        :return: None
        """

        try:
            submitted = int(getattr(self.__pool, 'submitted_size', 0))
            planned = int(getattr(self.__pool, 'total_items_size', 0))
        except (TypeError, ValueError):
            return

        self.__pool.total_items_size = max(submitted, planned - 1)

    def __deduplicate_scan_url(self, url):
        """
        Skip duplicate subdomain candidates before they reach the HTTP queue.

        Directory scans intentionally keep their previous behavior.

        :param str url: candidate request URL
        :return: bool
        """

        if self.__is_subdomains_scan() is not True:
            return True

        key = str(url).strip()
        if key in self.__seen_scan_urls:
            self.__shrink_planned_total_for_deduplicated_url()
            return False

        self.__seen_scan_urls.add(key)
        return True

    def __emit_ignored_item_warning(self, url):
        """Emit an ignored-item warning without gluing it to rotating progress."""

        with self.__get_progress_output_lock():
            self.__finish_filtered_progress_line()
            tpl.warning(
                key='ignored_item',
                current='{0:0{l}d}'.format(0, l=len(str(abs(self.__reader.total_lines)))),
                total=self.__reader.total_lines,
                item=helper.parse_url(url).path
            )

    def _add_urls(self, urllist):
        """
        Add received urllist to threadpool
        :param dict urllist: read from dictionary
        :raise KeyboardInterrupt
        :return: None
        """

        self.__ensure_session_runtime_state()

        try:

            for url in urllist:
                if self.__deduplicate_scan_url(url) is not True:
                    continue

                if False is self.__is_ignored(url):
                    if self.__register_pending_request(url, 0):
                        self.__pool.add(self.__http_request, url, 0)
                else:
                    self.__catch_report_data('ignored', url)
                    self.__emit_ignored_item_warning(url)
            self.__pool.join()
        except (SystemExit, KeyboardInterrupt):
            raise KeyboardInterrupt

    def __emit_sniffer_finding(self, finding, response_object=None):
        """
        Emit runtime output for one independent sniffer finding.

        :param SnifferResult finding: sniffer finding to render
        :param object | None response_object: optional raw response object
        :return: bool
        """

        if not isinstance(finding, SnifferResult):
            return False

        self.__apply_sniffer_metadata(response_object, finding.metadata)

        debug_response_data = getattr(self.__response, 'debug_response_data', None)
        if not callable(debug_response_data):
            return False

        self.__clear_filtered_progress()
        debug_response_data(
            self.__sniffer_response_data(finding),
            request_url=str(finding.url),
            items_size=self.__pool.items_size,
            total_size=self.__pool.total_items_size,
            response=response_object,
        )
        return True

    def __catch_sniffer_finding(self, finding):
        """
        Persist one independent sniffer finding.

        :param SnifferResult finding: sniffer finding to persist
        :return: bool
        """

        if not isinstance(finding, SnifferResult):
            return False

        response_data = self.__sniffer_response_data(finding)
        self.__catch_report_data(
            response_data[0],
            response_data[1],
            response_data[2],
            response_data[3],
            metadata=finding.metadata,
        )
        return True

    @staticmethod
    def __sniffer_response_data(finding):
        """
        Convert one sniffer finding to the legacy response tuple shape.

        :param SnifferResult finding: sniffer finding
        :return: tuple
        """

        return (
            finding.bucket,
            str(finding.url),
            '0B' if finding.size is None else str(finding.size),
            '-' if finding.code is None else str(finding.code),
        )

    @staticmethod
    def __apply_sniffer_metadata(response_object, metadata):
        """
        Attach known sniffer metadata to a response object for existing debug renderers.

        :param object | None response_object: raw response object
        :param dict | None metadata: sniffer metadata
        :return: bool
        """

        if response_object is None or not isinstance(metadata, dict):
            return False

        mappings = (
            ('stacktrace_detection', 'opendoor_stacktrace_detection'),
            ('secret_detection', 'opendoor_secret_detection'),
            ('shadow_detection', 'opendoor_shadow_detection'),
            ('openredirect_detection', 'opendoor_openredirect_detection'),
        )

        applied = False
        for source_key, target_key in mappings:
            if not isinstance(metadata.get(source_key), dict):
                continue
            try:
                setattr(response_object, target_key, dict(metadata.get(source_key)))
                applied = True
            except (AttributeError, TypeError):
                continue

        return applied

    def __catch_report_data(self, status, url, size='0B', code='-', metadata=None):
        """
        Add to basket report pool.
        :param str status: response status
        :param str url: request url
        :param str size: response content size
        :param str code: actual response code
        :param dict|None metadata: extra report metadata
        :return: None
        """

        if 'report_items' not in self.__result:
            self.__result['report_items'] = helper.list()

        item = {'url': url, 'size': size, 'code': str(code)}

        if isinstance(metadata, dict):
            if metadata.get('name'):
                item['waf'] = metadata.get('name')
            if metadata.get('confidence') is not None:
                item['waf_confidence'] = int(metadata.get('confidence'))
            if metadata.get('signals'):
                item['waf_signals'] = list(metadata.get('signals'))
            if metadata.get('calibration_score') is not None:
                item['calibration_score'] = float(metadata.get('calibration_score'))
            if metadata.get('calibration_reason'):
                item['calibration_reason'] = metadata.get('calibration_reason')
            if metadata.get('dns_wildcard_host'):
                item['dns_wildcard_host'] = metadata.get('dns_wildcard_host')
            if metadata.get('dns_wildcard_addresses'):
                item['dns_wildcard_addresses'] = list(metadata.get('dns_wildcard_addresses'))
            if metadata.get('bypass'):
                item['bypass'] = metadata.get('bypass')
            if metadata.get('bypass_profile'):
                item['bypass_profile'] = metadata.get('bypass_profile')
            if metadata.get('bypass_header'):
                item['bypass_header'] = metadata.get('bypass_header')
            if metadata.get('bypass_value'):
                item['bypass_value'] = metadata.get('bypass_value')
            if metadata.get('bypass_variant'):
                item['bypass_variant'] = metadata.get('bypass_variant')
            if metadata.get('bypass_url'):
                item['bypass_url'] = metadata.get('bypass_url')
            if metadata.get('bypass_from_status'):
                item['bypass_from_status'] = metadata.get('bypass_from_status')
            if metadata.get('bypass_to_status'):
                item['bypass_to_status'] = metadata.get('bypass_to_status')
            if metadata.get('bypass_from_code') is not None:
                item['bypass_from_code'] = str(metadata.get('bypass_from_code'))
            if metadata.get('bypass_to_code') is not None:
                item['bypass_to_code'] = str(metadata.get('bypass_to_code'))
            if metadata.get('bypass_score') is not None:
                item['bypass_score'] = int(metadata.get('bypass_score'))
            if metadata.get('bypass_reasons'):
                item['bypass_reasons'] = list(metadata.get('bypass_reasons'))
            if isinstance(metadata.get('stacktrace_detection'), dict):
                item['stacktrace_detection'] = dict(metadata.get('stacktrace_detection'))
            if isinstance(metadata.get('secret_detection'), dict):
                item['secret_detection'] = dict(metadata.get('secret_detection'))
            if isinstance(metadata.get('shadow_detection'), dict):
                item['shadow_detection'] = dict(metadata.get('shadow_detection'))
            if isinstance(metadata.get('openredirect_detection'), dict):
                item['openredirect_detection'] = dict(metadata.get('openredirect_detection'))

        self.__result['total'].update((status,))
        self.__result['items'][status] += [url]
        self.__result['report_items'][status] += [item]

    @property
    def result(self):
        """Return a defensive copy of the current scan result."""

        self.__ensure_session_runtime_state()
        return copy.deepcopy(self.__result)

    def done(self):
        """
        Scan finish action
        :raise BrowserError
        :return: None
        """

        self.__ensure_session_runtime_state()
        self.__drain_shadow_probes()

        self.__result['total'].update({"items": self.__pool.total_items_size})
        self.__result['total'].update({"workers": self.__pool.workers_size})

        if 0 == self.__pool.size:

            try:
                self.__warn_if_scan_finished_early()
                self.__save_session(reason='finish', force=True)

                for rtype in self.__config.reports:
                    report = Reporter.load(rtype, self.__config.host, self.__result)
                    report.process()
            except ReporterError as error:
                raise BrowserError(error)
        else:
            pass

    def __task_key(self, url, depth):
        """Build stable request key for session tracking."""

        return '{0}::{1}'.format(int(depth), str(url))

    def __mark_session_dirty(self):
        """Mark current logical scan state as changed."""

        self.__session_dirty = True

    def __register_pending_request(self, url, depth):
        """Register a queued request in persistent state."""

        self.__ensure_session_runtime_state()

        key = self.__task_key(url, depth)
        if key in self.__completed_requests:
            return False
        if key in self.__pending_requests:
            return False

        self.__pending_requests[key] = {'url': url, 'depth': int(depth)}
        self.__mark_session_dirty()
        return True

    def __complete_request(self, url, depth):
        """Finalize a processed request in persistent state."""

        self.__ensure_session_runtime_state()

        key = self.__task_key(url, depth)
        self.__pending_requests.pop(key, None)
        self.__completed_requests.add(key)
        self.__mark_session_dirty()

    def __warn_filtered_progress_mode(self):
        """
        Warn when scan progress can look sparse because filtering/reporting is enabled.

        :return: None
        """

        if True is not getattr(self.__config, 'is_response_filtering', False) \
                and True is not getattr(self.__config, 'is_auto_calibrate', False) \
                and True is not getattr(self.__config, 'is_sniff', False):
            return

        tpl.warning(key='filtered_progress_notice')

    def __build_session_snapshot(self, reason='periodic'):
        """Build a serializable checkpoint snapshot."""

        self.__ensure_session_runtime_state()

        return {
            'createdAt': self.__session_snapshot.get('createdAt') if isinstance(self.__session_snapshot, dict) else SessionManager.now(),
            'updatedAt': SessionManager.now(),
            'params': self.__export_session_params(),
            'targets': self.__export_targets(),
            'pending': list(self.__pending_requests.values()),
            'seen': sorted(self.__completed_requests),
            'queuedRecursive': sorted(self.__queued_recursive),
            'visitedRecursive': sorted(self.__visited_recursive),
            'result': copy.deepcopy(self.__result),
            'stats': {
                'processed': self.__processed_offset + self.__pool.items_size,
                'total_items': self.__pool.total_items_size,
            },
            'checkpointReason': reason,
            'calibration': self.__calibration.to_dict() if self.__calibration is not None else None,
            'wafSafeMode': {
                'active': self.__waf_safe_active,
                'vendor': self.__waf_safe_vendor,
                'confidence': self.__waf_safe_confidence,
                'delay': self.__waf_safe_delay,
                'recoveryCount': self.__waf_safe_recovery_count,
                'blockEvents': list(self.__waf_safe_block_events),
            },
        }

    def __export_session_params(self):
        """Export filtered params needed to resume the scan."""

        params = {
            'scan': self.__config.scan,
            'scheme': self.__config.scheme,
            'ssl': self.__config.is_ssl,
            'host': self.__config.host,
            'port': self.__config.port,
            'proxy': self.__config.proxy if self.__config.proxy else None,
            'header': self.__config.headers if len(self.__config.headers) > 0 else None,
            'cookie': self.__config.cookies if len(self.__config.cookies) > 0 else None,
            'raw_request': self.__config.raw_request,
            'request_body': self.__config.request_body,
            'accept_cookies': self.__config.accept_cookies,
            'keep_alive': self.__config.keep_alive,
            'fingerprint': getattr(self.__config, 'is_fingerprint', False),
            'waf_detect': getattr(self.__config, 'is_waf_detect', False),
            'waf_safe_mode': getattr(self.__config, 'is_waf_safe_mode', False),
            'wordlist': getattr(self.__config, 'wordlist', None),
            'reports': ','.join(self.__config.reports),
            'reports_dir': getattr(self.__config, 'reports_dir', None),
            'random_agent': self.__config.is_random_user_agent,
            'random_list': self.__config.is_random_list,
            'prefix': getattr(self.__config, 'prefix', ''),
            'extensions': ','.join(self.__config.extensions) if self.__config.extensions else None,
            'ignore_extensions': ','.join(self.__config.ignore_extensions) if self.__config.ignore_extensions else None,
            'recursive': self.__config.is_recursive,
            'recursive_depth': self.__config.recursive_depth,
            'recursive_status': ','.join(self.__config.recursive_status),
            'recursive_exclude': ','.join(self.__config.recursive_exclude),
            'sniff': ','.join(self.__config.sniffers) if self.__config.sniffers else None,
            'include_status': ','.join(self.__config.include_status) if self.__config.include_status else None,
            'exclude_status': ','.join(self.__config.exclude_status) if self.__config.exclude_status else None,
            'exclude_size': ','.join([str(i) for i in self.__config.exclude_size]) if self.__config.exclude_size else None,
            'exclude_size_range': ','.join(['{0}-{1}'.format(a, b) for a, b in self.__config.exclude_size_range]) if self.__config.exclude_size_range else None,
            'match_text': self.__config.match_text if self.__config.match_text else None,
            'exclude_text': self.__config.exclude_text if self.__config.exclude_text else None,
            'match_regex': self.__config.match_regex if self.__config.match_regex else None,
            'exclude_regex': self.__config.exclude_regex if self.__config.exclude_regex else None,
            'min_response_length': self.__config.min_response_length,
            'max_response_length': self.__config.max_response_length,
            'threads': self.__config.threads,
            'delay': self.__config.delay,
            'timeout': self.__config.timeout,
            'retries': self.__config.retries,
            'debug': self.__config.debug,
            'proxy_pool': self.__config.is_builtin_proxy_pool,
            'proxy_list': self.__config.proxy_list if self.__config.is_external_proxy_list else None,
            'method': self.__config.requested_method,
            'auto_calibrate': getattr(self.__config, 'is_auto_calibrate', False),
            'calibration_samples': getattr(self.__config, 'calibration_samples', None),
            'calibration_threshold': getattr(self.__config, 'calibration_threshold', None),
            'header_bypass': getattr(self.__config, 'is_header_bypass', False),
            'header_bypass_profile': getattr(self.__config, 'header_bypass_profile', None)
            if getattr(self.__config, 'is_header_bypass', False) is True else None,
            'header_bypass_headers': ','.join(getattr(self.__config, 'header_bypass_headers', []))
            if getattr(self.__config, 'is_header_bypass', False) is True else None,
            'header_bypass_ips': ','.join(getattr(self.__config, 'header_bypass_ips', []))
            if getattr(self.__config, 'is_header_bypass', False) is True else None,
            'header_bypass_status': ','.join([
                str(status) for status in getattr(self.__config, 'header_bypass_status', [])
            ]) if getattr(self.__config, 'is_header_bypass', False) is True else None,
            'header_bypass_limit': getattr(self.__config, 'header_bypass_limit', None)
            if getattr(self.__config, 'is_header_bypass', False) is True else None,
            'session_save': getattr(self.__config, 'session_save', None),
            'session_autosave_sec': getattr(self.__config, 'session_autosave_sec', None),
            'session_autosave_items': getattr(self.__config, 'session_autosave_items', None),
        }

        return {key: value for key, value in params.items() if value is not None}

    def __export_targets(self):
        """Export resolved session targets."""

        targets = []
        if self.__config.host:
            target = {
                'host': self.__config.host,
                'scheme': self.__config.scheme,
                'ssl': self.__config.is_ssl,
            }
            if self.__config.port is not None:
                target['port'] = self.__config.port
            targets.append(target)
        return targets

    def __restore_session_state(self, snapshot):
        """Hydrate browser state from loaded checkpoint."""

        self.__session_snapshot = snapshot
        self.__result = snapshot.get('result') or {'total': helper.counter(), 'items': helper.list(), 'report_items': helper.list()}
        if 'report_items' not in self.__result:
            self.__result['report_items'] = helper.list()

        self.__visited_recursive = set(snapshot.get('visitedRecursive', []))
        self.__queued_recursive = set(snapshot.get('queuedRecursive', []))
        self.__completed_requests = set(snapshot.get('seen', []))
        self.__pending_requests = {}
        self.__seen_scan_urls = {
            str(item).split('::', 1)[1]
            for item in self.__completed_requests
            if '::' in str(item)
        }

        for item in snapshot.get('pending', []):
            self.__pending_requests[self.__task_key(item.get('url'), item.get('depth', 0))] = {
                'url': item.get('url'),
                'depth': int(item.get('depth', 0))
            }
            if item.get('url') is not None:
                self.__seen_scan_urls.add(str(item.get('url')))

        self.__processed_offset = int(snapshot.get('stats', {}).get('processed', 0))
        saved_total = int(snapshot.get('stats', {}).get('total_items', self.__pool.total_items_size))
        if saved_total > self.__pool.total_items_size:
            self.__pool.total_items_size = saved_total

        waf_safe = snapshot.get('wafSafeMode') or {}
        self.__waf_safe_active = bool(waf_safe.get('active', False))
        self.__waf_safe_vendor = waf_safe.get('vendor')
        self.__waf_safe_confidence = waf_safe.get('confidence')
        self.__waf_safe_delay = float(waf_safe.get('delay', self.WAF_SAFE_MIN_DELAY))
        self.__waf_safe_recovery_count = int(waf_safe.get('recoveryCount', 0))
        self.__waf_safe_block_events = [float(item) for item in waf_safe.get('blockEvents', [])]
        self.__waf_safe_next_at = 0.0
        self.__calibration = Calibration.from_dict(snapshot.get('calibration'))
        self.__session_dirty = False

    def __save_session(self, reason='periodic', force=False):
        """Persist session snapshot if configured and needed."""

        self.__ensure_session_runtime_state()

        if True is not getattr(self.__config, 'is_session_enabled', False):
            return

        if self.__session is None:
            return

        processed = self.__processed_offset + self.__pool.items_size
        if True is not self.__session.should_save(self.__session_dirty, processed, force=force):
            return

        snapshot = self.__build_session_snapshot(reason=reason)
        self.__session.save(snapshot)
        self.__session_dirty = False
        tpl.info(msg='Session checkpoint saved: {0}'.format(self.__session.path))

    def __resume_pending_requests(self):
        """Re-enqueue restored pending requests."""

        self.__ensure_session_runtime_state()

        if len(self.__pending_requests) <= 0:
            return

        tpl.info(msg='Restoring {0} pending requests from session checkpoint ...'.format(len(self.__pending_requests)))

        if self.__pool.total_items_size < (self.__processed_offset + len(self.__pending_requests)):
            self.__pool.total_items_size = self.__processed_offset + len(self.__pending_requests)

        for item in list(self.__pending_requests.values()):
            self.__pool.add(self.__http_request, item['url'], item['depth'])

    def __finalize_processed_request(self, url, depth):
        """Mark request as processed and maybe save session."""

        self.__ensure_session_runtime_state()

        if True is not getattr(self.__config, 'is_session_enabled', False):
            return

        with self.__session_lock:
            self.__complete_request(url, depth)
            self.__save_session(reason='items', force=False)

    def __ensure_session_runtime_state(self):
        """
        Lazily initialize session-related runtime state.

        This keeps legacy tests and non-session runs fully backward compatible,
        especially when Browser is created through __new__() or Config is mocked
        by SimpleNamespace without session-specific properties.

        :return: None
        """

        if not hasattr(self, '_Browser__session_lock'):
            self.__session_lock = threading.RLock()

        if not hasattr(self, '_Browser__session'):
            self.__session = None

        if not hasattr(self, '_Browser__session_dirty'):
            self.__session_dirty = False

        if not hasattr(self, '_Browser__completed_requests'):
            self.__completed_requests = set()

        if not hasattr(self, '_Browser__pending_requests'):
            self.__pending_requests = {}

        if not hasattr(self, '_Browser__seen_scan_urls'):
            self.__seen_scan_urls = set()

        if not hasattr(self, '_Browser__processed_offset'):
            self.__processed_offset = 0

        if not hasattr(self, '_Browser__session_snapshot'):
            self.__session_snapshot = None

        if not hasattr(self, '_Browser__visited_recursive'):
            self.__visited_recursive = set()

        if not hasattr(self, '_Browser__queued_recursive'):
            self.__queued_recursive = set()

        if not hasattr(self, '_Browser__result'):
            self.__result = {
                'total': helper.counter(),
                'items': helper.list(),
                'report_items': helper.list()
            }
        if not hasattr(self, '_Browser__waf_safe_lock'):
            self.__waf_safe_lock = threading.RLock()

        if not hasattr(self, '_Browser__progress_output_lock'):
            self.__progress_output_lock = threading.RLock()

        if not hasattr(self, '_Browser__waf_safe_active'):
            self.__waf_safe_active = False

        if not hasattr(self, '_Browser__waf_safe_next_at'):
            self.__waf_safe_next_at = 0.0

        if not hasattr(self, '_Browser__waf_safe_delay'):
            self.__waf_safe_delay = self.WAF_SAFE_MIN_DELAY

        if not hasattr(self, '_Browser__waf_safe_recovery_count'):
            self.__waf_safe_recovery_count = 0

        if not hasattr(self, '_Browser__waf_safe_vendor'):
            self.__waf_safe_vendor = None

        if not hasattr(self, '_Browser__waf_safe_confidence'):
            self.__waf_safe_confidence = None

        if not hasattr(self, '_Browser__waf_safe_block_events'):
            self.__waf_safe_block_events = []

        if not hasattr(self, '_Browser__calibration'):
            self.__calibration = None

        if not hasattr(self, '_Browser__shared_cookie_header'):
            self.__shared_cookie_header = None

        if not hasattr(self, '_Browser__header_bypass') or self.__header_bypass is None:
            if hasattr(self, '_Browser__config'):
                self.__header_bypass = HeaderBypassProbe(self.__config)
            else:
                self.__header_bypass = None
