# -*- coding: utf-8 -*-

"""Arguments class"""
from src.core import options , OptionsError, CoreError

class Arguments:
    """Arguments class"""

    @staticmethod
    def get():
        try:
            args = options().get_arg_values()
            return args
        except OptionsError as e:
            print e
            raise CoreError(e.message)


