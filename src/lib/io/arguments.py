# -*- coding: utf-8 -*-

"""Arguments class"""
from src.core import options , OptionsError
from src.core import sys

class Arguments:
    """Arguments class"""

    @staticmethod
    def get():
        try:
            args = options().get_arg_values()
            return args
        except OptionsError as e:
            sys.exit(e.message)


