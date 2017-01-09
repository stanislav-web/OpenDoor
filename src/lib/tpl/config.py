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

    Development Team: Stanislav Menshov
"""

class Config:
    """Config class"""

    templates = {
        'abort'  : 'Session canceled',
        'use_log'  : 'Use --log param to store your scan results',
        'logged' : 'The {host} has been stored. Press ENTER to rescan or CTRL+C to exit: ',
        'online': 'Server {host}:{port} ({ip}) is online!',
        'scanning': 'Scanning {host} ...',
        'debug': 'Starting debug level {level} ...',
        'browser': 'Fetching user-agent: {browser}',
        'directories': 'Read directories list by line',
        'subdomains': 'Read subdomains list by line',
        'random_browser': 'Fetching random user-agent per request...',
        'proxy': 'Fetching proxies...'
    }

    #                "http": {
    #                    'online': "Server {0} {1}:{2} is online",
    #                    'offline': "Oops Error occured, Server offline or invalid URL. Reason: {}",
    #                    'redirect': "Redirect {0} --> {1}",
    #                    'scanning': "Scanning {0} ...",
    #                    'abort': "Session canceled",
    #                    'timeout': "Connection timeout: {0} . Try to increase --delay between requests",
    #                    'excluded': "Excluded path: {0}",
    #                    'unresponsible': "Unresponsible path : {0}",
    #                    'use_log': "Use --log param to save scan result",
    #                    'max_threads': "Passed {0} threads max for your possibility",
    #                    'has_scanned': "You already have the results for {0} saved in logs directory.\nWould you like to rescan? Press [ENTER] to continue: ",
    #                    'file_detected': "Probably you found important filesource {0} {1}"
    #                }
    #            },


