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

import random


class UserAgentHeaderProvider(object):
    """ UserAgentHeaderProvider class"""

    def __init__(self, config, agent_list=()):
        """
        Init interface
        Parameters:
        agent_list (tuple, optional): A tuple containing the initial list of agents. Defaults to an empty tuple.
        """

        self.__cfg = config
        self.__agent_list = agent_list

    @property
    def _user_agent(self):
        """
        Get 'User-Agent' Header
        :return: str
        """

        if True is self.__cfg.is_random_user_agent:
            index = random.randrange(0, len(self.__agent_list))
            user_agent = self.__agent_list[index].strip()
        else:
            user_agent = self.__cfg.user_agent
        return user_agent
