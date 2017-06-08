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

    Development Team: Stanislav WEB
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
            self.__result = {'total': {}, 'items': {}}
            self.__reader = Reader(browser_config={
                'list': self.__config.scan,
                'torlist': self.__config.torlist,
                'use_random': self.__config.is_random_list,
                'use_extensions': self.__config.is_extension_filter,
                'is_external_wordlist': self.__config.is_external_wordlist,
                'is_standalone_proxy': self.__config.is_standalone_proxy,
                'is_external_torlist': self.__config.is_external_torlist,
                'prefix': self.__config.prefix
            })

            if True is self.__config.is_external_reports_dir:
                Reporter.external_directory = self.__config.reports_dir
                
            if True is self.__config.is_extension_filter and self.__config.scan == self.__config.DEFAULT_SCAN:
                self.__reader.filter_by_extension(target=self.__config.scan,
                                                  output='extensionlist',
                                                  extensions=self.__config.extensions
                                                  )
            self.__reader.count_total_lines()

            Filter.__init__(self, self.__config, self.__reader.total_lines)

            self.__pool = ThreadPool(num_threads=self.__config.threads, total_items=self.__reader.total_lines,
                                     timeout=self.__config.delay)

            self.__result = {'total': helper.counter(), 'items': helper.list()}

            self.__response = response(config=self.__config, debug=self.__debug, tpl=tpl)

        except ReaderError as error:
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

        try:  # beginning scan process
            if True is self.__config.is_random_list:
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
                    loader=getattr(self, '_add_urls'.format()))

        except (ProxyRequestError, HttpRequestError, HttpsRequestError, ReaderError) as error:
            raise BrowserError(error)

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

    def __http_request(self, url):
        """
        Make HTTP request
        :param str url: received url
        :return: None
        """

        try:
            resp = self.__client.request(url)

            response_data = self.__response.handle(resp, request_url=url,
                                                   items_size=self.__pool.items_size,
                                                   total_size=self.__pool.total_items_size,
                                                   ignore_list=self.__reader.get_ignored_list()
                                                   )
            if None is response_data:
                self.__catch_report_data('ignored', url)
            else:
                self.__catch_report_data(response_data[0], response_data[1])

        except (HttpRequestError, HttpsRequestError, ProxyRequestError, ResponseError) as error:
            raise BrowserError(error)

    def __is_ignored(self, url):
        """
        Check if path will be ignored
        :param str url: recieved url
        :return: bool
        """

        path = helper.parse_url(url).path.strip("/")
        return path in self.__reader.get_ignored_list()

    def _add_urls(self, urllist):
        """
        Add recieved urllist to threadpool
        :param dict urllist: read from dictionary
        :raise KeyboardInterrupt
        :return: None
        """

        try:

            for url in urllist:
                if False is self.__is_ignored(url):
                    self.__pool.add(self.__http_request, url)
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

    def __catch_report_data(self, status, url):
        """
        Add to basket report pool
        :param str status: response status
        :param url: request url
        :return: None
        """

        self.__result['total'].update((status,))
        self.__result['items'][status] += [url]

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
