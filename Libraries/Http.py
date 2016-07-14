try:
    import sys
    import threadpool
    from urllib3 import connection_from_url
    from FileReader import FileReader

except ImportError:
    sys.exit("""You need urllib3!
                install it from http://pypi.python.org/pypi
                or run pip install urllib3""")


class Http:
    """Http mapper class"""

    DEFAULT_THREADS = 1
    DEFAULT_HTTP_METHOD = 'HEAD'
    DEFAULT_HTTP_PROTOCOL = 'http://'

    def __init__(self):
        self.reader = FileReader()

    def get(self, host, threads = DEFAULT_THREADS):
        """Get metadata by url"""

        urls = self.get_urls(host);
        pool = threadpool.ThreadPool(threads)
        requests = threadpool.makeRequests(self.request, urls)
        [pool.putRequest(req) for req in requests]
        pool.wait()

        return

    def request(self, url):
        """Get the request to url"""
        conn = connection_from_url(url, timeout=10.0, maxsize=10, block=True)

        headers = {
            'user-agent': self._get_user_agent()
        }
        response = conn.request(self.DEFAULT_HTTP_METHOD, url, headers=headers)
        print url, response
        print "Done!"


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