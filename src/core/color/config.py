# -*- coding: utf-8 -*-

"""Config classes """


class Config:
    """Config class"""

    default = 'white'

    @staticmethod
    def get(key):

        colorlist = {
            'black' : 0,
            'red' : 1,
            'green' : 2,
            'yellow' : 3,
            'blue' : 4,
            'magenta' : 5,
            'cyan' : 6,
            'white' : 7
        }

        if key in colorlist:
            return colorlist[key]
        else:
            return colorlist[Config.default]


