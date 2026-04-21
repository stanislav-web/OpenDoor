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
# noinspection PyPep8Naming
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

            if True is self.__pool.is_started:
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

    def fingerprint(self):
        """
        Run heuristic technology fingerprinting before the main scan.

        :return: dict | None
        """

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

        try:

            for url in urllist:
                if False is self.__is_ignored(url):
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

        self.__result['total'].update({"items": self.__pool.total_items_size})
        self.__result['total'].update({"workers": self.__pool.workers_size})

        if 0 == self.__pool.size:

            try:
                for rtype in self.__config.reports:
                    report = Reporter.load(rtype, self.__config.host, self.__result)
                    report.process()
            except ReporterError as error:
                raise BrowserError(error)
        else:
            pass
