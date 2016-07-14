try:
    import sys
    import threadpool
    from urllib3 import connection_from_url
    from FileReader import FileReader

except ImportError:
    sys.exit("""You need urllib3 , threadpool!
                install it from http://pypi.python.org/pypi
                or run pip install urllib3 threadpool""")


class Http:
    """Http mapper class"""

    DEFAULT_THREADS = 2
    DEFAULT_HTTP_METHOD = 'HEAD'
    DEFAULT_HTTP_PROTOCOL = 'http://'

    def __init__(self):
        self.reader = FileReader()
        self.urls = 0;
        self.success = 0;
        self.possibly = 0;

    def get(self, host, threads = DEFAULT_THREADS):
        """Get metadata by url"""

        urls = self.get_urls(host);
        pool = threadpool.ThreadPool(threads)
        requests = threadpool.makeRequests(self.request, urls)
        for req in requests:
            pool.putRequest(req)
        pool.wait()

        # Threads : pool.workers.__len__()
        # All urls : urls.__len__()

        return

    def request(self, url):
        """
        Get the request to url
        :param url: request url
        :type url: str
        :return: urllib3.response.HTTPResponse
        :rtype: urllib3.response.HTTPResponse
        """
        conn = connection_from_url(url, timeout=10.0, maxsize=10, block=True)

        headers = {
            'user-agent': self._get_user_agent()
        }
        HTTPResponse = conn.request(self.DEFAULT_HTTP_METHOD, url, headers=headers)
        return self.response(HTTPResponse)

    def response(self, HTTPResponse):
        pass
        #print HTTPResponse.status
        #print HTTPResponse.version
        #print HTTPResponse.reason
        #print HTTPResponse.headers

    def get_urls(self, host):
        """Get urls"""
        dirs = self.reader.get_directories();
        urls = self.__urls_resolves(host, dirs);

        return urls

    def __path_resolve(self, path):
        """Directory path resolve"""

        path = path.replace("\n", "")
        if "/" != path[0]:
            path = '/' + path

        return path

    def __urls_resolves(self, host, directories):
        """Urls path resolve"""

        resolve_dirs = []
        for path in directories:
            resolve_dirs.append(self.DEFAULT_HTTP_PROTOCOL + host + self.__path_resolve(path))

        return resolve_dirs

    def _get_user_agent(self):
        """Get random user agent from FileReader"""
        return self.reader.get_random_user_agent()[0];