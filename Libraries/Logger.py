# -*- coding: utf-8 -*-

"""Logger class"""

import os
import sys
from datetime import datetime
from termcolor import colored
import coloredlogs
from HttpConfig import HttpConfig as Status


class Logger:
    """Logger class"""

    @staticmethod
    def success(message, showtime=True, showlevel=True):
        """Success level message"""

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

        return "{}{}{}\n".format(asctime, level, message)

    @staticmethod
    def notice(message, showtime=True, title=True, showlevel=True):
        """Notice level message"""

        level = 'NOTICE'
        if True == showtime:
            asctime = colored(datetime.now().strftime('[%Y-%m-%d %H:%M:%S] '), 'green')
        else:
            asctime = ""
        if True == showlevel:
            level = colored(level, attrs=['bold']) + " : "
        else:
            level = ""
        message = colored(message, 'green')

        return "{}{}{}\n".format(asctime, level, message)

    @staticmethod
    def info(message, showtime=True, title=True, showlevel=True):
        """Info level message"""

        level = 'INFO'
        if True == showtime:
            asctime = colored(datetime.now().strftime('[%Y-%m-%d %H:%M:%S] '), 'green')
        else:
            asctime = ""
        if True == showlevel:
            level = colored(level, attrs=['bold']) + " : "
        else:
            level = ""

        return "{}{}{}\n".format(asctime, level, message)

    @staticmethod
    def warning(message, showtime=True, showlevel=True):
        """Warning level message"""

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
        return "{}{}{}\n".format(asctime, level, message)

    @staticmethod
    def error(message, showtime=True, showlevel=True):
        """Error level message"""

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
        return "{}{}{}\n".format(asctime, level, message)

    @staticmethod
    def debug(message, showtime=True, showlevel=True):
        """Debug level message"""

        level = 'DEBUG'
        if True == showtime:
            asctime = colored(datetime.now().strftime('[%Y-%m-%d %H:%M:%S] '), 'green')
        else:
            asctime = ""
        if True == showlevel:
            level = colored(level, attrs=['bold']) + " : "
        else:
            level = ""

        message = colored(message, 'green')
        return "{}{}{}\n".format(asctime, level, message)

    @staticmethod
    def verbose(message, showtime=True, showlevel=True):
        """Verbose level message"""

        level = 'VERBOSE'
        if True == showtime:
            asctime = colored(datetime.now().strftime('[%Y-%m-%d %H:%M:%S] '), 'green')
        else:
            asctime = ""
        if True == showlevel:
            level = colored(level, attrs=['bold']) + " : "
        else:
            level = ""

        message = colored(message, 'blue')
        return "{}{}{}\n".format(asctime, level, message)

    @staticmethod
    def is_logged(hostname):
        """Check host in logfile"""
        path = os.path.join('Logs', hostname)
        if not os.path.exists(path):
            return False
        else:
            return True

    @staticmethod
    def syslog(key, params):
        """System log (file log)"""

        path = os.path.join('Logs', key)
        if not os.path.exists(path):
            os.makedirs(path)

        params.pop("count", None)
        result = params.get('result')
        for status in result:

            if status in Status.DEFAULT_HTTP_BAD_REQUEST_STATUSES:
                # have redirects urls log
                file = open(os.path.join(path, 'badreqests.log'), 'w')
                for url in result[status]:
                    file.write('{}\n'.format(url))
                file.close()

            if status in Status.DEFAULT_HTTP_REDIRECT_STATUSES:
                # have redirects urls log
                file = open(os.path.join(path, 'redirects.log'), 'w')
                for url in result[status]:
                    file.write('{}\n'.format(url))
                file.close()

            if status in Status.DEFAULT_HTTP_UNRESOLVED_STATUSES:
                # unresolved urls log
                file = open(os.path.join(path, 'possible.log'), 'w')
                for url in result[status]:
                    file.write('{}\n'.format(url))
                file.close()

            if status in Status.DEFAULT_HTTP_SUCCESS_STATUSES:
                # success urls print
                file = open(os.path.join(path, 'success.log'), 'w')
                for url in result[status]:
                    file.write('{}\n'.format(url))
                file.close()

        sys.exit(Logger.info("Your results logs has been created in {0}".format(path)))
