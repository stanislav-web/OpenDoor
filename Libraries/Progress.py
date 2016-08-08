import sys
from Logger import Logger
import Http as Status

try:
    from tabulate import tabulate
    import coloredlogs
    from termcolor import colored

except ImportError:
    sys.exit("""\t\t[!] You need coloredlogs termcolor and tabulate!
                install it from http://pypi.python.org/pypi
                or run pip install coloredlogs termcolor tabulate.""")

class Progress:
    """Progress helper class"""

    @staticmethod
    def line(message, countall, status, iterator):
        """Progress line"""

        iterator += 1
        iterator = int(iterator)
        indicator = iterator * 100 / countall;
        getattr(Logger, '{}'.format(status))('{}% {}'.format(str(indicator), message), showtime = True, showlevel = False)
        sys.stdout.flush()
        return iterator

    @staticmethod
    def view(result):
        """Result line"""

        count = result.get('count').items()
        result.pop("count", None)
        result = result.get('result')
        for status in result:

            if status in Status.Http.DEFAULT_HTTP_FAILED_STATUSES:
                # failed urls print
                print colored('FAILED ', 'red', attrs=['bold'])
                for url in result[status]:
                    Logger.error(str(status) + " : " + url, showtime=False, showlevel=False);

            if status in Status.Http.DEFAULT_HTTP_REDIRECT_STATUSES:
                # have redirects urls print
                print colored('REDIRECTS ', 'yellow', attrs=['bold'])
                for url in result[status]:
                    Logger.verbose(str(status) + " : " + url, showtime=False, showlevel=False);

            if status in Status.Http.DEFAULT_HTTP_UNRESOLVED_STATUSES:
                # unresolved urls print
                print colored('POSSIBLE ', 'yellow', attrs=['bold'])
                for url in result[status]:
                    Logger.warning(str(status) + " : " + url, showtime=False, showlevel=False);

            if status in Status.Http.DEFAULT_HTTP_SUCCESS_STATUSES:
                # success urls print
                print colored('SUCCESS ', 'green', attrs=['bold'])
                for url in result[status]:
                    Logger.success(str(status) + " : " + url, showtime=False, showlevel=False);

        print tabulate(count, headers=[colored('Statistics', attrs=['bold']),colored('Summary', attrs=['bold'])], tablefmt="fancy_grid")
        sys.exit