import subprocess
import os
from Version import get_versions
from Colors import init

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
    str = "============================================================\n"
    str += Colors.colored("\tOpendoor hackware\n", 'blue')
    str += Colors.colored("\tVersion: " + get_versions()['version'] + "\n", 'green')
    str += "============================================================\n"
    print str
    exit()
