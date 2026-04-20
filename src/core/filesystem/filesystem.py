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

    Development Team: Brain Storm Team
"""

from configparser import RawConfigParser, ParsingError, NoOptionError
import errno
import os
import random
import re

from .exceptions import FileSystemError


class FileSystem(object):

    """FileSystem class"""

    sep = os.sep
    text_encoding = 'utf-8'
    READLINE_BATCH_SIZE = 2048

    @staticmethod
    def _project_root():
        """
        Return the project root directory.

        :return: str
        """

        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

    @staticmethod
    def _iter_file_candidates(filename, include_home=False, include_project_root=False):
        """
        Build candidate file paths for lookups.

        :param str filename:
        :param bool include_home:
        :param bool include_project_root:
        :return: list
        """

        candidates = []

        if os.path.isabs(filename):
            candidates.append(filename)
        else:
            candidates.append(os.path.abspath(filename))

            if include_project_root:
                candidates.append(os.path.abspath(os.path.join(FileSystem._project_root(), filename)))

            if include_home:
                candidates.append(os.path.abspath(os.path.join(os.path.expanduser('~'), filename)))

        unique_candidates = []
        for candidate in candidates:
            if candidate not in unique_candidates:
                unique_candidates.append(candidate)
        return unique_candidates

    @staticmethod
    def _resolve_readable_file(filename, include_home=False, include_project_root=False):
        """
        Resolve a readable file path.

        :param str filename:
        :param bool include_home:
        :param bool include_project_root:
        :raise FileSystemError:
        :return: str
        """

        candidates = FileSystem._iter_file_candidates(
            filename,
            include_home=include_home,
            include_project_root=include_project_root,
        )

        for candidate in candidates:
            if os.path.isfile(candidate):
                if os.access(candidate, os.R_OK):
                    return candidate
                raise FileSystemError(
                    "Configuration file {0} can not be read. Setup chmod 0644".format(candidate)
                )

        raise FileSystemError("{0} is not a file ".format(filename))

    @staticmethod
    def _resolve_writable_file(filename):
        """
        Resolve a writable file path.

        :param str filename:
        :raise FileSystemError:
        :return: str
        """

        filepath = os.path.abspath(filename)

        if not os.path.isfile(filepath):
            raise FileSystemError("{0} is not a file ".format(filename))
        if not os.access(filepath, os.W_OK):
            raise FileSystemError(
                "Targeting file {0} is not writable. Please, check access".format(filepath)
            )

        return filepath

    @staticmethod
    def is_exist(directory, filename):
        """
        Check if dir-file is exist.

        :param str directory:
        :param str filename:
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
        Create new directory.

        :param str directory:
        :param int mode:
        :raise FileSystemError:
        :return: str
        """

        target = directory or os.curdir
        error_message = None
        candidates = [target]

        if not os.path.isabs(target):
            candidates.append(os.path.join(os.path.expanduser('~'), target))

        for candidate in candidates:
            try:
                os.makedirs(candidate, mode=mode, exist_ok=True)
                if os.access(candidate, os.W_OK):
                    return candidate
            except OSError as error:
                if error.errno != errno.EEXIST:
                    error_message = error

        if error_message is None:
            error_message = "Permission denied"

        raise FileSystemError("Cannot create directory `{0}`. Reason: {1}".format(directory, error_message))

    @staticmethod
    def getabsname(filename):
        """
        Get absolute file path.

        :param str filename:
        :return: str
        """

        filename = os.path.join(filename)
        return os.path.abspath(filename)

    @staticmethod
    def get_extension(line):
        """
        Get extension from line.

        :param str line:
        :return: str
        """

        ext = os.path.splitext(line)[-1]
        return ext

    @staticmethod
    def has_extension(line):
        """
        Check line for extension.

        :param str line:
        :return: bool
        """

        ext = FileSystem.get_extension(line)
        return True if 0 < len(ext) else False

    @staticmethod
    def filter_file_lines(dirlist, pattern):
        """
        Filter lines by regex pattern.

        :param list dirlist:
        :param str pattern:
        :return: list
        """

        regex = re.compile(pattern)
        newlist = filter(regex.match, dirlist)
        filteredlist = list(newlist)
        return filteredlist

    @staticmethod
    def clear(directory, extension=''):
        """
        Clear directory.

        :param str directory:
        :param str extension:
        :raise FileSystemError:
        :return: None
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
        Create a new file with context.

        :param str filename:
        :raise FileSystemError:
        :return: str
        """

        filepath = os.path.join(filename)
        if False is os.path.exists(filepath) or False is os.access(filepath, os.R_OK):
            try:
                directory = os.path.dirname(filepath)
                if directory:
                    directory = FileSystem.makedir(directory)
                    abs_filename = os.path.join(directory, os.path.basename(filepath))
                else:
                    abs_filename = filepath

                with open(abs_filename, 'w', encoding=FileSystem.text_encoding):
                    pass
                return abs_filename
            except IOError as error:
                raise FileSystemError(error.strerror)
        else:
            return filepath

    @staticmethod
    def shuffle(target, output, total):
        """
        Shuffle data in file.

        :param str target:
        :param str output:
        :param int total:
        :return: bool
        """

        try:
            with open(target, 'r', encoding=FileSystem.text_encoding) as i_f, open(output, 'wb') as o_f:
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
                        o_f.write(current_lines[node].encode(FileSystem.text_encoding))

        except IOError as error:
            raise FileSystemError(error.strerror)

    @staticmethod
    def readline(filename, handler, handler_params, loader):
        """
        Read txt file line by line in batches.

        The old implementation accumulated the entire file in memory before
        calling the loader once. This version keeps the public contract but
        sends processed lines to the loader in smaller batches to reduce
        peak memory usage on large wordlists.

        :param str filename:
        :param func handler:
        :param dict handler_params:
        :param func loader:
        :raise FileSystemError:
        :return: None
        """

        filepath = FileSystem._resolve_readable_file(filename, include_home=True)

        batch = []
        has_lines = False

        with open(filepath, 'r', encoding=FileSystem.text_encoding) as f_handler:
            for line in f_handler:
                has_lines = True
                batch.append(handler(line, handler_params))

                if len(batch) >= FileSystem.READLINE_BATCH_SIZE:
                    loader(batch)
                    batch = []

        if batch or not has_lines:
            loader(batch)

    @staticmethod
    def read(filename):
        """
        Read .txt file.

        :param str filename:
        :raise FileSystemError:
        :return: list
        """

        filepath = FileSystem._resolve_readable_file(filename)

        with open(filepath, 'r', encoding=FileSystem.text_encoding) as f_handler:
            data = f_handler.readlines()
        return data

    @staticmethod
    def count_lines(filename):
        """
        Count lines in .txt file.

        :param str filename:
        :raise FileSystemError:
        :return: int
        """

        filepath = FileSystem._resolve_readable_file(filename)

        count = 0
        with open(filepath, 'r', encoding=FileSystem.text_encoding) as f_handler:
            for count, _line in enumerate(f_handler, start=1):
                pass
        return count

    @staticmethod
    def readcfg(filename):
        """
        Read .cfg file.

        :param str filename:
        :raise FileSystemError:
        :return: configparser.RawConfigParser
        """

        filepath = FileSystem._resolve_readable_file(filename, include_project_root=True)

        try:
            config = RawConfigParser()
            config.read(filepath, encoding=FileSystem.text_encoding)
            return config

        except (ParsingError, NoOptionError) as error:
            raise FileSystemError(error)

    @staticmethod
    def writelist(filename, data, separator=''):
        """
        Write the list to file.

        :param str filename:
        :param list data:
        :param str separator:
        :raise FileSystemError:
        :return: None
        """

        filepath = FileSystem._resolve_writable_file(filename)

        with open(filepath, "w", encoding=FileSystem.text_encoding) as f_handler:
            f_handler.write(separator.join(data))

    @staticmethod
    def human_size(size, precision=2):
        """
        Humanize accepted bytes.

        :param int size:
        :param int precision:
        :return: str
        """

        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        suffix_index = 0
        size = int(size)
        while size > 1024 and suffix_index < 4:
            suffix_index += 1
            size /= 1024

        return "%.*f%s" % (precision, size, suffixes[suffix_index])