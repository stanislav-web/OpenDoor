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

    Development Team: Brain Storm Team
"""

import copy
import threading
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
from .exceptions import BrowserError
from .fingerprint import Fingerprint
from .filter import Filter
from .threadpool import ThreadPool


class Browser(Filter):
    """ Browser class """

    def __init__(self, params):
        """
        Browser constructor
        :param dict params: filtered input params
        :raise BrowserError
        """

        try:
            self.__client = None
            self.__config = Config(params)
            self.__debug = Debug(self.__config)
            self.__session_lock = threading.RLock()
            self.__session = None
            self.__session_dirty = False
            self.__completed_requests = set()
            self.__pending_requests = {}
            self.__processed_offset = 0
            self.__session_snapshot = params.get('session_snapshot')
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
                'torlist': self.__config.torlist,
                'use_random': self.__config.is_random_list,
                'use_extensions': self.__config.is_extension_filter,
                'use_ignore_extensions': self.__config.is_ignore_extension_filter,
                'is_external_wordlist': self.__config.is_external_wordlist,
                'wordlist': self.__config.wordlist,
                'is_standalone_proxy': self.__config.is_standalone_proxy,
                'is_external_torlist': self.__config.is_external_torlist,
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

            tpl.info(key='scanning', host=self.__config.host)

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

            result = Fingerprint(config=self.__config, client=self.__client).detect()
            self.__result['fingerprint'] = result

            tpl.debug(
                msg='Fingerprint result: {category}/{name} ({confidence}%)'.format(
                    category=result.get('category', 'custom'),
                    name=result.get('name', 'Unknown custom stack'),
                    confidence=result.get('confidence', 0),
                )
            )

            if result.get('signals'):
                evidence = ', '.join([signal.get('value', '') for signal in result.get('signals', [])[:4]])
                tpl.debug(msg='Fingerprint evidence: {0}'.format(evidence))

            return result

        except (ProxyRequestError, HttpRequestError, HttpsRequestError, AttributeError, TypeError, ValueError) as error:
            tpl.warning(msg='Fingerprint skipped: {0}'.format(error))
            result = dict(Fingerprint.DEFAULT_RESULT)
            self.__result['fingerprint'] = result
            return result

    def __start_request_provider(self):
        """
        Start selected request provider

        :return: None
        """

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

    def __http_request(self, url, depth=0):
        """
        Make HTTP request
        :param str url: received url
        :param int depth: current recursion depth
        :return: None
        """

        self.__ensure_session_runtime_state()

        try:
            resp = self.__client.request(url)

            response_data = self.__response.handle(
                resp,
                request_url=url,
                items_size=self.__pool.items_size,
                total_size=self.__pool.total_items_size,
                ignore_list=self.__reader.get_ignored_list()
            )

            if None is response_data:
                self.__catch_report_data('ignored', url)
            elif False is self.__is_response_allowed(resp, response_data):
                self.__catch_report_data('ignored', response_data[1], response_data[2], response_data[3])
            else:
                self.__catch_report_data(
                    response_data[0],
                    response_data[1],
                    response_data[2],
                    response_data[3]
                )

                if self.__should_expand_recursively(response_data[3], response_data[1], depth):
                    if response_data[1] not in self.__visited_recursive:
                        self.__visited_recursive.add(response_data[1])
                        self.__enqueue_recursive_children(response_data[1], depth)

        except (HttpRequestError, HttpsRequestError, ProxyRequestError, ResponseError) as error:
            raise BrowserError(error)
        finally:
            self.__finalize_processed_request(url, depth)

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
            tpl.debug(
                msg='Recursive expansion [{0}] -> +{1} urls (next depth: {2})'.format(
                    parent_url,
                    len(child_urls),
                    depth + 1
                )
            )
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
                if False is self.__is_ignored(url):
                    if self.__register_pending_request(url, 0):
                        self.__pool.add(self.__http_request, url, 0)
                else:
                    self.__catch_report_data('ignored', url)
                    tpl.warning(
                        key='ignored_item',
                        current='{0:0{l}d}'.format(0, l=len(str(abs(self.__reader.total_lines)))),
                        total=self.__reader.total_lines,
                        item=helper.parse_url(url).path
                    )
            self.__pool.join()
        except (SystemExit, KeyboardInterrupt):
            raise KeyboardInterrupt

    def __catch_report_data(self, status, url, size='0B', code='-'):
        """
        Add to basket report pool
        :param str status: response status
        :param url: request url
        :param str size: response content size
        :param str code: actual response code
        :return: None
        """

        if 'report_items' not in self.__result:
            self.__result['report_items'] = helper.list()

        self.__result['total'].update((status,))
        self.__result['items'][status] += [url]
        self.__result['report_items'][status] += [{'url': url, 'size': size, 'code': str(code)}]

    def done(self):
        """
        Scan finish action
        :raise BrowserError
        :return: None
        """

        self.__ensure_session_runtime_state()

        self.__result['total'].update({"items": self.__pool.total_items_size})
        self.__result['total'].update({"workers": self.__pool.workers_size})

        if 0 == self.__pool.size:

            try:
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
            'tor': self.__config.is_internal_torlist,
            'torlist': self.__config.torlist if self.__config.is_external_torlist else None,
            'method': self.__config.requested_method,
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

        for item in snapshot.get('pending', []):
            self.__pending_requests[self.__task_key(item.get('url'), item.get('depth', 0))] = {
                'url': item.get('url'),
                'depth': int(item.get('depth', 0))
            }

        self.__processed_offset = int(snapshot.get('stats', {}).get('processed', 0))
        saved_total = int(snapshot.get('stats', {}).get('total_items', self.__pool.total_items_size))
        if saved_total > self.__pool.total_items_size:
            self.__pool.total_items_size = saved_total

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