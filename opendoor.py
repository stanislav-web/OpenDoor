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

import Libraries;
from Vendors import Version, Colors;

VERSION = Version.get_versions().get('version');

print '##################################################################################################'
print '#                                                                                                #'
print '#                                                                                                #'
print '#   .oooooo.                                         oooooooooo.                                 #'
print '#  d8P'  'Y8b                                        `888'   'Y8b                                #'
print '# 888      888 oo.ooooo.   .ooooo.   ooo. .oo.        888      888  .ooooo.   .ooooo.  oooo d8b  #'
print '# 888      888  888' '88b d88' '88b `888P"Y88b        888      888 d88' '88b d88' '88b `888""8P  #'
print '# 888      888  888   888 888ooo888  888   888        888      888 888   888 888   888  888      #'
print '# `88b    d88`  888   888 888    .o  888   888        888     d88" 888   888 888   888  888      #'
print '#  `Y8bood8P"   888bod8P" `Y8bod8P" o888o o888o      o888bood8P"   "Y8bod8P"  Y8bod8P` d888b     #'
print '#               888                                                                              #'
print '#              o888o                                                                             #'
print '#                                                                                                #'
print '# '+ Colors.colored('v ' + VERSION, 'blue') +'                                                   #'
print '##################################################################################################'


Libraries.Http().connect();