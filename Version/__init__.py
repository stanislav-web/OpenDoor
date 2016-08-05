"""
This example module shows various types of documentation available for use
with pydoc.  To generate HTML documentation for this module issue the
command:

    pydoc -w foo

"""
from Libraries.Logger import Logger as log

try:
    import sys
    import subprocess
    import os
    import urllib3
    import httplib2
    from distutils.version import LooseVersion

    from colorama import init
    from termcolor import colored
    from Libraries.FileReader import FileReader

except ImportError:
    log.critical("""You need urllib3, colorama and termcolor!
                install it from http://pypi.python.org/pypi
                or run pip install colorama termcolor urllib3.""")

init()

CMD = '/usr/bin/git pull origin master'


def update():
    log.success('Checking for updates...')
    pr = subprocess.Popen(CMD, cwd=os.getcwd(),
                          shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, error) = pr.communicate()
    log.success(str(out))
    log.info(str(error))


def get_license():
    config = FileReader().get_config()
    return config.get('info', 'license')

def get_local_version():
    config = FileReader().get_config()
    return config.get('info', 'version')

def get_full_version():
    config = FileReader().get_config()

    banner = """
============================================================
  %s {%s} -> {%s}
  %s
  %s
============================================================
    """ %   (
                colored(config.get('info', 'name'), 'blue'),
                get_current_version(),
                colored('v' +get_remote_version(), 'green'),
                colored("Repo: " + config.get('info', 'repository'), 'yellow'),
                colored(config.get('info', 'license'), 'yellow')
            )
    return banner

def get_remote_version():
    config = FileReader()
    if hasattr(urllib3, 'disable_warnings'):
        urllib3.disable_warnings()
    http = urllib3.PoolManager()
    response = http.request('GET', config.get_config().get('info', 'setup'))
    config = config.get_config_raw(response.data)
    return config.get('info', 'version')

def get_current_version():
    remote = get_remote_version()
    local = get_local_version()

    if LooseVersion(local) < LooseVersion(remote):
        version = colored('v' + local, 'red')
    else:
        version = colored('v' + local, 'green')
    return version

def get_directories_count():
    return FileReader().get_file_data('directories').__len__()

def get_subdomains_count():
    return FileReader().get_file_data('subdomains').__len__()

def banner():
    banner = """
    ############################################################
    #                                                          #
    #   _____  ____  ____  _  _    ____   _____  _____  ____   #
    #  (  _  )(  _ \( ___)( \( )  (  _ \ (  _  )(  _  )(  _ \  #
    #   )(_)(  )___/ )__)  )  (    )(_) ) )(_)(  )(_)(  )   /  #
    #  (_____)(__)  (____)(_)\_)  (____/ (_____)(_____)(_)\_)  #
    #                                                          #
    #  %s\t\t                       #
    #  %s\t\t\t                       #
    #  %s                     #
    ############################################################
    """ % (
                colored('DB Directories: ' + str(get_directories_count()), 'yellow'),
                colored('DB Subdomains: ' + str(get_subdomains_count()), 'yellow'),
                colored(get_license(), 'yellow'),
          )

    print banner