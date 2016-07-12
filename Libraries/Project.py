import subprocess
import os

class Project:
    """Project class"""
    def __init__(self):
        self.UPDATE_CMD = '/usr/bin/git pull origin master'

    def update(self):
        pr = subprocess.Popen(self.UPDATE_CMD, cwd=os.getcwd(),
                              shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, error) = pr.communicate()
        print "Error : " + str(error)
        print "out : " + str(out)