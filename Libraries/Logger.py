import sys

try:
    import coloredlogs
except ImportError:
    sys.exit("""\t\t[!] You need coloredlogs!
                install it from http://pypi.python.org/pypi
                or run pip install coloredlogs.""")

class Logger:
    """Message helper class"""

    @staticmethod
    def success(string):
        level = 'INFO'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.info(string);
        pass

    @staticmethod
    def warning(string):
        level = 'WARNING'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.warning(string);
        pass

    @staticmethod
    def error(string):
        level = 'ERROR'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.error(string);
        pass

    @staticmethod
    def critical(string):
        level = 'CRITICAL'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.critical(string);
        exit();

    @staticmethod
    def debug(string):
        level = 'DEBUG'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.debug(string);
        pass

    @staticmethod
    def verbose(string):
        level = 'VERBOSE'
        coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log(level);
        logger.verbose(string);
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