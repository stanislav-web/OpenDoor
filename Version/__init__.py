try:
    import sys
    import subprocess
    import os
    import urllib3
    from distutils.version import LooseVersion

    from colorama import init
    from termcolor import colored
    from Libraries.FileReader import FileReader

except ImportError:
    sys.exit("""You need colorama and termcolor!
                install it from http://pypi.python.org/pypi
                or run pip install colorama termcolor .""")

init()

CMD = '/usr/bin/git pull origin master'


def update():
    pr = subprocess.Popen(CMD, cwd=os.getcwd(),
                          shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, error) = pr.communicate()
    print "Error : " + str(error)
    print "out : " + str(out)


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
                colored(config.get('info', 'repository'), 'blue'),
                colored(config.get('info', 'license'), 'blue')
            )
    return banner

def get_remote_version():
    config = FileReader().get_config()

    http = urllib3.PoolManager()
    http.headers[':authority:'] = 'bitbucket.org'
    http.headers[':method:'] = 'GET'
    http.headers[':path:'] = '/stanislav-web/opendoor/raw/master/setup.cfg'
    http.headers[':scheme:'] = 'http'

    response = http.request('GET', config.get('info', 'setup'))

    config = FileReader().get_config_raw(response.data)
    return config.get('info', 'version')

def get_current_version():
    remote = get_remote_version()
    local = get_local_version()

    if LooseVersion(local) < LooseVersion(remote):
        version = colored('v' + local, 'red')
    else:
        version = colored('v' + local, 'green')
    return version

def get_examples():
    examples = """
    Examples:
        ./opendoor.py --url "http://owasp.com"
        ./opendoor.py --url "http://owasp.com" --threads 10
        ./opendoor.py --url "http://owasp.com" --threads 10 --check="dir" (sub)
        ./opendoor.py --url "http://owasp.com" --threads 1 --dalay 10 --check="dir" (sub. dir is default)
        ./opendoor.py --url "http://owasp.com" --threads 1 --dalay 10 --random-agents
        ./opendoor.py --url "http://owasp.com" --threads 1 --dalay 10 --random-agents --proxy-list="proxy.dat"
        """
    return examples

def print_banner():
    banner = """
    ############################################################
    #                                                          #
    #   _____  ____  ____  _  _    ____   _____  _____  ____   #
    #  (  _  )(  _ \( ___)( \( )  (  _ \ (  _  )(  _  )(  _ \  #
    #   )(_)(  )___/ )__)  )  (    )(_) ) )(_)(  )(_)(  )   /  #
    #  (_____)(__)  (____)(_)\_)  (____/ (_____)(_____)(_)\_)  #
    #                                                          #
    #  {%s}                                                    #
    ############################################################
    """ % get_current_version()
    print banner