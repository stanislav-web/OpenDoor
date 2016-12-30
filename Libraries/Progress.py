# -*- coding: utf-8 -*-

"""Progress class"""

import sys
from .Logger import Logger as Log
from tabulate import tabulate
from termcolor import colored


class Progress:
    """Progress helper class"""

    @staticmethod
    def line(message, countall, status, iterator, show=True):
        """Progress line"""

        iterator += 1
        iterator = int(iterator)
        indicator = iterator * 100 / countall;
        if True == show:
            message = '{}% {}'.format(str(indicator), message)
            getattr(Log, '{}'.format(status))(message, showtime = True, showlevel = False)
        sys.stdout.flush()
        return iterator

    @staticmethod
    def view(result):
        """Result line"""

        count = result.get('count').items()
        result.pop("count", None)
        result = result.get('result')
        for status in result:

            #if status in Status.Http.DEFAULT_HTTP_FAILED_STATUSES:
                # failed urls print
                #print colored('FAILED ', 'red', attrs=['bold'])
                #for url in result[status]:
                #    Log.error('{} : {}'.format(str(status), url), showtime=False, showlevel=False);

            if status in Status.Http.DEFAULT_HTTP_REDIRECT_STATUSES:
                # have redirects urls print
                print colored('REDIRECTS ', 'yellow', attrs=['bold'])
                for url in result[status]:
                    Log.verbose('{} : {}'.format(str(status), url), showtime=False, showlevel=False);

            if status in Status.Http.DEFAULT_HTTP_UNRESOLVED_STATUSES:
                # unresolved urls print
                print colored('POSSIBLE ', 'yellow', attrs=['bold'])
                for url in result[status]:
                    Log.warning('{} : {}'.format(str(status), url), showtime=False, showlevel=False);

            if status in Status.Http.DEFAULT_HTTP_SUCCESS_STATUSES:
                # success urls print
                print colored('SUCCESS ', 'green', attrs=['bold'])
                for url in result[status]:
                    Log.success('{} : {}'.format(str(status), url), showtime=False, showlevel=False);

        headers = [colored('Statistics', attrs=['bold']), colored('Summary', attrs=['bold'])]
        print tabulate(count, headers=headers, tablefmt="fancy_grid")
