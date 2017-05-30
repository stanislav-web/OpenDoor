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

import datetime
import functools
import time


def execution_time(func=None, log=None):
    """
    Time execution decorator @execution_time(log=tpl)
    :param funct func: wrapped function
    :param funct log: logger
    :return: func
    """

    if not func:
        # noinspection PyArgumentList
        return functools.partial(execution_time, log=log)

    @functools.wraps(func)
    def function_timer(*args, **kwargs):
        """
        Function timer
        :param args:  arguments
        :param kwargs: key arguments
        :return: func
        """

        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        timeless = "{0}".format(datetime.timedelta(seconds=(end - start)))
        log.debug(key='total_time_lvl3', time=timeless)
        return result

    return function_timer
