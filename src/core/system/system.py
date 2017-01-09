# -*- coding: utf-8 -*-

"""System class"""

import sys

class System:
    """System class"""

    lastln = False

    @staticmethod
    def exit(string):
        """console abort"""

        sys.exit(string)

    @staticmethod
    def writels(string):
        """ write in line """

        System.__clean()
        sys.stdout.write(string)
        sys.stdout.flush()
        System.lastln = True

    @staticmethod
    def writeln(string):
        """ write new line """

        if True == System.lastln:
            System.__clean()
        sys.stdout.write('{0}\n'.format(string))
        sys.stdout.flush()
        System.lastln = False
        sys.stdout.flush()

    @staticmethod
    def __clean():
        """ clean tpl line """

        sys.stdout.write('\033[1K')
        sys.stdout.write('\033[0G')

