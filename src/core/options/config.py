# -*- coding: utf-8 -*-

"""Config class"""

class Config:
    """Config class"""

    standalone = [
        "version",
        "update",
        "examples"
    ]

    arguments = [
        {
            "args": "-p",
            "argl": "--port",
            "default": 80,
            "action": "store",
            "help": "Custom port (Default 80)",
            "type" : int
        },
        {
            "args": "-m",
            "argl": "--method",
            "default": "HEAD",
            "action": "store",
            "help": "HTTP method (use HEAD as default)",
            "type": str
        },
        {
            "args": "-t",
            "argl": "--threads",
            "default": 1,
            "action": "store",
            "help": "Allowed threads",
            "type": int
        },
        {
            "args": "-d",
            "argl": "--delay",
            "default": 0,
            "action": "store",
            "help": "Delay between requests",
            "type": int
        },
        {
            "args": None,
            "argl": "--timeout",
            "default": 0,
            "action": "store",
            "help": "Request timeout",
            "type": int
        },
        {
            "args": None,
            "argl": "--debug",
            "default": 0,
            "action": "store",
            "help": "Debug level 1 - 3",
            "type": int
        },
        {
            "args": None,
            "argl": "--tor",
            "default": False,
            "action": "store_true",
            "help": "Using proxylist",
            "type": bool
        },
        {
            "args": "-s",
            "argl": "--scan",
            "default": "directories",
            "action": "store",
            "help": "Scan type scan=directories or scan=subdomains",
            "type": str
        },
        {
            "args": "-l",
            "argl": "--log",
            "default": False,
            "action": "store_true",
            "help": "Scan logging",
            "type": bool
        },
        {
            "args": None,
            "argl": "--random-agent",
            "default": False,
            "action": "store_true",
            "help": "Scan logging",
            "type": bool
        },
        {
            "args": "-i",
            "argl": "--indexof",
            "default": False,
            "action": "store_true",
            "help": "Detect  Index of/",
            "type": bool
        },
        {
            "args": None,
            "argl": "--update",
            "default" : False,
            "action" : "store_true",
            "help": "Update from CVS",
            "type": bool
        },
        {
            "args": None,
            "argl": "--version",
            "default": False,
            "action": "store_true",
            "help": "Get current version",
            "type": bool
        },
        {
            "args": None,
            "argl": "--examples",
            "default": False,
            "action": "store_true",
            "help": "Examples of usage",
            "type": bool
        }
    ]
