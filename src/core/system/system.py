# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development Team: Stanislav Menshov
"""

import sys

class System:
    """System class"""

    lastln = False

    @staticmethod
    def exit(msg):
        """
        Abort session

        :param str msg: text message
        :return: None
        """

        sys.exit(msg)

    @staticmethod
    def writels(msg):
        """
        Write in line

        :param str msg: text message
        :return: None
        """

        System.__clean()
        sys.stdout.write(msg)
        sys.stdout.flush()
        System.lastln = True

    @staticmethod
    def writeln(msg):
        """
        Write new line

        :param str msg: text message
        :return: None
        """

        if True is System.lastln:
            System.__clean()
        sys.stdout.write('{0}\n'.format(msg))
        sys.stdout.flush()
        System.lastln = False
        sys.stdout.flush()

    @staticmethod
    def __clean():
        """
        Clean line

        :return: None
        """

        sys.stdout.write('\033[1K')
        sys.stdout.write('\033[0G')

