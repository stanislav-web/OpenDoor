import sys
from Logger import Logger

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
    def line(message, httpstatus, countall, status, iterator):

        iterator += 1
        iterator = int(iterator)
        indicator = iterator * 100 / countall;

        getattr(Logger, '%s' % status)(str(indicator) + "% " + str(httpstatus) + " " + message)
        sys.stdout.flush()
        return iterator

    @staticmethod
    def view(result):
        count = result.get('count').items()
        print tabulate(count, headers=[colored('Statistics', attrs=['bold']),colored('Summary', attrs=['bold'])], tablefmt="fancy_grid")