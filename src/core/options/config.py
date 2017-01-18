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


class Config:
    """Config class"""

    groups = {'request': "Request tools", 'stream': "Stream tools", 'debug': "Debug tools",
        'wordlist': "Wordlist tools", 'sniff': "Sniff tools", 'app': "Application tools",}

    standalone = ["version", "update", "examples"]

    arguments = [{"group": "request", "args": "-p", "argl": "--port", "default": 80, "action": "store",
        "help": "Custom port (Default 80)", "type": int},
        {"group": "request", "args": "-m", "argl": "--method", "default": "HEAD", "action": "store",
            "help": "HTTP method (use HEAD as default)", "type": str},
        {"group": "stream", "args": "-t", "argl": "--threads", "default": 1, "action": "store",
            "help": "Allowed threads", "type": int},
        {"group": "request", "args": "-d", "argl": "--delay", "default": 0, "action": "store",
            "help": "Delay between requests", "type": int},
        {"group": "request", "args": None, "argl": "--timeout", "default": 0, "action": "store",
            "help": "Request timeout", "type": int},
        {"group": "request", "args": None, "argl": "--cookies", "default": "", "action": "store",
            "help": "Request cookies from cookies.txt", "type": str},
        {"group": "debug", "args": None, "argl": "--debug", "default": 0, "action": "store",
            "help": "Debug level 1 - 3", "type": int},
        {"group": "request", "args": None, "argl": "--tor", "default": False, "action": "store_true",
            "help": "Using proxylist", "type": bool},
        {"group": "wordlist", "args": "-s", "argl": "--scan", "default": "directories", "action": "store",
            "help": "Scan type scan=directories or scan=subdomains", "type": str},
        {"group": "wordlist", "args": "-l", "argl": "--reports", "default": None, "action": "store",
            "help": "Scan reports", "type": bool},
        {"group": "request", "args": None, "argl": "--random-agent", "default": False, "action": "store_true",
            "help": "Randomize user-agent per request", "type": bool},
        {"group": "wordlist", "args": None, "argl": "--random-list", "default": False, "action": "store_true",
            "help": "Randomize scan list", "type": bool},
        {"group": "sniff", "args": "-i", "argl": "--indexof", "default": False, "action": "store_true",
            "help": "Detect  Index of/", "type": bool},
        {"group": "app", "args": None, "argl": "--update", "default": False, "action": "store_true",
            "help": "Update from CVS", "type": bool},
        {"group": "app", "args": None, "argl": "--version", "default": False, "action": "store_true",
            "help": "Get current version", "type": bool},
        {"group": "app", "args": None, "argl": "--examples", "default": False, "action": "store_true",
            "help": "Examples of usage", "type": bool}]
