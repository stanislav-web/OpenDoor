#    OpenDoor Web Directory Scanner
#    Copyright (C) 2016  Stanislav Menshov
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Development Team:
#
#    Stanislav Menshov (Stanislav WEB) since version 1.0

from Libraries import Command, Filter, Controller;
from Version import get_banner;

print(get_banner())

# Init libraries
Command = Command();
Filter = Filter();
InputArguments = []

# Parse input arguments
if Command.get_arg_values():
    InputArguments = Filter.call(Command)
    Controller(InputArguments)