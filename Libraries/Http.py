import sys
import socket
import time
import logging
import multiprocessing
import exceptions
import collections
import httplib
from Logger import Logger as log

try:

    import threadpool
    import urllib3

except ImportError:
    log.critical("""\t\t[!] You need urllib3 , threadpool!
                install it from http://pypi.python.org/pypi
                or run pip install urllib3 threadpool""")

from FileReader import FileReader
from Progress import Progress

class Http:
    """Http mapper class"""

    DEFAULT_HTTP_METHOD = 'HEAD'
    DEFAULT_HTTP_PROTOCOL = 'http://'
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

        self.__is_server_online(host)
        self.__disable_verbose();
        self.__parse_params(params)
        self.urls = self.__get_urls(host);
        response = {};

        try:
            httplib.HTTPConnection.debuglevel = self.debug

            if hasattr(urllib3, 'disable_warnings'):
                urllib3.disable_warnings()

            pool = threadpool.ThreadPool(self.threads)
            requests = threadpool.makeRequests(self.request, self.urls)
            for req in requests:
                pool.putRequest(req)
            time.sleep(1)
            pool.wait()
        except exceptions.AttributeError as e:
            log.critical(e.message)
        except KeyboardInterrupt:
            log.warning('Session canceled')
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
                log.critical(e.message + ": " + proxyserver)
        else:
            conn = urllib3.connection_from_url(url, maxsize=10, block=True, timeout=self.rest)

        headers = {
            'accept-encoding' :'gzip, deflate, sdch',
            'accept-language' : 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4,uk;q=0.2,es;q=0.2',
            'cache-control' : 'no-cache',
            'user-agent': self.reader.get_random_user_agent()
        }
        try :
            HTTPResponse = conn.request(self.DEFAULT_HTTP_METHOD, url, headers=headers)
        except (urllib3.exceptions.ConnectTimeoutError ,
                urllib3.exceptions.MaxRetryError,
                urllib3.exceptions.HostChangedError,
                urllib3.exceptions.ReadTimeoutError,
                urllib3.exceptions.ProxyError
                ) as e:
            HTTPResponse = None
            self.iterator = Progress.line(url + ' -> ' + e.message, self.urls.__len__(), 'warning', self.iterator)
        except exceptions.AttributeError as e:
            log.critical(e.message)
        except TypeError as e:
            log.critical(e.message)

        time.sleep(self.delay)
        return self.response(HTTPResponse, url)

    def response(self, HTTPResponse, url):
        """Response handler"""

        # TODO
        #print HTTPResponse.getheader('content-length');

        self.counter.update(("completed",))
        if hasattr(HTTPResponse, 'status'):
            if HTTPResponse.status in self.DEFAULT_HTTP_FAILED_STATUSES:
                self.iterator = Progress.line(url, self.urls.__len__(), 'error', self.iterator)
                self.counter.update(("failed",))
            elif HTTPResponse.status in self.DEFAULT_HTTP_SUCCESS_STATUSES:
                self.iterator = Progress.line(url, self.urls.__len__(), 'success', self.iterator)
                self.counter.update(("success",))
            elif HTTPResponse.status in self.DEFAULT_HTTP_UNRESOLVED_STATUSES:
                self.iterator = Progress.line(url, self.urls.__len__(), 'warning', self.iterator)
                self.counter.update(("possible",))
            elif HTTPResponse.status in self.DEFAULT_HTTP_REDIRECT_STATUSES:
                self.iterator = Progress.line(url, self.urls.__len__(), 'warning', self.iterator)
                self.counter.update(("redirects",))
            else:
                self.counter.update(("undefined",))
                return
            self.result[HTTPResponse.status].append(url)

        else:
            return

    def __disable_verbose(self):
        """ Disbale verbose warnings info"""
        level = 'WARNING'
        logging.getLogger("urllib3").setLevel(level)

    def __is_server_online(self, host):
        """ Check if server is online"""
        try:
            socket.gethostbyname(host)
            log.info('Server : '+ host +' is online')
            log.info('Scanning ' + host + ' ...')
        except socket.error:
            log.critical('Oops Error occured, Server offline or invalid URL or response')

    def __get_urls(self, host):
        """Get urls"""

        lines = self.reader.get_file_data(self.check);

        if self.DEFAULT_CHECK == self.check:
            urls = self.__urls_resolves(host, lines);
        else:
            urls = self.__subdomains_resolves(host, lines);
        return urls

    def __urls_resolves(self, host, directories):
        """Urls path resolve"""
        resolve_dirs = []
        for path in directories:
            path = path.replace("\n", "")
            if "/" != path[0]:
                path = '/' + path
            resolve_dirs.append(self.DEFAULT_HTTP_PROTOCOL + host + path)
        return resolve_dirs

    def __subdomains_resolves(self, host, subdomains):
        """Subdomains path resolve"""
        resolve_subs = []
        for sub in subdomains:
            sub = sub.replace("\n", "")
            resolve_subs.append(self.DEFAULT_HTTP_PROTOCOL + sub + "." + host)
        return resolve_subs

    def __parse_params(self, params):
        """Parse additional params"""
        self.threads = params.get('threads', self.DEFAULT_THREADS)
        self.rest = params.get('rest', self.DEFAULT_REQUEST_TIMEOUT)
        self.delay = params.get('delay', self.DEFAULT_REQUEST_DELAY)
        self.debug = params.get('debug', self.DEFAULT_DEBUG_LEVEL)
        self.proxy = params.get('proxy', self.DEFAULT_USE_PROXY)
        self.check = params.get('check', self.DEFAULT_CHECK)
        self.iterator = 0

        if self.cpu_cnt < self.threads:
            self.threads = self.cpu_cnt
            log.warning('Passed ' + str(self.cpu_cnt) + ' threads max for your possibility')
            pass