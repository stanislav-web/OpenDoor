# -*- coding: utf-8 -*-

"""Arguments class"""
from src.core import options , OptionsError
from ...lib.exceptions import LibError

class Arguments:
    """Arguments class"""

    @staticmethod
    def get_arguments():

        try:
            args = options().get_arg_values()
            return args
        except OptionsError as e:
            raise LibError(e.message)


