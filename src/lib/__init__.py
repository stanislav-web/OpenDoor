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

from .browser import Browser as browser
from .browser import BrowserError
from .events import EventHandler as events
from .io import Arguments as args
from .io import ArgumentsError
from .package import Package as package
from .package import PackageError
from .reader import Reader as reader
from .reader import ReaderError
from .reporter import Reporter as applog
from .tpl import Tpl as tpl
