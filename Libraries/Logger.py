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
    def success(message):
        currdate = datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ')
        date = colored(currdate, 'green')
        status = colored('SUCCESS', attrs = ['bold'])
        dot = ' : '
        message = colored(message, 'green')
        output = "%s%s%s%s" % (date, status, dot, message)
        print (output)
        pass

    @staticmethod
    def info(message):
        level = 'INFO'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.info(message);
        pass

    @staticmethod
    def warning(message):
        level = 'WARNING'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.warning(message);
        pass

    @staticmethod
    def error(message):
        level = 'ERROR'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.error(message);
        pass

    @staticmethod
    def critical(message):
        level = 'CRITICAL'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.critical(message);
        exit();

    @staticmethod
    def debug(message):
        level = 'DEBUG'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.debug(message);
        pass

    @staticmethod
    def verbose(message):
        level = 'VERBOSE'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
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