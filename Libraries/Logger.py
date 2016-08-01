import sys
from datetime import datetime

try:
    import coloredlogs
    from termcolor import colored
except ImportError:
    sys.exit("""\t\t[!] You need coloredlogs and termcolor!
                install it from http://pypi.python.org/pypi
                or run pip install coloredlogs termcolor.""")

class Logger:
    """Message helper class"""

    @staticmethod
    def success(message, putdate=True):

        status = colored('SUCCESS', attrs = ['bold'])
        dot = ' : '
        message = colored(message, 'green')

        if True == putdate:
            currdate = datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ')
            date = colored(currdate, 'green')
            output = "%s%s%s%s" % (date, status, dot, message)
        else:
            output = "%s" % (message)
        print (output)
        pass

    @staticmethod
    def info(message, putdate=True):
        level = 'INFO'
        if True == putdate:
            coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        else:
            coloredlogs.install(level=level, fmt='%(message)s')
        logger = Logger.log(level);
        logger.info(message);
        pass

    @staticmethod
    def warning(message, putdate=True):
        level = 'WARNING'
        if True == putdate:
            coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        else:
            coloredlogs.install(level=level, fmt='%(message)s')
        logger = Logger.log(level);
        logger.warning(message);
        pass

    @staticmethod
    def error(message, putdate=True):
        level = 'ERROR'
        if True == putdate:
            coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        else:
            coloredlogs.install(level=level, fmt='%(message)s')
        logger = Logger.log(level);
        logger.error(message);
        pass

    @staticmethod
    def critical(message, putdate=True):
        level = 'CRITICAL'
        if True == putdate:
            coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        else:
            coloredlogs.install(level=level, fmt='%(message)s')
        logger = Logger.log(level);
        logger.critical(message);
        exit();

    @staticmethod
    def debug(message, putdate=True):
        level = 'DEBUG'
        if True == putdate:
            coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        else:
            coloredlogs.install(level=level, fmt='%(message)s')
        logger = Logger.log(level);
        logger.debug(message);
        pass

    @staticmethod
    def verbose(message, putdate=True):
        level = 'VERBOSE'
        if True == putdate:
            coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        else:
            coloredlogs.install(level=level, fmt='%(message)s')
        logger = Logger.log(level);
        logger.verbose(message);
        pass

    @classmethod
    def log(cls, level):

        try:
            import logging
            import verboselogs

        except ImportError:
            sys.exit("""You need logging , verboselogs!
                            install it from http://pypi.python.org/pypi
                            or run pip install logging verboselogs""")

        # set logger level from parent class
        logger =  verboselogs.VerboseLogger('')
        # add the handlers to the logger
        logger.setLevel(getattr(logging, level))

        return logger