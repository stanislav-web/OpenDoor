try:
    import sys
    import urllib3
except ImportError:
    sys.exit("""You need urllib3!
                install it from http://pypi.python.org/pypi
                or run pip install urllib3""")

from FileReader import FileReader

class Http:
    """Http mapper class"""

    DEFAULT_THREADS = 1
    DEFAULT_HTTP_METHOD = 'HEAD'

    def __init__(self):
        self.reader = FileReader()

    def connect(self, host, threads = DEFAULT_THREADS):

        # load directories list
        directories = self.reader.get_directories()
        # open pool
        self.pool = self.__open(host, threads)

        for path in directories:
            path = path.replace("\n", "")
            headers = {
                'user-agent' : self.reader.get_random_user_agent()[0]
            }
            response = self.request(path, headers)

            #print response.status
            #print response.headers
        #print self.pool.num_connections
        #print self.pool.num_requests
        #print self.pool.port
        #self.pool.close()
        #return

    def __open(self, url, threads):
        pool = urllib3.HTTPConnectionPool(url, maxsize=threads)
        return pool

    def request(self, path, headers):
        response = self.pool.request(self.DEFAULT_HTTP_METHOD, path, redirect=True, timeout=10, headers=headers)
        return response