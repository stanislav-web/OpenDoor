# -*- coding: utf-8 -*-

"""Package class"""

from src.core import sys, process, filesystem, helper

from .config import Config

class Package:
    """Package class"""

    @staticmethod
    def load_examples():
        """ load usage examples """

        sys.exit(Config.params['examples'])

    @staticmethod
    def banner():
        """ load application banner """

        banner = Config.params['banner'].format(
           'Directories: ' + str(0),
            'Subdomains: ' + str(0),
            'Browsers: ' + str(0),
            'Proxies: ' + str(0),
            str(0), 'yellow')

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
    def get_directories_count():
        """ Get directories counter from directories list"""

        return FileReader().get_file_data('directories').__len__()

    @staticmethod
    def get_subdomains_count():
        """ Get subdomains counter from subdomains list"""

        return FileReader().get_file_data('subdomains').__len__()

    @staticmethod
    def get_user_agents_count():
        """ Get user agents counter from user-agents list"""

        return FileReader().get_file_data('useragents').__len__()

    @staticmethod
    def get_proxy_count():
        """ Get proxy counter from proxy list """

        return FileReader().get_file_data('proxy').__len__()



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

        config = filesystem.readcfg(Config.params['cfg'])
        request_uri = config.get('info', 'setup')

        # @TODO
        # response = http.request('GET', request_uri)
        # raw = filesystem.readraw(response.data)
        # return raw.get('info', 'version')

        return "2.1"

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