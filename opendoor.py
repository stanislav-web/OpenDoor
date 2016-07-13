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

from Libraries import Http, Command, FileReader, Filter;
from Vendors import Colors, get_version, update;

VERSION = get_version()
FileReader = FileReader();
Command = Command();
Filter = Filter();

print '############################################################'
print '#                                                          #'
print '#   _____  ____  ____  _  _    ____   _____  _____  ____   #'
print '#  (  _  )(  _ \( ___)( \( )  (  _ \ (  _  )(  _  )(  _ \  #'
print '#   )(_)(  )___/ )__)  )  (    )(_) ) )(_)(  )(_)(  )   /  #'
print '#  (_____)(__)  (____)(_)\_)  (____/ (_____)(_____)(_)\_)  #'
print '#                                                          #'
print '#  '+ Colors.colored(VERSION, 'green') +'\t\t\t           #'
print '############################################################'

# Init argument's helper


# FileReader functions
FileReader.get_user_agent()
FileReader.get_random_user_agent()

# User for update command update();
# Http functions
Http().connect();

if Command.get_arg_values() :
    Filter.call(Command)