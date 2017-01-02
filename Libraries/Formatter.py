# -*- coding: utf-8 -*-

"""Formatter class"""


class Formatter:
    """Formatter args class"""

    @staticmethod
    def get_readable_size(size, precision=2):
        """Get readable file sizes"""

        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        suffix_index = 0
        size = int(size)
        while size > 1024 and suffix_index < 4:
            suffix_index += 1
            size = size / 1024.0

        return "%.*f%s" % (precision, size, suffixes[suffix_index])
