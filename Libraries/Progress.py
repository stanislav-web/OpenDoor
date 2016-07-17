import sys
from Logger import Logger

class Progress:
    """Progress helper class"""

    @staticmethod
    def line(message, countall, status, iterator):

        iterator += 1
        iterator = int(iterator)
        indicator = iterator * 100 / countall;

        getattr(Logger, '%s' % status)(str(indicator) + "% " + message)
        sys.stdout.flush()
        return iterator
