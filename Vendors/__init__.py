try:
    import sys
    import subprocess
    import os
    import json
    import urllib3

    from colorama import init
    from termcolor import colored
    from Version import get_versions
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


def get_version():
    return get_versions()['version']

def get_full_version():
    config = FileReader().get_config()

    BANNER = """
============================================================
  %s
  %s
  %s
  %s
============================================================
    """ %   (
                colored(config.get('info', 'name'), 'blue'),
                colored(get_versions()['version'], 'blue'),
                colored(config.get('info', 'repository'), 'blue'),
                colored(config.get('info', 'license'), 'blue')
            )
    return BANNER

def load_remote_version():
    config = FileReader().get_config()
    r = urllib3.connection_from_url(config.get('info', 'setup'))
    response = r.request('GET', '/')
    data = json.load(response)
    print data

