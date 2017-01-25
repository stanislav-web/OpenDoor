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

    templates = {
        'unsupported': 'Your version v {actual} is not supported by this application. Please consider v{expected}',
        'abort'  : 'Session canceled',
        'use_reports'  : 'Use --report param to store your scan results',
        'logged' : 'The {host} has been reported. Press ENTER to rescan or CTRL+C to exit: ',
        'checking_connect' : 'Wait, please, checking connect to -> {host}:{port} ...',
        'slow_connection': 'Too slow connection. Please decrease the number of threads and increase the request timeout',
        'online': 'Server {host}:{port} ({ip}) is online!',
        'scanning': 'Scanning {host} ...',
        'debug': 'Starting debug level {level} . Using scan method: {method} ...',
        'randomizing': 'Randomizing scan list ...',
        'browser': 'Fetching user-agent: {browser}',
        'directories': 'Read {total} directories list by line',
        'create_queue': 'Creating queue with {threads} thread(s)...',
        'subdomains': 'Read {total} subdomains list by line...',
        'random_browser': 'Fetching random user-agent per request...',
        'proxy': 'Fetching proxies...',
        'get_item_lvl0' : '{percent} {item}',
        'total_time_lvl3'  : 'Total time running: {time}',
        'thread_limit'  : 'Threads has been reduced to {max} (max) instead of {threads}',
        'stop_threads'  : 'Stopping threads ({threads})...',
        'option_prompt'  : 'Press "[C]ontinue" to resume or "[E]xit" to abort session: ',
        'resume_threads'  : 'Resuming scan...',
        'get_item_lvl1' : '{percent} [{current}/{total}] - {size} - {item}',
        'addtopool'  : 'Adding {total} lines to queue...',
        'http_pool_start' : 'Using HTTP keep-alive connection',
        'https_pool_start' : 'Using SSL keep-alive connection',
        'proxy_pool_start' : 'Using random proxies',
        'request_header_dbg': 'Request headers:\n{dbg}',
        'custom_proxy'     : 'Using custom proxy server: {server}',
        'ignored_path'     : 'Ignored. The path {path} in ignore list',
        'max_retry_error'  : 'Skipped. Max retries exceeded: {url}',
        'proxy_max_retry_error': 'Skipped. Proxy {proxy} Max retries exceeded: {url}',
        'host_changed_error'   : 'Block external redirect -> {details}',
        'read_timeout_error' : 'Connection timeout! {url}. Increase using --timeout option',
    }

    #                "http": {
    #                    'redirect': "Redirect {0} --> {1}",
    #                    'excluded': "Excluded path: {0}",
    #                    'unresponsible': "Unresponsible path : {0}",
    #                    'has_scanned': "You already have the results for {0} saved in logs directory.\nWould you like to rescan? Press [ENTER] to continue: ",
    #                    'file_detected': "Probably you found important filesource {0} {1}"
    #                }
    #            },


