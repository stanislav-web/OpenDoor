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
        'unsupported': 'Your version v {actual} is not supported by this application. Please consider v{expected}',
        'abort'  : 'Session canceled',
        'use_log'  : 'Use --log param to store your scan results',
        'logged' : 'The {host} has been stored. Press ENTER to rescan or CTRL+C to exit: ',
        'online': 'Server {host}:{port} ({ip}) is online!',
        'scanning': 'Scanning {host} ...',
        'debug': 'Starting debug level {level} ...',
        'randomizing': 'Randomizing scan list ...',
        'browser': 'Fetching user-agent: {browser}',
        'directories': 'Read {total} directories list by line...',
        'create_queue': 'Wait please. Create queue with {threads} thread(s)...',
        'subdomains': 'Read {total} subdomains list by line...',
        'random_browser': 'Fetching random user-agent per request...',
        'proxy': 'Fetching proxies...',
        'get_item_lvl0' : '{percent} {item}',
        'stop_threads'  : 'Stopping threads, please wait...',
        'resume_threads'  : 'Press [ENTER] to resume threads: ',
        'resuming'  : 'Resuming...',
        'get_item_lvl1' : '{percent} [{current}/{total}] - {size} - {item}',
        'addtopool'  : 'Adding {total} lines to queue...'
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


