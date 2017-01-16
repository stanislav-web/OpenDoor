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

import time
import datetime
import functools

def execution_time(function=None,log=None):
    """
    Time execution decorator @execution_time(log=tpl)


    :param funct function: wrapped function
    :param funct log: logger
    :return: func
    """

    if not function:
        return functools.partial(execution_time, log=log)

    @functools.wraps(function)
    def function_timer(*args, **kwargs):
        """
        Timer
        :param args:  arguments
        :param kwargs: key arguments
        :return: func
        """
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        timeless = "{:0>8}".format(datetime.timedelta(seconds=(t1 - t0)))
        log.debug (key='total_time_lvl3', time=timeless)
        return result
    return function_timer