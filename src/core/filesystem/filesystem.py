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


class FileSystem(object):
    """FileSystem class"""

    sep = os.sep

    @staticmethod
    def is_exist(directory, filename):
        """
        Check if dir-file is exist
        :param str directory: directory
        :param str filename: filename
        :return: bool
        """

        path = os.path.join(directory, filename)
        if not os.path.exists(path):
            return False
        else:
            return True

    @staticmethod
    def makedir(directory, mode=0777):
        """
        Create new directory

        :param str directory: directory
        :param int permission: directory permission
        :raise: FileSystemError
        :return: None
        """

        if not os.path.exists(directory):
            try:
                directory = os.path.join(os.getcwd(), directory)
                os.makedirs(directory + '/', mode=mode)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise FileSystemError("Cannot create directory `{0}`. Reason: {1}".format(directory, e.message))

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
    def has_extension(line):
        """
        Check line for extension
        :param str line:
        :return: bool
        """

        ext = os.path.splitext(line)[-1]
        return True if 0 < len(ext) else False

    @staticmethod
    def clear(directory):
        """
        Clear directory
        :param str filename: directory
        :raise: FileSystemError
        :return: Bool
        """

        if True is os.path.exists(directory):
            try:
                for root, dirs, files in os.walk(directory):
                    for name in files:
                        os.remove(os.path.join(root, name))
            except IOError as e:
                raise FileSystemError(e)
        else:
            raise FileSystemError("The directory {0} you want to clear is not exist".format(directory))

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

        filepath = os.path.join(os.getcwd(), filename)
        if not os.path.isfile(filepath):
            raise FileSystemError("{0} is not a file ".format(filepath))
        if not os.access(filepath, os.R_OK):
            raise FileSystemError("Configuration file {0} can not be read. Setup chmod 0644".format(filepath))

        lines = []
        with open(filepath, "r") as f_handler:
            for line in f_handler:
                lines.append(handler(line, handler_params))
            loader(lines)

    @staticmethod
    def read(filename):
        """
        Read .txt file
        :param str filename: read filename
        :raise FileSystemError
        :return: list
        """

        filepath = os.path.join(os.getcwd(), filename)
        if not os.path.isfile(filepath):
            raise FileSystemError("{0} is not a file ".format(file))
        if not os.access(filepath, os.R_OK):
            raise FileSystemError("Configuration file {0} can not be read. Setup chmod 0644".format(filepath))

        with open(filepath, "r") as f_handler:
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

        filepath = os.path.join(os.getcwd(), filename)
        if not os.path.isfile(filepath):
            raise FileSystemError("{0} is not a file ".format(filepath))
        if not os.access(filepath, os.R_OK):
            raise FileSystemError("Configuration file {0} can not be read. Setup chmod 0644".format(filepath))

        try:
            config = ConfigParser.RawConfigParser()
            config.read(filepath)
            return config
        except ConfigParser.ParsingError as e:
            raise FileSystemError(e.message)

    @staticmethod
    def writelist(filename, data):
        """
        Write list to file
        :param str filename: write filename
        :param list data: list data
        :raise FileSystemError
        :return: None
        """

        filepath = os.path.join(os.getcwd(), filename)
        if not os.path.isfile(filepath):
            raise FileSystemError("{0} is not a file ".format(file))
        if not os.access(filepath, os.W_OK):
            raise FileSystemError("Targeting file {0} is not writable. Please, check access".format(filepath))

        with open(filepath, "w") as f_handler:
            f_handler.write("\n".join(data))

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
        """
        Humanize accepted bytes
        :param int size:
        :param int precision:
        :return:
        """

        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        suffix_index = 0
        size = int(size)
        while size > 1024 and suffix_index < 4:
            suffix_index += 1
            size = size / 1024.0

        return "%.*f%s" % (precision, size, suffixes[suffix_index])
