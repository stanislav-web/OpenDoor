import sys
import os
from datetime import datetime
import Http as Status

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
    def success(message, showtime=True, showlevel=True):
        level = 'SUCCESS'
        if True == showtime:
            asctime = colored(datetime.now().strftime('[%Y-%m-%d %H:%M:%S] '), 'green')
        else:
            asctime = ""
        if True == showlevel:
            level = colored(level, attrs=['bold']) + " : "
        else:
            level = ""

        message = colored(message, 'green')

        print "%s%s%s" % (asctime, level, message)
        pass

    @staticmethod
    def info(message, showtime=True, title=True):
        level = 'INFO'
        if True == showtime:
            coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        else:
            coloredlogs.install(level=level, fmt='%(message)s')
        logger = Logger.log(level);
        logger.info(message);
        pass

    @staticmethod
    def warning(message, showtime=True, showlevel=True):
        level = 'WARNING'
        if True == showtime:
            asctime = colored(datetime.now().strftime('[%Y-%m-%d %H:%M:%S] '), 'green')
        else:
            asctime = ""
        if True == showlevel:
            level = colored(level, attrs=['bold']) + " : "
        else:
            level = ""

        message = colored(message, 'yellow')
        print "%s%s%s" % (asctime, level, message)
        pass

    @staticmethod
    def error(message, showtime=True, showlevel=True):
        level = 'ERROR'
        if True == showtime:
            asctime = colored(datetime.now().strftime('[%Y-%m-%d %H:%M:%S] '), 'green')
        else:
            asctime = ""
        if True == showlevel:
            level = colored(level, attrs=['bold']) + " : "
        else:
            level = ""

        message = colored(message, 'red')
        print "%s%s%s" % (asctime, level, message)
        pass

    @staticmethod
    def critical(message, showtime=True, title=True):
        level = 'CRITICAL'
        if True == showtime:
            coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        else:
            coloredlogs.install(level=level, fmt='%(message)s')
        logger = Logger.log(level);
        sys.exit(logger.critical(message));

    @staticmethod
    def debug(message, showtime=True):
        level = 'DEBUG'
        if True == showtime:
            coloredlogs.install(level=level, fmt='[%(asctime)s] %(levelname)s : %(message)s')
        else:
            coloredlogs.install(level=level, fmt='%(message)s')
        logger = Logger.log(level);
        logger.debug(message);
        pass

    @staticmethod
    def verbose(message, showtime=True, showlevel=True):

        if True == showtime:
            asctime = colored(datetime.now().strftime('[%Y-%m-%d %H:%M:%S] '), 'green')
        else:
            asctime = ""
        if True == showlevel:
            level = colored('VERBOSE', attrs=['bold']) + " : "
        else:
            level = ""

        message = colored(message, 'blue')

        print "%s%s%s" % (asctime, level, message)
        pass

    @staticmethod
    def log(level):

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

    @staticmethod
    def syslog(key, params):

        path = os.path.join('Logs', key);
        if not os.path.exists(path):
            os.makedirs(path)

        params.pop("count", None)
        result = params.get('result')

        for status in result:

            if status in Status.Http.DEFAULT_HTTP_REDIRECT_STATUSES:
                # have redirects urls log
                file = open(os.path.join(path, 'redirects.log'), 'w')
                for url in result[status]:
                    file.write("%s\n" % url)
                file.close()

            if status in Status.Http.DEFAULT_HTTP_UNRESOLVED_STATUSES:
                # unresolved urls log
                file = open(os.path.join(path, 'possible.log'), 'w')
                for url in result[status]:
                    file.write("%s\n" % url)
                file.close()

            if status in Status.Http.DEFAULT_HTTP_SUCCESS_STATUSES:
                # success urls print
                file = open(os.path.join(path, 'success.log'), 'w')
                for url in result[status]:
                    file.write("%s\n" % url)
                file.close()