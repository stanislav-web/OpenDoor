# -*- coding: utf-8 -*-

"""Version class"""

import os
import sys
import subprocess
from colorama import init
from distutils.version import LooseVersion
from termcolor import colored

import urllib3

from .FileReader import FileReader
from .Logger import Logger as Log


class Version:
    """Version class"""

    def __init__(self):
        init()

    @staticmethod
    def update():
        """ Checking for app update"""

        CMDUP = '/usr/bin/git pull origin master'
        CMDLOG = '/usr/bin/git log --oneline -n 1'
        Log.success('Checking for updates...')
        pr = subprocess.Popen(CMDUP, cwd=os.getcwd(),
                              shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, error) = pr.communicate()
        sys.stdout.write(Log.success(str(out).rstrip()))
        sys.stdout.write(Log.info(str(error).rstrip()))
        prlog = subprocess.Popen(CMDLOG, cwd=os.getcwd(),
                                 shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        (out, error) = prlog.communicate()
        sys.stdout.write(Log.info(str(out).strip()))

    @staticmethod
    def get_license():
        """ Show license """

        config = FileReader().get_config()
        return config.get('info', 'license')

    @staticmethod
    def get_local_version():
        """ Show local version """

        config = FileReader().get_config()
        return config.get('info', 'version')

    def get_full_version(self):
        """ Show full-version banner"""

        config = FileReader().get_config()

        banner = """
============================================================
  {0} {1} -> {2}
  {3}
  {4}
============================================================
    """.format(
            colored(config.get('info', 'name'), 'blue'),
            self.get_current_version(),
            colored('v' + self.get_remote_version(), 'green'),
            colored("Repo: " + config.get('info', 'repository'), 'yellow'),
            colored(config.get('info', 'license'), 'yellow')
        )
        return banner

    @staticmethod
    def get_remote_version():
        """ Show remote version """

        config = FileReader()
        if hasattr(urllib3, 'disable_warnings'):
            urllib3.disable_warnings()
        http = urllib3.PoolManager()
        response = http.request('GET', config.get_config().get('info', 'setup'))
        config = config.get_config_raw(response.data)
        return config.get('info', 'version')

    def get_current_version(self):
        """ Get current app version """

        remote = self.get_remote_version()
        local = self.get_local_version()

        if LooseVersion(local) < LooseVersion(remote):
            version = colored('v' + local, 'red')
        else:
            version = colored('v' + local, 'green')
        return version

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

    def banner(self):
        """ Load application banner """

        banner = """
    ############################################################
    #                                                          #
    #   _____  ____  ____  _  _    ____   _____  _____  ____   #
    #  (  _  )(  _ \( ___)( \( )  (  _ \ (  _  )(  _  )(  _ \  #
    #   )(_)(  )___/ )__)  )  (    )(_) ) )(_)(  )(_)(  )   /  #
    #  (_____)(__)  (____)(_)\_)  (____/ (_____)(_____)(_)\_)  #
    #                                                          #
    #  {0}\t\t                       #
    #  {1}\t\t                       #
    #  {2}\t\t\t                       #
    #  {3}\t\t\t                       #
    #  {4}                     #
    ############################################################
        """.format(
            colored('Directories: ' + str(self.get_directories_count()), 'yellow'),
            colored('Subdomains: ' + str(self.get_subdomains_count()), 'yellow'),
            colored('Browsers: ' + str(self.get_user_agents_count()), 'yellow'),
            colored('Proxies: ' + str(self.get_proxy_count()), 'yellow'),
            colored(self.get_license(), 'yellow'),
        )
        sys.stdout.write("{0}\n".format(banner))
