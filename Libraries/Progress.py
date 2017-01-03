# -*- coding: utf-8 -*-

"""Progress class"""

import sys
from termcolor import colored
from tabulate import tabulate

from .HttpConfig import HttpConfig as Status
from .Logger import Logger as Log


class Progress:
    """Progress class"""

    @staticmethod
    def line(message, countall, status, iterator, show=True, inline=True):
        """Progress line"""

        iterator += 1
        iterator = int(iterator)
        indicator = iterator * 100 / countall
        if True == show:
            message = '{}% {}'.format(str(indicator), message)
            getattr(Log, '{}'.format(status))(message, showtime=True, showlevel=False)
        sys.stdout.flush()
        return iterator

    @staticmethod
    def clear():
        sys.stdout.write('\033[1K')
        sys.stdout.write('\033[0G')

    @staticmethod
    def view(result):
        """Result line"""

        count = result.get('count').items()
        result.pop("count", None)
        result = result.get('result')
        for status in result:

            if status in Status.DEFAULT_HTTP_BAD_REQUEST_STATUSES:
                # have redirects urls print
                print colored('BAD REQUESTS ', 'yellow', attrs=['bold'])
                for url in result[status]:
                    Log.verbose('{} : {}'.format(str(status), url), showtime=False, showlevel=False)

            if status in Status.DEFAULT_HTTP_REDIRECT_STATUSES:
                # have redirects urls print
                print colored('REDIRECTS ', 'yellow', attrs=['bold'])
                for url in result[status]:
                    Log.verbose('{} : {}'.format(str(status), url), showtime=False, showlevel=False)

            if status in Status.DEFAULT_HTTP_UNRESOLVED_STATUSES:
                # unresolved urls print
                print colored('POSSIBLE ', 'yellow', attrs=['bold'])
                for url in result[status]:
                    Log.warning('{} : {}'.format(str(status), url), showtime=False, showlevel=False)

            if status in Status.DEFAULT_HTTP_SUCCESS_STATUSES:
                # success urls print
                print colored('SUCCESS ', 'green', attrs=['bold'])
                for url in result[status]:
                    Log.success('{} : {}'.format(str(status), url), showtime=False, showlevel=False)

        headers = [colored('Statistics', attrs=['bold']), colored('Summary', attrs=['bold'])]
        print tabulate(count, headers=headers, tablefmt="fancy_grid")
