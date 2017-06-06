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

# noinspection PyPep8Naming
from src.lib.tpl import Tpl as tpl


class Filter(object):

    """Filter class"""

    # noinspection PyPep8Naming
    def __init__(self, Config, total_lines):
        """
        Filter constructor
        :param Config: Config
        :param int total_lines: num lines in list
        """

        if Config.threads > Config.DEFAULT_MAX_THREADS or Config.threads > total_lines:

            max_threads = total_lines if Config.DEFAULT_MAX_THREADS > total_lines else Config.DEFAULT_MAX_THREADS
            tpl.warning(key='thread_limit', threads=Config.threads, max=max_threads)
            Config.set_threads(max_threads)
