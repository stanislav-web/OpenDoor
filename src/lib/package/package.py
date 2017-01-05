# -*- coding: utf-8 -*-

"""Package class"""

from src.core import sys, process, filesystem, helper
from .config import Config
#TODO
from ...lib.exceptions import LibError

class Package:
    """Package class"""

    remote_version = None

    @staticmethod
    def examples():
        """ load usage examples """

        sys.exit(Config.params['examples'])

    @staticmethod
    def banner():
        """ load application banner """

        banner = Config.params['banner'].format(
            'Directories: {0}'.format(Package.__directories_count()),
            'Subdomains: {0}'.format(Package.__subdomains_count()),
            'Browsers: {0}'.format(Package.__browsers_count()),
            'Proxies: {0}'.format(Package.__proxies_count()),
            Package.__license(), 'yellow')

        sys.writeln(banner)

    @staticmethod
    def version():
        """ load application version """

        banner = Config.params['version'].format(
            Package.__app_name(),
            Package.__current_version(),
            Package.__remote_version(),
            Package.__repo(),
            Package.__license(),
            'yellow')

        sys.writeln(banner)

    @staticmethod
    def update():
        """ check for update"""

        #Log.success('Checking for updates...')
        status = process.open(Config.params['cvsupdate'])

        sys.writeln(str(status[0]).rstrip())
        sys.writeln(str(status[1]).rstrip())
        # sys.stdout.write(Log.success(str(out).rstrip()))
        # sys.stdout.write(Log.info(str(error).rstrip()))

        status = process.open(Config.params['cvslog'])
        sys.exit(str(status[0]).rstrip())
        #sys.stdout.write(Log.info(str(out).strip()))

    @staticmethod
    def __app_name():
        """ get app name """

        config = filesystem.readcfg(Config.params['cfg'])
        return config.get('info', 'name')

    @staticmethod
    def __local_version():
        """ get local version """

        config = filesystem.readcfg(Config.params['cfg'])
        return config.get('info', 'version')

    @staticmethod
    def __remote_version():
        """ get remote version """

        if None is Package.remote_version:
            config = filesystem.readcfg(Config.params['cfg'])
            request_uri = config.get('info', 'setup')
            result = process.open('curl -sb GET {uri}'.format(uri = request_uri))
            raw = filesystem.readraw(result[0])
            Package.remote_version = raw.get('info', 'version')
            return Package.remote_version
        else:
            return Package.remote_version

    @staticmethod
    def __current_version():
        """ get current version """

        local = Package.__local_version()
        remote = Package.__remote_version()

        if True is helper.is_less(local, remote):
            # @TODO red
            version = local
        else:
            # @TODO green
            version = local
        return version

    @staticmethod
    def __repo():
        """ get repo """

        config = filesystem.readcfg(Config.params['cfg'])
        return config.get('info', 'repository')

    @staticmethod
    def __license():
        """ get license """

        config = filesystem.readcfg(Config.params['cfg'])
        return config.get('info', 'license')

    @staticmethod
    def __directories_count():
        """ Get number of directories in basic wordlist"""

        config = filesystem.readcfg(Config.params['cfg'])
        filename = config.get('opendoor', 'directories')
        count = filesystem.read(filename).__len__()

        return count

    @staticmethod
    def __subdomains_count():
        """ Get number of subdomains in basic wordlist"""

        config = filesystem.readcfg(Config.params['cfg'])
        filename = config.get('opendoor', 'subdomains')
        count = filesystem.read(filename).__len__()

        return count

    @staticmethod
    def __browsers_count():
        """ Get number of browsers in basic wordlist"""

        config = filesystem.readcfg(Config.params['cfg'])
        filename = config.get('opendoor', 'useragents')
        count = filesystem.read(filename).__len__()

        return count

    @staticmethod
    def __proxies_count():
        """ Get number of proxy servers in basic wordlist"""

        config = filesystem.readcfg(Config.params['cfg'])
        filename = config.get('opendoor', 'proxy')
        count = filesystem.read(filename).__len__()

        return count