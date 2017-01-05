# -*- coding: utf-8 -*-

"""Process class"""

import subprocess
import os
from .exceptions import SystemError


class Process:
    """Process class"""

    @staticmethod
    def open(command):

        try:
            pr = subprocess.Popen(command, cwd=os.getcwd(),
                                  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            (out, error) = pr.communicate()
            return (out, error)

        except subprocess.CalledProcessError as e:
            raise SystemError(e)
