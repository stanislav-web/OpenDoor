# -*- coding: utf-8 -*-

"""Http class"""

import sys
import socket
import time
import re
import logging
import multiprocessing
import exceptions
import collections
import httplib
import threadpool
import urllib3
from urlparse import urlparse
from .Logger import Logger as Log
from .FileReader import FileReader
from .Progress import Progress



class Http:
    """Http mapper class"""

    DEFAULT_HTTP_METHOD = 'HEAD'
    DEFAULT_HTTP_PROTOCOL = 'http://'
    DEFAULT_HTTP_PORT = 80
    DEFAULT_THREADS = 1
    DEFAULT_DEBUG_LEVEL = 0
    DEFAULT_REQUEST_TIMEOUT  = 10
    DEFAULT_REQUEST_DELAY  = 0
    DEFAULT_USE_PROXY = False
    DEFAULT_CHECK = 'directories'
    DEFAULT_HTTP_SUCCESS_STATUSES = [100,101,200,201,202,203,204,205,206,207,208]
    DEFAULT_HTTP_REDIRECT_STATUSES = [301,302,303,304,307,308]
    DEFAULT_HTTP_FAILED_STATUSES = [404,429,500,501,502,503,504]
    DEFAULT_HTTP_UNRESOLVED_STATUSES = [401,403]

    def __init__(self):
        """Init constructor"""

        self.reader = FileReader()
        self.cpu_cnt = multiprocessing.cpu_count();
        self.counter = collections.Counter()
        self.result = collections.defaultdict(list)
        self.result.default_factory

    def get(self, host, params = ()):
        """Get metadata by url"""

        self.__parse_params(params)
        self.__is_server_online(host, self.port)
        self.__disable_verbose()
        self.urls = self.__get_urls(host)
        response = {}

        try:
            httplib.HTTPConnection.debuglevel = self.debug

            if hasattr(urllib3, 'disable_warnings'):
                urllib3.disable_warnings()

            pool = threadpool.ThreadPool(self.threads)
            requests = threadpool.makeRequests(self.request, self.urls)
            for req in requests:
                pool.putRequest(req)
            pool.wait()
        except exceptions.AttributeError as e:
            Log.critical(e.message)
        except KeyboardInterrupt:
            Log.warning('Session canceled')
            sys.exit();

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
                Log.critical(e.message + ": " + proxyserver)
        else:
            try:

                conn = urllib3.connection_from_url(url, maxsize=10, block=True,
                                                   timeout=self.rest)
            except TypeError as e:
                Log.critical(e.message)

        headers = {
            'accept-encoding' :'gzip, deflate, sdch',
            'accept-language' : 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4,uk;q=0.2,es;q=0.2',
            'cache-control' : 'no-cache',
            'user-agent': self.reader.get_random_user_agent()
        }
        try :
            response = conn.request(self.DEFAULT_HTTP_METHOD, url, headers=headers, redirect=False)
        except (urllib3.exceptions.ConnectTimeoutError ,
                urllib3.exceptions.HostChangedError,
                urllib3.exceptions.ReadTimeoutError,
                urllib3.exceptions.ProxyError,
                urllib3.exceptions.NewConnectionError
                ) as e:
            response = None
            self.iterator = Progress.line(url + ' -> ' + e.message, self.urls.__len__(), 'warning', self.iterator)
        except urllib3.exceptions.MaxRetryError:
            pass
        except exceptions.AttributeError as e:
            Log.critical(e.message)
        except TypeError as e:
            Log.critical(e.message)

        time.sleep(self.delay)
        return self.response(response, url)

    def response(self, response, url):
        """Response handler"""
        self.counter.update(("completed",))
        if hasattr(response, 'status'):
            if response.status in self.DEFAULT_HTTP_FAILED_STATUSES:
                self.iterator = Progress.line(url, self.urls.__len__(), 'error', self.iterator, False)
                self.counter.update(("failed",))
            elif response.status in self.DEFAULT_HTTP_SUCCESS_STATUSES:
                self.iterator = Progress.line(url, self.urls.__len__(), 'success', self.iterator)
                self.counter.update(("success",))
            elif response.status in self.DEFAULT_HTTP_UNRESOLVED_STATUSES:
                self.iterator = Progress.line(url, self.urls.__len__(), 'warning', self.iterator)
                self.counter.update(("possible",))
            elif response.status in self.DEFAULT_HTTP_REDIRECT_STATUSES:
                self.iterator = Progress.line(url, self.urls.__len__(), 'warning', self.iterator)
                self.counter.update(("redirects",))
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

        level = 'WARNING'
        logging.getLogger("urllib3").setLevel(level)

    @staticmethod
    def __is_server_online(host, port):
        """ Check if server is online"""

        s = socket.socket()

        try:
            ip = socket.gethostbyname(host)

            print socket.gethostbyaddr(ip)
            s.settimeout(3)
            s.connect((host, port))

            Log.info('Server {0} {1}:{2} is online'.format(host,ip,port))
            Log.info('Scanning ' + host + ' ...')
        except (socket.gaierror,socket.timeout) as e:
            Log.critical('Oops Error occured, Server offline or invalid URL. Reason: {}'.format(e))
        finally:
            s.close()

    def __handle_redirect_url(self, url, response):
        """ Handle redirect url """
        location = response.get_redirect_location()
        matches = re.search("(?P<url>https?://[^\s]+)", location)
        if None != matches.group("url"):
            redirect_url = matches.group("url")
        else:
            urlp = urlparse(url)
            redirect_url = urlp.scheme + '://' + urlp.netloc + location

        Log.verbose('Redirect to : ' + redirect_url);
        http = urllib3.PoolManager()

        try:
            response_red = http.request(self.DEFAULT_HTTP_METHOD, redirect_url, redirect=True)
            time.sleep(self.delay)
            self.response(response_red, redirect_url)
        except urllib3.exceptions.MaxRetryError:
            pass

    def __get_urls(self, host):
        """Get urls"""

        lines = self.reader.get_file_data(self.check);

        if self.DEFAULT_CHECK == self.check:
            urls = self.__urls_resolves(host, self.port, lines);
        else:
            urls = self.__subdomains_resolves(host, lines);
        return urls

    def __urls_resolves(self, host, port, directories):
        """Urls path resolve"""

        resolve_dirs = []
        for path in directories:
            path = path.replace("\n", "")
            if "/" != path[0]:
                path = '/' + path

            if self.DEFAULT_HTTP_PORT != port:
                resolve_dirs.append(self.scheme + host + ":" + str(port) + path)
            else:
                resolve_dirs.append(self.scheme + host + path)
        return resolve_dirs

    def __subdomains_resolves(self, host, subdomains):
        """Subdomains path resolve"""

        resolve_subs = []
        for sub in subdomains:
            sub = sub.replace("\n", "")
            resolve_subs.append(self.scheme + sub + "." + host)
        return resolve_subs

    def __parse_params(self, params):
        """Parse additional params"""

        self.threads = params.get('threads', self.DEFAULT_THREADS)
        self.rest = params.get('rest', self.DEFAULT_REQUEST_TIMEOUT)
        self.delay = params.get('delay', self.DEFAULT_REQUEST_DELAY)
        self.debug = params.get('debug', self.DEFAULT_DEBUG_LEVEL)
        self.proxy = params.get('proxy', self.DEFAULT_USE_PROXY)
        self.scheme = params.get('scheme', self.DEFAULT_HTTP_PROTOCOL)
        self.port = params.get('port', self.DEFAULT_HTTP_PORT)
        self.check = params.get('check', self.DEFAULT_CHECK)
        self.iterator = 0

        if 'log' not in params:
            Log.debug('Use --log param to save scan result');

        if self.cpu_cnt < self.threads:
            self.threads = self.cpu_cnt
            Log.warning('Passed ' + str(self.cpu_cnt) + ' threads max for your possibility')
            pass
        