import sys

class Progress:
    """Progress helper class"""

    @staticmethod
    def run(iterator):
        iterator += 1
        sys.stdout.write("\r%d%%" % int(iterator))
        sys.stdout.flush()
        return iterator
