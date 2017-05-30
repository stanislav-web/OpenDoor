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
from .browser import Browser as browser, BrowserError
# noinspection PyPep8Naming
from .events import EventHandler as events
# noinspection PyPep8Naming
from .io import Arguments as args, ArgumentsError
# noinspection PyPep8Naming
from .package import Package as package, PackageError
# noinspection PyPep8Naming
from .reader import Reader as reader, ReaderError
# noinspection PyPep8Naming
from .reporter import Reporter as reporter, ReporterError
# noinspection PyPep8Naming
from .tpl import Tpl as tpl, TplError
