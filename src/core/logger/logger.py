# -*- coding: utf-8 -*-

"""Logger class"""


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
    def is_logged(filename):
        """Check host in logfile"""

        path = os.path.join('logs', filename)
        if not os.path.exists(path):
            return False
        else:
            return True

    @staticmethod
    def syslog(directory, filename, items):
        """System log (file log)"""

        path = os.path.join('logs', directory)
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                file = open(os.path.join(path, filename), 'w')
                for item in items:
                    file.write('{}\n'.format(item))
                file.close()
            except OSError as e:
                sys.exit(e.message)