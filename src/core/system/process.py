# -*- coding: utf-8 -*-

"""Process class"""

import subprocess
import os

class Process:
    """Process class"""

    @staticmethod
    def open(command):
        pr = subprocess.Popen(command, cwd=os.getcwd(),
                              shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        (out, error) = pr.communicate()
        return (out, error)