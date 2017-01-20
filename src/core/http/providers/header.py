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

import random

class HeaderProvider(object):
    """ HeaderProvider class"""

    def __init__(self, config, agent_list=()):
        self.__config = config
        self.__agent_list = agent_list

    @property
    def user_agent(self):
        """
        Get user agent
        :return: str user-agent
        """

        if True is self.__config._is_random_user_agent:
            index = random.randrange(0, len(self.__agent_list))
            user_agent = self.__agent_list[index].strip()
        else:
            user_agent = self.__config.user_agent
        return user_agent

