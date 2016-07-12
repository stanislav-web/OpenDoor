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

from Libraries import Http, Args, FileReader, Project;
from Vendors import Version, Colors;

VERSION = Version.get_versions().get('version');
FileReader = FileReader();
Project = Project();

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
Args();

# FileReader functions
FileReader.get_user_agent()
FileReader.get_random_user_agent()

Project.update();
# Http functions
Http().connect();


