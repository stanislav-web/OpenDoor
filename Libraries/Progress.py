import sys
from Logger import Logger

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
