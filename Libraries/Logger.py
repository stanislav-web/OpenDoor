import coloredlogs

class Logger:
    """Message helper class"""

    @staticmethod
    def success(string):
        coloredlogs.install(level='INFO', fmt='[%(asctime)s] %(levelname)s : %(message)s')
        coloredlogs.install(level='INFO')
        logger = Logger.log('INFO');
        logger.success(string);
        pass

    @staticmethod
    def warning(string):
        coloredlogs.install(level='WARNING', fmt='[%(asctime)s] %(levelname)s : %(message)s')
        coloredlogs.install(level='WARNING')
        logger = Logger.log('WARNING');
        logger.warning(string);
        pass

    @staticmethod
    def error(string):
        coloredlogs.install(level='ERROR', fmt='[%(asctime)s] %(levelname)s : %(message)s')
        coloredlogs.install(level='ERROR')
        logger = Logger.log('ERROR');
        logger.error(string);
        pass

    @staticmethod
    def critical(string):
        coloredlogs.install(level='CRITICAL', fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log('CRITICAL');
        logger.critical(string);
        exit();

    @staticmethod
    def debug(string):
        coloredlogs.install(level='DEBUG', fmt='[%(asctime)s] %(levelname)s : %(message)s')
        logger = Logger.log('DEBUG');
        logger.debug(string);
        pass

    @staticmethod
    def verbose(string):
        coloredlogs.install(level='VERBOSE', fmt='[%(asctime)s] %(levelname)s : %(message)s')
        coloredlogs.install(level='VERBOSE')
        logger = Logger.log('DEBUG');
        logger.debug(string);
        pass

    @classmethod
    def log(cls, level):

        import logging

        # set logger level from parent class
        logger = logging.getLogger()
        # add the handlers to the logger
        logger.setLevel(getattr(logging, level))

        return logger
