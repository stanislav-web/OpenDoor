# -*- coding: utf-8 -*-

"""Http class"""

import collections
import logging
import multiprocessing
import re
import urllib3

import sys
import threadpool
import time

class Http:
    """Http class"""

    def __init__(self):
        """Init constructor"""

        self.cpu_cnt = multiprocessing.cpu_count()
        self.counter = collections.Counter()
        self.result = collections.defaultdict(list)
        self.exclusions = []
        self.result.default_factory

    def get(self, host, params=()):
        """Get metadata by url"""

        self.__disable_verbose()
        response = {}

        self.counter['total'] = self.urls.__len__()
        self.counter['pools'] = pool.workers.__len__()

        response['count'] = self.counter
        response['result'] = self.result

        return response

    def request(self, url):

        """Request handler"""

        try:

                conn = urllib3.connection_from_url(url, maxsize=10, block=True,
                                                   timeout=self.rest)
        except TypeError as e:
            sys.exit(Log.error(e.message))


        try:
            response = conn.request(config.DEFAULT_HTTP_METHOD, url, headers={}, redirect=False)
        except (urllib3.exceptions.HostChangedError
                ) as e:
            response = None
            self.iterator = Progress.line(url + ' -> ' + e.message, self.urls.__len__(), 'warning', self.iterator)
        except urllib3.exceptions.ConnectTimeoutError:
            sys.stdout.write(Log.warning(self.message.get('timeout').format(url)))
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

