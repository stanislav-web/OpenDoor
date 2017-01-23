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

    Development Team: Stanislav WEB
"""

import ConfigParser
import StringIO
import errno
import os

from .exceptions import FileSystemError


class FileSystem:
    """FileSystem class"""

    @staticmethod
    def is_exist(dir, filename):
        """
        Check if dir-file is exist
        :param str dir: directory
        :param str filename: filename
        :return: bool
        """

        path = os.path.join(dir, filename)
        if not os.path.exists(path):
            return False
        else:
            return True

    @staticmethod
    def makedir(dir, mode=0777):
        """
        Create new directory

        :param str dir: directory
        :param int permission: directory permission
        :raise: FileSystemError
        :return: None
        """
        if not os.path.exists(dir):
            try:
                dir = os.path.join(os.getcwd(), dir)
                os.makedirs(dir + '/', mode=mode)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise FileSystemError("Cannot create directory `{0}`. Reason: {1}".format(dir, e.message))
        pass

    @staticmethod
    def getabsname(filename):

        """
        Get absolute file path
        :param str filename: directory
        :return: str
        """

        filename = os.path.join(os.getcwd(), filename)
        return os.path.abspath(filename)

    @staticmethod
    def makefile(filename):
        """
        Create new file with context
        :param str filename: directory
        :param str destination:
        :param str context:
        :raise: FileSystemError
        :return: Bool
        """

        filename = os.path.join(os.getcwd(), filename)

        if False is os.path.exists(filename):
            try:
                FileSystem.makedir(os.path.dirname(filename))
                open(filename, 'w')

                return True
            except IOError as e:
                raise FileSystemError(e)
        else:
            return False

    @staticmethod
    def readline(filename, handler, handler_params, loader):
        """
        Read txt file line by line
        :param str filename: source file name
        :param func handler: url handler
        :param func handler_params: url handler parameters
        :param func loader: browser
        :raise FileSystemError
        :return: str
        """

        file = os.path.join(os.getcwd(), filename)
        if not os.path.isfile(file):
            raise FileSystemError("{0} is not a file ".format(file))
        if not os.access(file, os.R_OK):
            raise FileSystemError("Configuration file {0} can not be read. Setup chmod 0644".format(file))

        with open(file, "r") as f_handler:
            for i, line in enumerate(f_handler):
                line = handler(line, handler_params)
                loader(line)

    @staticmethod
    def read(filename):
        """
        Read .txt file
        :param str filename: read filename
        :raise FileSystemError
        :return: list
        """

        file = os.path.join(os.getcwd(), filename)
        if not os.path.isfile(file):
            raise FileSystemError("{0} is not a file ".format(file))
        if not os.access(file, os.R_OK):
            raise FileSystemError("Configuration file {0} can not be read. Setup chmod 0644".format(file))

        with open(file, "r") as f_handler:
            data = f_handler.readlines()
        return data

    @staticmethod
    def readcfg(filename):
        """
        Read .cfg file
        :param str filename: read filename
        :raise FileSystemError
        :return: ConfigParser.RawConfigParser
        """

        file = os.path.join(os.getcwd(), filename)
        if not os.path.isfile(file):
            raise FileSystemError("{0} is not a file ".format(file))
        if not os.access(file, os.R_OK):
            raise FileSystemError("Configuration file {0} can not be read. Setup chmod 0644".format(file))

        try:
            config = ConfigParser.RawConfigParser()
            config.read(file)
            return config
        except ConfigParser.ParsingError as e:
            raise FileSystemError(e.message)

    @staticmethod
    def readraw(data):
        """
        Read .cfg raw data file
        :param str data: file data
        :raise FileSystemError
        :return: ConfigParser.RawConfigParser
        """

        buf = StringIO.StringIO(data)
        try:
            config = ConfigParser.ConfigParser()
            config.readfp(buf)
            return config
        except ConfigParser.Error as e:
            raise FileSystemError(e.message)

    @staticmethod
    def human_size(size, precision=2):
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        suffix_index = 0
        size = int(size)
        while size > 1024 and suffix_index < 4:
            suffix_index += 1
            size = size / 1024.0

        return "%.*f%s" % (precision, size, suffixes[suffix_index])
