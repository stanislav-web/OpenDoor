# -*- coding: utf-8 -*-

"""Helper class"""


from distutils.version import LooseVersion

class Helper:
    """Helper class"""

    @staticmethod
    def is_less(arg1, arg2):
        if LooseVersion(arg1) < LooseVersion(arg2):
            return True
        else:
            return False

