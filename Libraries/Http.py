import sys
import socket
import time
import logging
import Queue
import multiprocessing

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
    DEFAULT_REQUEST_TIMEOUT  = 10
    DEFAULT_REQUEST_DELAY  = 0
    DEFAULT_HTTP_SUCCESS_STATUSES = [100,101,200,201,204]
    DEFAULT_HTTP_FAILED_STATUSES = [404,500,501,502,503,504]
    DEFAULT_HTTP_UNRESOLVED_STATUSES = [401,403]

    def __init__(self):
        """Init constructor"""
        self.reader = FileReader()
        self.cpu_cnt = multiprocessing.cpu_count();
        self.urls = 0;
        self.success = 0;
        self.possibly = 0;
        self.errors = 0;

    def get(self, host, params = ()):
        """Get metadata by url"""

        self.__is_server_online(host)
        self.__disable_verbose();
        self.urls = self.__get_urls(host);
        self.__parse_params(params)

        try:

            pool = threadpool.ThreadPool(self.threads)
            requests = threadpool.makeRequests(self.request, self.urls)
            for req in requests:
                pool.putRequest(req)
            time.sleep(1)
            pool.wait()
        except (Exception , SystemExit, Queue.Empty) as e:
            exit('First: ' + e)
        except (Exception , SystemExit, Queue.Empty) as e:
            exit('Seconf: ' + e)

        # Threads : pool.workers.__len__()
        # All urls : self.urls.__len__()

        return

    def request(self, url):
        conn = urllib3.connection_from_url(url, maxsize=10, block=True, timeout=self.rest, retries=3)

        headers = {
            'user-agent': self.reader.get_random_user_agent()
        }
        try :
            HTTPResponse = conn.request(self.DEFAULT_HTTP_METHOD, url, headers=headers)
        except urllib3.exceptions.HostChangedError as e:
            HTTPResponse = None
            self.iterator = Progress.line(url + ' -> ' +e.message, self.urls.__len__(), 'warning', self.iterator)

        time.sleep(self.delay)
        return self.response(HTTPResponse, url)

    def response(self, HTTPResponse, url):
        """Response handler"""
        # print HTTPResponse.status
        # print HTTPResponse.status
        # print HTTPResponse.reason
        # print HTTPResponse.pool

        if HTTPResponse == None:
            return

        if HTTPResponse.status in self.DEFAULT_HTTP_SUCCESS_STATUSES:
            self.iterator = Progress.line(url, self.urls.__len__(), 'success', self.iterator)
        if HTTPResponse.status in self.DEFAULT_HTTP_UNRESOLVED_STATUSES:
            self.iterator = Progress.line(url, self.urls.__len__(), 'warning', self.iterator)
        if HTTPResponse.status in self.DEFAULT_HTTP_FAILED_STATUSES:
            self.iterator = Progress.line(url, self.urls.__len__(), 'error', self.iterator)


        # print HTTPResponse.status
        # print HTTPResponse.version
        # print HTTPResponse.reason
        # print HTTPResponse.headers

    def __disable_verbose(self):
        """ Disbale verbose warnings info"""
        level = 'WARNING'
        logging.getLogger("urllib3").setLevel(level)

    def __is_server_online(self, host):
        """ Check if server is online"""
        try:
            socket.gethostbyname(host)
            log.success('Server : '+ host +' is online')
            log.success('Scanning ' + host + ' ...')
        except socket.error:
            log.critical('Oops Error occured, Server offline or invalid URL or response')

    def __get_urls(self, host):
        """Get urls"""
        dirs = self.reader.get_file_data('directories');
        urls = self.__urls_resolves(host, dirs);
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

    def __parse_params(self, params):
        """Parse additional params"""
        self.threads = params.get('threads', self.DEFAULT_THREADS)
        self.rest = params.get('rest', self.DEFAULT_REQUEST_TIMEOUT)
        self.delay = params.get('delay', self.DEFAULT_REQUEST_DELAY)
        self.iterator = 0
        if self.cpu_cnt < self.threads:
            self.threads = self.cpu_cnt
            log.warning('Passed ' + str(self.cpu_cnt) + ' threads max for your possibility')
            pass




# class DevNull:
#     def write(self, msg):
#         pass

#sys.stderr = DevNull()