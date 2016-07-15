from Logger import Logger as log

try:
    import sys
    import threadpool
    import time
    import Queue
    import multiprocessing
    import httplib

    from urllib3 import connection_from_url
    from FileReader import FileReader
    from Progress import Progress

except ImportError:
    log.critical("""You need urllib3 , threadpool!
                install it from http://pypi.python.org/pypi
                or run pip install urllib3 threadpool""")

class Http:
    """Http mapper class"""

    DEFAULT_HTTP_METHOD = 'HEAD'
    DEFAULT_HTTP_PROTOCOL = 'http://'
    DEFAULT_THREADS = 1
    DEFAULT_REQUEST_TIMEOUT  = 10
    DEFAULT_REQUEST_DELAY  = 0

    def __init__(self):
        self.reader = FileReader()
        self.cpu_cnt = multiprocessing.cpu_count();
        self.urls = 0;
        self.success = 0;
        self.possibly = 0;
        self.errors = 0;


    def get(self, host, params = ()):
        """Get metadata by url"""

        self.threads = params.get('threads', self.DEFAULT_THREADS)
        self.rest = params.get('rest', self.DEFAULT_REQUEST_TIMEOUT)
        self.delay = params.get('delay', self.DEFAULT_REQUEST_DELAY)


        if self.cpu_cnt < self.threads:
            log.critical('Pass ' + str(self.cpu_cnt) + ' threads max')

        urls = self.get_urls(host);
        self.iterator = 0
        self.urlslen = urls.__len__();

        try:
            pool = threadpool.ThreadPool(self.threads)
            requests = threadpool.makeRequests(self.request, urls)
            for req in requests:
                pool.putRequest(req)
            time.sleep(1)
            pool.wait()
        except (Exception , SystemExit, Queue.Empty):
            #TODO Eception handle
            pass

        # Threads : pool.workers.__len__()
        # All urls : urls.__len__()

        return

    def request(self, url):
        conn = connection_from_url(url, maxsize=10, block=True, timeout=self.rest)

        headers = {
            'user-agent': self._get_user_agent()
        }
        #httplib.HTTPConnection.debuglevel = 1
        HTTPResponse = conn.request(self.DEFAULT_HTTP_METHOD, url, headers=headers)
        time.sleep(self.delay)

        return self.response(HTTPResponse)

    def response(self, HTTPResponse):
        """Response handler"""

        self.iterator = Progress.run(self.iterator)

        if HTTPResponse == None:
            pass
        # print HTTPResponse.status
        # print HTTPResponse.version
        # print HTTPResponse.reason
        # print HTTPResponse.headers

    def get_urls(self, host):
        """Get urls"""
        dirs = self.reader.get_directories();
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

    def _get_user_agent(self):
        """Get random user agent from FileReader"""
        return self.reader.get_random_user_agent()[0];


# class DevNull:
#     def write(self, msg):
#         pass

#sys.stderr = DevNull()