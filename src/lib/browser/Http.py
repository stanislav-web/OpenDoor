# -*- coding: utf-8 -*-

"""Http class"""

import collections
import exceptions
import httplib
import logging
import multiprocessing
import re
import socks
import urllib3
from urlparse import urlparse

import sys
import threadpool
import time
from src.lib.logger.logger import Logger as Log
from .FileReader import FileReader
from .Message import Message

from src.core.helper.Formatter import Formatter
from src.core.helper.Progress import Progress
from src.lib.browser.HttpConfig import HttpConfig as config


class Http:
    """Http class"""

    def __init__(self):
        """Init constructor"""

        self.message = Message()
        self.reader = FileReader()
        self.cpu_cnt = multiprocessing.cpu_count()
        self.counter = collections.Counter()
        self.result = collections.defaultdict(list)
        self.exclusions = []
        self.result.default_factory

    def get(self, host, params=()):
        """Get metadata by url"""

        self.__parse_params(params)
        self.__is_server_online(host, self.port)
        self.__disable_verbose()
        self.urls = self.__get_urls(host)
        self.exclusions = self.__get_exclusions()
        response = {}

        try:
            if 2 is self.debug:
                httplib.HTTPConnection.debuglevel = self.debug

            if hasattr(urllib3, 'disable_warnings'):
                urllib3.disable_warnings()

            pool = threadpool.ThreadPool(self.threads)
            requests = threadpool.makeRequests(self.request, self.urls)
            for req in requests:
                pool.putRequest(req)
            pool.wait()
        except exceptions.AttributeError as e:
            sys.exit(Log.error(e.message))
        except KeyboardInterrupt:
            sys.exit("{0}".format(Log.warning(self.message.get('abort'))))

        self.counter['total'] = self.urls.__len__()
        self.counter['pools'] = pool.workers.__len__()

        response['count'] = self.counter
        response['result'] = self.result

        return response

    def request(self, url):

        """Request handler"""
        if True == self.proxy:
            proxyserver = self.reader.get_random_proxy()
            try:
                conn = urllib3.proxy_from_url(proxyserver, maxsize=10, block=True, timeout=self.rest)
            except urllib3.exceptions.ProxySchemeUnknown as e:
                sys.stdout.write(Log.warning('{} : {}'.format(e.message, proxyserver)))
        else:
            try:

                conn = urllib3.connection_from_url(url, maxsize=10, block=True,
                                                   timeout=self.rest)
            except TypeError as e:
                sys.exit(Log.error(e.message))

        headers = {
            'accept-encoding': 'gzip, deflate, sdch',
            'accept-language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4,uk;q=0.2,es;q=0.2',
            'cache-control': 'no-cache',
            'user-agent': self.reader.get_random_user_agent()
        }
        try:
            response = conn.request(config.DEFAULT_HTTP_METHOD, url, headers=headers, redirect=False)
        except (urllib3.exceptions.HostChangedError,
                urllib3.exceptions.ReadTimeoutError,
                urllib3.exceptions.ProxyError,
                ) as e:
            response = None
            self.iterator = Progress.line(url + ' -> ' + e.message, self.urls.__len__(), 'warning', self.iterator)
        except urllib3.exceptions.ConnectTimeoutError:
            sys.stdout.write(Log.warning(self.message.get('timeout').format(url)))
            pass
        except urllib3.exceptions.MaxRetryError:
            pass
        except urllib3.exceptions.NewConnectionError as e:
            sys.exit(Log.error(e.message))
        except exceptions.AttributeError as e:
            sys.exit(Log.error(e.message))
        except TypeError as e:
            sys.exit(Log.error(e.message))

        try:
            time.sleep(self.delay)
            return self.response(response, url)
        except exceptions.UnboundLocalError as e:
            sys.stdout.write(Log.warning(self.message.get('unresponsible').format(url)))
            pass

    def response(self, response, url):
        """Response handler"""

        if True == self.__is_excluded(url):

            sys.stdout.write(Log.info(self.message.get('excluded').format(url)))
            self.iterator = Progress.line(url, self.urls.__len__(), 'warning', self.iterator, False)
            self.counter.update(("excluded",))
            return
        else:
            if hasattr(response, 'status'):
                if response.status in config.DEFAULT_HTTP_FAILED_STATUSES:
                    show = True if self.debug in [1,2] else False
                    self.iterator = Progress().line(url, self.urls.__len__(), 'error', self.iterator, show)
                    self.counter.update(("failed",))
                elif response.status in config.DEFAULT_HTTP_SUCCESS_STATUSES:
                    if 'Content-Length' in response.headers:
                        if config.DEFAULT_SOURCE_DETECT_MIN_SIZE <= int(response.headers['Content-Length']):
                            size = Formatter.get_readable_size(response.headers['Content-Length'])
                            message = self.message.get('file_detected').format(url, size)
                            self.iterator = Progress.line(message, self.urls.__len__(), 'success', self.iterator)
                            self.counter.update(("sources",))
                        else:
                            self.iterator = Progress.line(url, self.urls.__len__(), 'success', self.iterator)
                            self.counter.update(("success",))
                    else:
                        self.iterator = Progress.line(url, self.urls.__len__(), 'success', self.iterator)
                        self.counter.update(("success",))
                elif response.status in config.DEFAULT_HTTP_UNRESOLVED_STATUSES:
                    self.iterator = Progress.line(url, self.urls.__len__(), 'warning', self.iterator)
                    self.counter.update(("possible",))
                elif response.status in config.DEFAULT_HTTP_REDIRECT_STATUSES:
                    self.iterator = Progress.line(url, self.urls.__len__(), 'warning', self.iterator)
                    self.counter.update(("redirects",))
                    self.__handle_redirect_url(url, response)
                elif response.status in config.DEFAULT_HTTP_BAD_REQUEST_STATUSES:
                    self.iterator = Progress.line(url, self.urls.__len__(), 'warning', self.iterator)
                    self.counter.update(("bad requests",))
                    self.__handle_redirect_url(url, response)
                else:
                    self.counter.update(("undefined",))
                    return
                self.result[response.status].append(url)

            else:
                return

    @staticmethod
    def __disable_verbose():
        """ Disbale verbose warnings info"""

        logging.getLogger("urllib3").setLevel('ERROR')

    def __is_server_online(self, host, port):
        """ Check if server is online"""

        s = socks.socket()

        try:
            ip = socks.gethostbyname(host)

            s.settimeout(config.DEFAULT_REQUEST_TIMEOUT)
            s.connect((host, port))

            sys.stdout.write(Log.info(self.message.get('online').format(host, ip, port)))
            sys.stdout.write(Log.info(self.message.get('scanning').format(host)))
        except (socks.gaierror, socks.timeout) as e:
            sys.stdout.exit(Log.error(self.message.get('offline').format(e)))
        finally:
            s.close()

    def __handle_redirect_url(self, url, response):
        """ Handle redirect url """

        try:
            location = response.get_redirect_location()

            if False != location:

                matches = re.search("(?P<url>https?://[^\s]+)", location)
                if None != matches.group("url"):
                    redirect_url = matches.group("url")
                else:
                    urlp = urlparse(url)
                    redirect_url = urlp.scheme + '://' + urlp.netloc + location

                sys.stdout.write(Log.info(self.message.get('redirect').format(url, redirect_url)))
                http = urllib3.PoolManager()

            try:
                if redirect_url:
                    response_red = http.request(config.DEFAULT_HTTP_METHOD, redirect_url, redirect=True)
                    time.sleep(self.delay)
                    self.response(response_red, redirect_url)
            except urllib3.exceptions.MaxRetryError:
                pass
        except exceptions.AttributeError:
            pass

    def __get_urls(self, host):
        """Get urls"""

        lines = self.reader.get_file_data(self.check)

        if config.DEFAULT_CHECK == self.check:
            urls = self.__urls_resolves(host, self.port, lines)
        else:
            urls = self.__subdomains_resolves(host, lines)
        return urls

    def __get_exclusions(self):
        """Get exclusions for redirect pages"""

        exlusionsList = []
        if not self.exclusions:
            lines = self.reader.get_file_data('excludes')
            for item in lines:
                item = item.replace("\n", "")
                if "/" == item[0]:
                    item = item.strip('/')
                exlusionsList.append(item)
        return exlusionsList

    def __is_excluded(self, url):
        """Check if url has been excluded"""

        path = urlparse(url).path.strip("/")

        if path in self.exclusions:
            return True
        else:
            return False

    def __urls_resolves(self, host, port, directories):
        """Urls path resolve"""

        resolved_dirs = []
        for path in directories:
            path = path.replace("\n", "")
            if "/" != path[0]:
                path = '/' + path

            if config.DEFAULT_HTTP_PORT != port:
                resolved_dirs.append(self.scheme + host + ":" + str(port) + path)
            else:
                resolved_dirs.append(self.scheme + host + path)
        return resolved_dirs

    def __subdomains_resolves(self, host, subdomains):
        """Subdomains path resolve"""

        resolve_subs = []
        for sub in subdomains:
            sub = sub.replace("\n", "")
            resolve_subs.append(self.scheme + sub + "." + host)
        return resolve_subs

    def __parse_params(self, params):
        """Parse additional params"""

        self.threads = params.get('threads', config.DEFAULT_THREADS)
        self.rest = params.get('rest', config.DEFAULT_REQUEST_TIMEOUT)
        self.delay = params.get('delay', config.DEFAULT_REQUEST_DELAY)
        self.debug = params.get('debug', config.DEFAULT_DEBUG_LEVEL)
        self.proxy = params.get('proxy', config.DEFAULT_USE_PROXY)
        self.scheme = params.get('scheme', config.DEFAULT_HTTP_PROTOCOL)
        self.port = params.get('port', config.DEFAULT_HTTP_PORT)
        self.check = params.get('check', config.DEFAULT_CHECK)
        self.iterator = 0

        if 'log' not in params:
            sys.stdout.write(Log.notice(self.message.get('use_log')))

        if self.cpu_cnt < self.threads:
            self.threads = self.cpu_cnt
            sys.stdout.write(Log.warning(self.message.get('max_threads').format(self.threads)))
            pass
