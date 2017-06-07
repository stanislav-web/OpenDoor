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

from configparser import ConfigParser, RawConfigParser, ParsingError, NoOptionError, Error
import errno
import os
from io import StringIO
import random
import re

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
    def makedir(directory, mode=0o777):
        """
        Create new directory

        :param str directory: directory
        :param int mode: directory permission
        :raise: FileSystemError
        :return: None
        """

        if not os.path.exists(directory):
            try:
                directory = os.path.join(directory)
                os.makedirs(directory + '/', mode=mode)
            except OSError as error:
                if error.errno != errno.EEXIST:
                    raise FileSystemError("Cannot create directory `{0}`. Reason: {1}".format(directory, error))

    @staticmethod
    def getabsname(filename):
        """
        Get absolute file path
        :param str filename: directory
        :return: str
        """

        filename = os.path.join(filename)
        return os.path.abspath(filename)

    @staticmethod
    def get_extension(line):
        """
        Get extension from line
        :param str line: input string
        :return: str
        """

        ext = os.path.splitext(line)[-1]
        return ext

    @staticmethod
    def has_extension(line):
        """
        Check line for extension
        :param str line: input string
        :return: bool
        """

        ext = FileSystem.get_extension(line)
        return True if 0 < len(ext) else False

    @staticmethod
    def filter_file_lines(dirlist, pattern):
        """
        Filter lines by regex pattern

        :param list dirlist:
        :param str pattern:
        :return: list
        """

        r = re.compile(pattern)
        newlist = filter(r.match, dirlist)
        filteredlist = list(newlist)

        return filteredlist

    @staticmethod
    def clear(directory, extension=''):
        """
        Clear directory
        :param str directory: os directory
        :param str extension: extension
        :raise: FileSystemError
        :return: Bool
        """

        if True is os.path.exists(directory):
            try:
                for files in os.listdir(directory):
                    filename = os.path.join(directory, files)
                    file_extension = os.path.splitext(filename)[1]
                    if extension == file_extension:
                        os.remove(os.path.join(directory, files))
            except IOError as error:
                raise FileSystemError(error.strerror)
        else:
            raise FileSystemError("The directory {0} you want to clear is not exist".format(directory))

    @staticmethod
    def makefile(filename):
        """
        Create new file with context
        :param str filename: input filename
        :raise: FileSystemError
        :return: Bool
        """

        filename = os.path.join(filename)

        if False is os.path.exists(filename):
            try:
                FileSystem.makedir(os.path.dirname(filename))
                open(filename, 'w')

                return True
            except IOError as error:
                raise FileSystemError(error.strerror)
        else:
            return False

    @staticmethod
    def shuffle(target, output, total):
        """
        Shuffle data in file
        :param str target: target file
        :param str output: suffled file
        :param int total: total lines
        :return: bool
        """

        try:
            i_f = open(target)
            o_f = open(output, 'wb')
            counter = sum(1 for _ in i_f)
            order = list(range(counter))
            random.shuffle(order)
            while order:
                current_lines = {}
                current_lines_count = 0
                current_chunk = order[:total]
                current_chunk_dict = dict((x, 1) for x in current_chunk)
                current_chunk_length = len(current_chunk)
                order = order[total:]
                i_f.seek(0)
                count = 0

                for line in i_f:
                    if count in current_chunk_dict:
                        current_lines[count] = line
                        current_lines_count += 1
                        if current_lines_count == current_chunk_length:
                            break
                    count += 1

                for node in current_chunk:
                    o_f.write(current_lines[node].encode())

        except IOError as error:
            raise FileSystemError(error.strerror)

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

        filepath = os.path.join(filename)
        if not os.path.isfile(filepath):
            raise FileSystemError("{0} is not a file ".format(filepath))
        if not os.access(filepath, os.R_OK):
            raise FileSystemError("Configuration file {0} can not be read. Setup chmod 0644".format(filepath))

        lines = []
        with open(filepath) as f_handler:
            for line in f_handler:
                lines.append(handler(line, handler_params))
            loader(lines)

    @staticmethod
    def read(filename):
        """
        Read .txt file
        :param str filename: input filename
        :raise FileSystemError
        :return: list
        """

        filepath = os.path.join(filename)

        if not os.path.isfile(filepath):
            raise FileSystemError("{0} is not a file ".format(filename))
        if not os.access(filepath, os.R_OK):
            raise FileSystemError("Configuration file {0} can not be read. Setup chmod 0644".format(filepath))

        with open(filepath) as f_handler:
            data = f_handler.readlines()
        return data

    @staticmethod
    def readcfg(filename):
        """
        Read .cfg file
        :param str filename: input filename
        :raise FileSystemError
        :return: configparser.RawConfigParser
        """

        #TODO : Win32/64 check this ^(([(\/|\)a-z].*?opendoor.*?)(\/|\\))
        expression = '^([\/a-z].*?opendoor.*?)\/'
        regex = re.compile(expression, re.IGNORECASE)
        cwd = regex.search(__file__)
        os.chdir(cwd.group())
        filepath = os.path.join(os.path.sep, os.getcwd(), filename)

        if not os.path.isfile(filepath):
            raise FileSystemError("{0} is not a file ".format(filepath))
        if not os.access(filepath, os.R_OK):
            raise FileSystemError("Configuration file {0} can not be read. Setup chmod 0644".format(filepath))

        try:

            config = RawConfigParser()
            config.read(filepath)
            return config

        except (ParsingError, NoOptionError) as error:
            raise FileSystemError(error)

    @staticmethod
    def writelist(filename, data, separator=''):
        """
        Write list to file
        :param str filename: input filename
        :param list data: record data
        :param str separator: line separator
        :raise FileSystemError
        :return: None
        """

        filepath = os.path.join(filename)
        if not os.path.isfile(filepath):
            raise FileSystemError("{0} is not a file ".format(filename))
        if not os.access(filepath, os.W_OK):
            raise FileSystemError("Targeting file {0} is not writable. Please, check access".format(filepath))

        with open(filepath, "w") as f_handler:
            f_handler.write(separator.join(data))

    @staticmethod
    def readraw(data):
        """
        Read .cfg raw data file
        :param str data: file data
        :raise FileSystemError
        :return: configparser.RawConfigParser
        """

        buf = StringIO(str(data, "utf-8"))
        try:
            config = ConfigParser()
            config.read_file(buf)
            return config
        except Error as error:
            raise FileSystemError(str(error))

    @staticmethod
    def human_size(size, precision=2):
        """
        Humanize accepted bytes
        :param int size: bytes
        :param int precision: delimiter
        :return:
        """

        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        suffix_index = 0
        size = int(size)
        while size > 1024 and suffix_index < 4:
            suffix_index += 1
            size /= 1024

        return "%.*f%s" % (precision, size, suffixes[suffix_index])
