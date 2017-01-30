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

from .color import Color as colour
from .decorators import execution_time
from .filesystem import FileSystem as filesystem
from .filesystem.exceptions import FileSystemError
from .helper import Helper as helper
from .http import HttpRequest as request_http
from .http import HttpsRequest as request_ssl
from .http import Proxy as request_proxy
from .http import Response as response
from .http import Socket as socket
from .http.exceptions import HttpRequestError
from .http.exceptions import HttpsRequestError
from .http.exceptions import ProxyRequestError
from .http.exceptions import ResponseError
from .http.exceptions import SocketError
from .logger import LoggerException as exception
from .logger import Logger as logger
from .options import Options as options
from .options.exceptions import OptionsError
from .system import Process as process
from .system import System as sys
from .system.exceptions import CoreSystemError
